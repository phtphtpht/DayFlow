"""
AI 分析模块
使用 OpenAI API 分析截图，识别用户的工作内容
"""

import os
import base64
import json
import re
import logging
from typing import Dict, Optional
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from ..database.db import SessionLocal, get_recent_context
from ..database.models import Activity
from ..utils.config import get_config

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化 OpenAI 客户端
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def _get_text_from_responses(resp) -> str:
    """Robustly extract plain text from Responses API return.
    Prefer `output_text`; fall back to concatenating nested content texts.
    """
    # 1) Prefer the high-level helper if available
    text = getattr(resp, "output_text", None)
    if text:
        return text

    # 2) Fallback: iterate nested structures (older SDKs)
    try:
        parts = []
        output = getattr(resp, "output", None)
        if output:
            for item in output:
                content = getattr(item, "content", None)
                if content:
                    for c in content:
                        # c may be pydantic object or dict; try attribute then dict
                        t = getattr(c, "text", None)
                        if not t and isinstance(c, dict):
                            t = c.get("text")
                        if t:
                            parts.append(t)
        return "".join(parts)
    except Exception:
        return ""


def get_analysis_prompt(lang: str, activity, recent_context: str) -> str:
    """
    根据语言返回对应的分析prompt

    Args:
        lang: 语言代码 ('zh', 'en', 'ja')
        activity: Activity 对象
        recent_context: 最近的工作上下文

    Returns:
        str: 对应语言的 prompt
    """
    if lang == 'zh':
        # 中文 prompt（保持现有内容）
        return f"""你是一个专业的工作活动分析助手。请**深入分析**这张多屏幕截图，详细识别用户正在进行的工作。

**重要提示：这是多屏幕截图**
- 图片包含用户的所有显示器内容
- 当前活跃窗口（用户正在操作的）：{activity.app_name}
- 请综合**所有屏幕**的内容来判断用户真正在做什么

**最近的工作上下文（过去50分钟）：**
{recent_context if recent_context else "无历史记录（这是今天的第一条记录）"}

**当前信息：**
- 活跃应用：{activity.app_name}
- 窗口标题：{activity.window_title}
- 时间：{activity.timestamp.strftime('%H:%M')}

**深度分析任务：**
你需要像一个细心的观察者一样，仔细查看截图中的每个细节：

1. **识别所有可见的应用和窗口**
   - 主屏幕上显示什么？
   - 副屏幕（如果有）上显示什么？
   - 背景中有哪些打开的窗口？

2. **理解具体的工作内容（重要：仔细识别内容性质）**
   - 不要只说"使用VSCode"，而要说明在VSCode中做什么（写代码？调试？看文件？）
   - 如果能看到代码，识别编程语言和正在处理的功能
   - 如果是浏览器，识别具体网站和页面内容
   - 如果是终端，识别正在执行的命令
   - **如果是视频/文档/网页，仔细判断内容性质：**
     * 技术教程/文档/编程相关 → 工作/学习
     * 娱乐内容（游戏、综艺、音乐MV、生活vlog） → 休息娱乐
     * 技术会议/演讲视频 → 工作相关
     * 游戏攻略/连招教学 → 娱乐（即使是"学习"，也是游戏相关）
   - **例如：**
     * YouTube视频标题是"React Hooks Complete Tutorial" → browsing/coding（技术学习）
     * B站视频是"原神连招教学" → entertainment（游戏娱乐）
     * YouTube视频是"游戏实况" → entertainment（娱乐）
     * arXiv论文页面 → browsing（研究学习）

3. **分析工作的上下文和目的**
   - 首先基于当前截图判断活动性质，然后参考历史判断连续性
   - **仔细观察内容细节**：视频标题、网页文字、窗口内容等，判断是工作还是娱乐
   - 如果当前活动与历史完全不同（如从编程切换到专注看娱乐视频），优先相信当前截图
   - 识别工作辅助活动（查文档、看教程、背景音乐）vs 完全的任务切换（工作→娱乐休息）

4. **判断任务状态（重要：准确识别任务切换 vs 工作辅助）**
   - 延续工作：当前活动与历史活动类型一致且相关 → 使用"继续..."
   - 任务切换：当前活动与历史工作性质完全不同 → 使用"从...切换到..."
   - **判断关键：**
     * a. 内容性质：仔细识别视频/网页的实际内容（技术 vs 娱乐）
     * b. 注意力分配：用户的主要注意力在哪里
   - **决策逻辑：**
     * 如果主要在工作（编程、写作），音乐/播客在后台 → 工作类别，可说"同时听音乐"
     * 如果在看技术教程/文档，同时在编辑器实践 → 工作类别，"边学习边实践"
     * 如果主要在看娱乐视频（游戏、综艺、vlog），工作已暂停 → entertainment，"切换到休息"

**描述质量要求：**
- 📏 **长度**：50-80字，要详细具体
- 🎯 **具体性**：避免"使用XXX"这样的空泛描述
- 🔗 **连贯性**：如果是延续工作，要体现与之前的关联
- 💡 **洞察力**：不只说"做什么"，还要说明"怎么做"、"为什么"
- 📝 **包含信息**：主要工具、具体内容、工作情境、是否多任务

**好的描述示例：**
❌ 差（太简单）："使用VSCode编程"
❌ 差（太模糊）："在电脑上工作"
✅ 好："继续开发AIWorkTracker项目的摘要生成模块，当前在analyzer.py文件中调试OpenAI API的调用逻辑，同时在Chrome中查阅OpenAI官方文档的Responses API部分，终端显示pytest测试输出"
✅ 好："从后端开发切换到前端工作，开始在VSCode中编写React组件，参考Tailwind CSS文档设计Dashboard界面，浏览器中打开了本地开发服务器预览效果"
✅ 好："在Claude.ai与AI助手讨论项目架构设计，同时在Obsidian中记录关键要点和待办事项，VSCode保持在后台打开着项目代码以便随时参考"

**任务切换示例（补充）：**
❌ 错误："继续开发项目，同时在YouTube观看视频"
   （如果在看娱乐视频，应该是entertainment，不应该说"继续开发"）
✅ 正确："从开发工作切换到休息，在YouTube观看娱乐视频" (category: entertainment)

❌ 错误："继续编程，当前在听音乐放松"
✅ 正确："工作暂停，在Apple Music听音乐休息" (category: entertainment)

✅ 正确："在VSCode编写代码，同时在终端运行测试，Chrome中查阅技术文档" (category: coding)
   （这是真正的工作辅助，可以说"同时"）

**内容识别与任务判断示例（重要补充）：**

**场景1：看技术教程视频**
✅ 正确："在YouTube观看'React Server Components完整教程'视频学习新技术，VSCode中同步编写示例代码验证理解"
   category: coding 或 browsing
   （虽然在看视频，但内容是技术教程，属于学习工作）

**场景2：看游戏攻略视频**
❌ 错误："继续开发项目，同时在B站学习游戏连招技巧"
✅ 正确："从工作切换到休息，在B站观看原神角色连招教学视频娱乐"
   category: entertainment
   （即使标题有"教学"，但这是游戏相关 = 娱乐）

**场景3：看技术会议演讲**
✅ 正确："观看Google I/O开发者大会关于Flutter新特性的演讲，了解最新技术动态"
   category: browsing
   （技术会议 = 工作相关学习）

**场景4：边听歌边编程**
✅ 正确："在VSCode继续开发项目，调试API接口逻辑，同时Apple Music播放背景音乐"
   category: coding
   （音乐是背景，主要在编程）

**场景5：看娱乐直播**
❌ 错误："继续工作，同时观看直播学习"
✅ 正确："工作暂停，在Twitch观看游戏直播娱乐"
   category: entertainment
   （直播内容如果是娱乐性质 = 休息）

**场景6：阅读技术论文**
✅ 正确："在arXiv阅读关于Transformer架构的最新论文，Chrome中打开多个相关研究进行对比学习"
   category: browsing
   （学术研究 = 工作）

**场景7：看B站综艺/vlog**
✅ 正确："从编程工作切换到休息时间，在B站观看生活类vlog放松"
   category: entertainment
   （生活内容 = 娱乐休息）

**场景8：看技术博客同时写代码**
✅ 正确："参考Medium技术博客中的实现方案，在VSCode中应用到当前项目的数据库优化工作"
   category: coding
   （技术博客 + 实践 = 工作）

**内容识别的关键线索：**
- 视频/网页标题中的关键词
- 屏幕上可见的文字内容
- 网站性质（技术网站 vs 娱乐平台）
- 内容主题（编程/技术 vs 游戏/娱乐/生活）
- 不要仅凭平台判断（YouTube既有教程也有娱乐，B站既有技术也有综艺）

**分类标准（重要：基于内容性质判断）：**
- **coding**：编写代码、调试、IDE操作、终端、Git、代码审查、跟随编程教程实践
- **writing**：写文档、邮件、文章、做笔记、技术博客撰写
- **meeting**：视频会议、在线会议、技术演讲/讲座（实时参与）
- **browsing**：查阅技术资料、阅读文档/论文、观看技术教程视频、技术博客、学术研究
  * 包括：技术教程视频、开发者文档、Stack Overflow、技术博客、学术论文
  * 关键：内容必须是技术/工作相关的学习
- **communication**：工作沟通、聊天工具、查看/回复邮件、与AI助手讨论技术问题
- **design**：使用设计工具、绘图、UI/UX设计
- **data_analysis**：数据处理、制作图表、数据分析
- **entertainment**：娱乐视频、游戏、社交媒体、购物、生活vlog、游戏直播/攻略
  * 包括：游戏相关内容（即使是"教学"）、综艺、音乐MV、娱乐直播、休闲浏览
  * 关键：主要注意力在娱乐/休息，工作已暂停
  * ⚠️ 背景音乐/播客不算entertainment（如果用户在工作）
- **other**：无法明确分类

**判断技巧：**
不要只看应用/平台，要看**内容性质**：
- YouTube/B站上的编程教程 → browsing/coding
- YouTube/B站上的游戏视频 → entertainment
- Chrome浏览技术文档 → browsing
- Chrome浏览购物网站 → entertainment

**返回格式（必须是有效的JSON）：**
{{
  "category": "选择上述分类之一",
  "description": "详细描述，50-80字，要具体说明在做什么、怎么做、用到哪些工具、工作情境",
  "confidence": 85
}}

**confidence 打分标准：**
- 90-100：能清晰识别具体工作内容、文件名、代码逻辑，多屏幕内容一致，与历史高度相关
- 70-89：能识别工作类型和主要内容，能看清部分细节
- 50-69：只能识别应用类型和大致方向，屏幕内容不够清晰
- 30-49：只能看到窗口标题，无法看清具体内容
- 0-29：截图模糊或无法识别

**分析提示：**
- **第一优先级**：仔细识别当前内容的**实际性质**（技术/工作 vs 娱乐/休息）
- **第二优先级**：判断用户的**主要注意力**在哪里
- 不要被应用名称误导（YouTube既有教程也有娱乐）
- 不要被历史记录主导（如果当前在娱乐，就是在休息，即使之前在工作）
- **观察线索**：视频标题、网页内容、窗口标题中的关键词

**特别提醒：**
- 仔细观察截图中的文字、代码、界面元素
- 不要满足于表面的应用名称，要深入理解工作内容
- 多屏幕要整合分析，不要只看活跃窗口
- 描述要像一个了解技术的同事在记录工作日志一样详细

只返回JSON，不要任何其他文字。
"""

    elif lang == 'en':
        # 英文 prompt
        return f"""You are a professional work activity analyzer. Please **analyze in depth** this multi-screen screenshot and identify what the user is working on.

**Important: This is a Multi-Screen Screenshot**
- The image contains all of the user's monitor contents
- Currently active window: {activity.app_name}
- Please analyze **all screens** comprehensively

**Recent Work Context (Past 50 minutes):**
{recent_context if recent_context else "No history (this is the first record today)"}

**Current Information:**
- Active Application: {activity.app_name}
- Window Title: {activity.window_title}
- Time: {activity.timestamp.strftime('%H:%M')}

**In-Depth Analysis Tasks:**
You need to carefully examine every detail in the screenshot like an attentive observer:

1. **Identify all visible applications and windows**
   - What's on the main screen?
   - What's on secondary screens (if any)?
   - What windows are open in the background?

2. **Understand specific work content (Important: Carefully identify content nature)**
   - Don't just say "using VSCode" - specify what's being done in VSCode (writing code? debugging? viewing files?)
   - If code is visible, identify the programming language and functionality being worked on
   - If it's a browser, identify specific websites and page content
   - If it's a terminal, identify commands being executed
   - **If it's video/document/webpage, carefully judge content nature:**
     * Technical tutorials/docs/programming-related → work/learning
     * Entertainment content (games, variety shows, music MVs, lifestyle vlogs) → rest/entertainment
     * Tech conferences/talks → work-related
     * Game guides/combo tutorials → entertainment (even if it's "learning", it's game-related)
   - **Examples:**
     * YouTube video title "React Hooks Complete Tutorial" → browsing/coding (technical learning)
     * Bilibili video "Genshin Impact Combo Guide" → entertainment (game entertainment)
     * YouTube video "Gaming Stream" → entertainment
     * arXiv paper page → browsing (research/learning)

3. **Analyze work context and purpose**
   - First judge activity nature based on current screenshot, then refer to history for continuity
   - **Carefully observe content details**: video titles, webpage text, window content to determine work vs entertainment
   - If current activity is completely different from history (e.g., switching from coding to focused entertainment viewing), trust the current screenshot
   - Distinguish work auxiliary activities (checking docs, watching tutorials, background music) vs complete task switching (work→entertainment rest)

4. **Determine task status (Important: Accurately identify task switching vs work assistance)**
   - Continuing work: Current activity is consistent and related to history → use "continuing..."
   - Task switching: Current activity is completely different from historical work → use "switched from...to..."
   - **Key judgment factors:**
     * a. Content nature: Carefully identify actual content of videos/webpages (technical vs entertainment)
     * b. Attention allocation: Where is the user's primary attention
   - **Decision logic:**
     * If mainly working (coding, writing), music/podcast in background → work category, can say "while listening to music"
     * If watching technical tutorials/docs, practicing in editor simultaneously → work category, "learning while practicing"
     * If mainly watching entertainment videos (games, variety shows, vlogs), work paused → entertainment, "switched to rest"

**Description Quality Requirements:**
- 📏 **Length**: 50-80 words, detailed and specific
- 🎯 **Specificity**: Avoid vague descriptions like "using XXX"
- 🔗 **Coherence**: If continuing work, show connection to previous activities
- 💡 **Insight**: Don't just say "what" - also explain "how" and "why"
- 📝 **Information**: Include main tools, specific content, work context, multitasking

**Good Description Examples:**
❌ Bad (too simple): "Using VSCode for programming"
❌ Bad (too vague): "Working on computer"
✅ Good: "Continuing development of AIWorkTracker summary generation module, currently debugging OpenAI API call logic in analyzer.py file, while consulting OpenAI official Responses API documentation in Chrome, terminal shows pytest test output"
✅ Good: "Switched from backend development to frontend work, started writing React components in VSCode, referencing Tailwind CSS documentation to design Dashboard interface, browser shows local development server preview"
✅ Good: "Discussing project architecture design with AI assistant on Claude.ai, simultaneously recording key points and todos in Obsidian, VSCode remains open in background with project code for reference"

**Task Switching Examples (Additional):**
❌ Wrong: "Continuing project development while watching YouTube videos"
   (If watching entertainment videos, should be entertainment, don't say "continuing development")
✅ Correct: "Switched from development work to rest, watching entertainment videos on YouTube" (category: entertainment)

❌ Wrong: "Continuing programming, currently listening to music to relax"
✅ Correct: "Work paused, listening to music on Apple Music for rest" (category: entertainment)

✅ Correct: "Writing code in VSCode, running tests in terminal, checking technical documentation in Chrome" (category: coding)
   (This is genuine work assistance, can say "while")

**Content Recognition and Task Judgment Examples (Important Addition):**

**Scenario 1: Watching Technical Tutorial Videos**
✅ Correct: "Watching 'React Server Components Complete Tutorial' video on YouTube to learn new technology, simultaneously writing sample code in VSCode to verify understanding"
   category: coding or browsing
   (Although watching video, content is technical tutorial, belongs to work/learning)

**Scenario 2: Watching Game Guide Videos**
❌ Wrong: "Continuing project development, while learning game combo skills on Bilibili"
✅ Correct: "Switched from work to rest, watching Genshin Impact character combo tutorial on Bilibili for entertainment"
   category: entertainment
   (Even if title has "tutorial", it's game-related = entertainment)

**Scenario 3: Watching Tech Conference Talks**
✅ Correct: "Watching Google I/O developer conference talk on Flutter new features, learning about latest technology trends"
   category: browsing
   (Tech conferences = work-related learning)

**Scenario 4: Listening to Music While Coding**
✅ Correct: "Continuing project development in VSCode, debugging API interface logic, with Apple Music playing background music"
   category: coding
   (Music is background, main activity is coding)

**Scenario 5: Watching Entertainment Streams**
❌ Wrong: "Continuing work while watching stream for learning"
✅ Correct: "Work paused, watching gaming stream on Twitch for entertainment"
   category: entertainment
   (If stream content is entertainment = rest)

**Scenario 6: Reading Technical Papers**
✅ Correct: "Reading latest paper on Transformer architecture on arXiv, Chrome has multiple related research papers open for comparative study"
   category: browsing
   (Academic research = work)

**Scenario 7: Watching Variety Shows/Vlogs**
✅ Correct: "Switched from coding work to rest time, watching lifestyle vlog on Bilibili to relax"
   category: entertainment
   (Lifestyle content = entertainment/rest)

**Scenario 8: Reading Tech Blogs While Coding**
✅ Correct: "Referencing implementation approach from Medium tech blog, applying it to current project's database optimization work in VSCode"
   category: coding
   (Tech blog + practice = work)

**Key Clues for Content Identification:**
- Keywords in video/webpage titles
- Visible text content on screen
- Website nature (technical sites vs entertainment platforms)
- Content theme (programming/technical vs games/entertainment/lifestyle)
- Don't judge solely by platform (YouTube has both tutorials and entertainment, Bilibili has both technical and variety content)

**Category Standards (Important: Judge based on content nature):**
- **coding**: Writing code, debugging, IDE operations, terminal, Git, code review, following programming tutorials with practice
- **writing**: Writing documents, emails, articles, note-taking, technical blog writing
- **meeting**: Video conferences, online meetings, tech talks/lectures (live participation)
- **browsing**: Checking technical materials, reading docs/papers, watching technical tutorial videos, tech blogs, academic research
  * Includes: technical tutorial videos, developer documentation, Stack Overflow, tech blogs, academic papers
  * Key: content must be technical/work-related learning
- **communication**: Work communication, chat tools, checking/replying emails, discussing technical issues with AI assistants
- **design**: Using design tools, drawing, UI/UX design
- **data_analysis**: Data processing, creating charts, data analysis
- **entertainment**: Entertainment videos, games, social media, shopping, lifestyle vlogs, gaming streams/guides
  * Includes: game-related content (even if "tutorials"), variety shows, music MVs, entertainment streams, casual browsing
  * Key: main attention is on entertainment/rest, work has paused
  * ⚠️ Background music/podcasts don't count as entertainment (if user is working)
- **other**: Cannot be clearly categorized

**Judgment Tips:**
Don't judge solely by application/platform, look at **content nature**:
- Programming tutorials on YouTube/Bilibili → browsing/coding
- Gaming videos on YouTube/Bilibili → entertainment
- Technical documentation in Chrome → browsing
- Shopping websites in Chrome → entertainment

**Return Format (valid JSON):**
{{
  "category": "choose one category from above",
  "description": "Detailed description, 50-80 words, specify what's being done, how, which tools used, work context",
  "confidence": 85
}}

**Confidence Scoring:**
- 90-100: Can clearly identify specific work content, filenames, code logic, multi-screen content is consistent, highly related to history
- 70-89: Can identify work type and main content, can see some details
- 50-69: Can only identify application type and general direction, screen content not clear enough
- 30-49: Can only see window title, cannot see specific content
- 0-29: Screenshot blurry or unidentifiable

**Analysis Tips:**
- **First priority**: Carefully identify the **actual nature** of current content (technical/work vs entertainment/rest)
- **Second priority**: Judge where user's **main attention** is
- Don't be misled by application names (YouTube has both tutorials and entertainment)
- Don't be dominated by historical records (if currently entertaining, it's rest, even if previously working)
- **Observation clues**: video titles, webpage content, window titles for keywords

**Special Reminders:**
- Carefully observe text, code, and interface elements in the screenshot
- Don't settle for surface-level application names - deeply understand work content
- Integrate analysis across multiple screens, don't only look at active window
- Description should be as detailed as a technically knowledgeable colleague recording a work log

Return only JSON, no other text.
"""

    elif lang == 'ja':
        # 日文 prompt
        return f"""あなたはプロの作業活動分析アシスタントです。このマルチスクリーンのスクリーンショットを**詳細に分析**して、ユーザーが何をしているかを特定してください。

**重要：マルチスクリーンのスクリーンショット**
- ユーザーのすべてのモニターの内容が含まれています
- アクティブウィンドウ：{activity.app_name}
- **すべての画面**を総合的に分析してください

**最近の作業コンテキスト（過去50分間）：**
{recent_context if recent_context else "履歴なし（今日の最初の記録）"}

**現在の情報：**
- アクティブアプリ: {activity.app_name}
- ウィンドウタイトル: {activity.window_title}
- 時刻: {activity.timestamp.strftime('%H:%M')}

**詳細分析タスク：**
注意深い観察者のように、スクリーンショットのすべての詳細を慎重に調べる必要があります：

1. **すべての表示可能なアプリケーションとウィンドウを特定**
   - メイン画面には何が表示されていますか？
   - サブ画面（ある場合）には何が表示されていますか？
   - バックグラウンドで開いているウィンドウは何ですか？

2. **具体的な作業内容を理解**
   - 単に「VSCodeを使用」と言わず、VSCodeで何をしているかを明記（コード作成？デバッグ？ファイル閲覧？）
   - コードが見える場合、プログラミング言語と処理中の機能を特定
   - ブラウザの場合、特定のウェブサイトとページ内容を特定
   - ターミナルの場合、実行中のコマンドを特定

3. **作業のコンテキストと目的を分析**
   - まず現在のスクリーンショットに基づいて活動の性質を判断し、次に履歴を参照して継続性を判断
   - 現在の活動が履歴と完全に異なる場合（例：コーディングからエンターテイメントへの切り替え）、現在のスクリーンショットを優先
   - 作業フローの補助活動（ドキュメント確認、テスト）vs 完全なタスク切り替え（作業→休憩）を区別

4. **タスクステータスを判断（重要：タスク切り替えを正確に識別）**
   - 作業継続：現在の活動が履歴の活動タイプと一致し関連している → 「継続...」を使用
   - タスク切り替え：現在の活動が履歴の作業性質と完全に異なる → 「...から...に切り替え」を使用
   - 特記：entertainmentカテゴリーは休憩/娯楽を表し、作業とは無関係 - 説明では作業内容に言及しない

**説明品質要件：**
- 📏 **長さ**：50-80文字（日本語）、詳細で具体的
- 🎯 **具体性**：「XXXを使用」のような曖昧な説明を避ける
- 🔗 **一貫性**：作業を継続する場合、以前の活動との関連を示す
- 💡 **洞察力**：「何を」だけでなく「どのように」「なぜ」も説明
- 📝 **情報含有**：主要ツール、具体的内容、作業状況、マルチタスクかどうか

**良い説明例：**
❌ 悪い（簡単すぎる）：「VSCodeでプログラミング」
❌ 悪い（曖昧すぎる）：「コンピューターで作業」
✅ 良い：「AIWorkTrackerプロジェクトのサマリー生成モジュールの開発を継続、analyzer.pyファイルでOpenAI APIの呼び出しロジックをデバッグ中、同時にChromeでOpenAI公式のResponses APIドキュメントを参照、ターミナルにpytestテスト出力が表示」
✅ 良い：「バックエンド開発からフロントエンド作業に切り替え、VSCodeでReactコンポーネントの作成を開始、Tailwind CSSドキュメントを参照してDashboardインターフェースを設計、ブラウザでローカル開発サーバーのプレビュー表示」
✅ 良い：「Claude.aiでAIアシスタントとプロジェクトアーキテクチャ設計について議論、同時にObsidianで重要なポイントとTodoを記録、VSCodeはバックグラウンドでプロジェクトコードを開いたまま参照用に保持」

**タスク切り替え例（補足）：**
❌ 間違い：「プロジェクト開発を継続しながらYouTube動画を視聴」
   （エンターテイメント動画を見ている場合、entertainmentであるべきで、「開発を継続」と言うべきではない）
✅ 正しい：「開発作業から休憩に切り替え、YouTubeでエンターテイメント動画を視聴」(category: entertainment)

❌ 間違い：「プログラミングを継続、現在音楽を聴いてリラックス」
✅ 正しい：「作業一時停止、Apple Musicで音楽を聴いて休憩」(category: entertainment)

✅ 正しい：「VSCodeでコードを作成、ターミナルでテストを実行、Chromeで技術ドキュメントを参照」(category: coding)
   （これは本当の作業補助、「同時に」と言える）

**コンテンツ認識とタスク判断の例（重要な補足）：**

**場面1：技術チュートリアル動画を視聴**
✅ 正しい：「YouTubeで『React Server Components完全チュートリアル』動画を視聴して新技術を学習、同時にVSCodeでサンプルコードを書いて理解を確認」
   category: coding または browsing
   （動画を見ているが、内容は技術チュートリアルで、作業/学習に属する）

**場面2：ゲーム攻略動画を視聴**
❌ 間違い：「プロジェクト開発を継続、同時にBilibiliでゲームコンボスキルを学習」
✅ 正しい：「作業から休憩に切り替え、Bilibiliで原神キャラクターコンボチュートリアル動画を娯楽視聴」
   category: entertainment
   （タイトルに「チュートリアル」があっても、これはゲーム関連 = 娯楽）

**場面3：技術カンファレンス講演を視聴**
✅ 正しい：「Google I/O開発者カンファレンスのFlutter新機能に関する講演を視聴、最新技術動向を理解」
   category: browsing
   （技術カンファレンス = 作業関連学習）

**場面4：音楽を聴きながらコーディング**
✅ 正しい：「VSCodeでプロジェクト開発を継続、APIインターフェースロジックをデバッグ中、同時にApple Musicでバックグラウンド音楽を再生」
   category: coding
   （音楽は背景、主な活動はコーディング）

**場面5：エンターテイメント配信を視聴**
❌ 間違い：「作業を継続しながら学習のために配信を視聴」
✅ 正しい：「作業一時停止、Twitchでゲーム配信を娯楽視聴」
   category: entertainment
   （配信内容が娯楽的 = 休憩）

**場面6：技術論文を読む**
✅ 正しい：「arXivでTransformerアーキテクチャに関する最新論文を読み、Chromeで複数の関連研究を開いて比較学習」
   category: browsing
   （学術研究 = 作業）

**場面7：バラエティ番組/vlogを視聴**
✅ 正しい：「コーディング作業から休憩時間に切り替え、Bilibiliで生活系vlogを視聴してリラックス」
   category: entertainment
   （生活コンテンツ = 娯楽休憩）

**場面8：技術ブログを読みながらコーディング**
✅ 正しい：「Mediumの技術ブログの実装方法を参考に、VSCodeで現在のプロジェクトのデータベース最適化作業に適用」
   category: coding
   （技術ブログ + 実践 = 作業）

**コンテンツ識別の重要な手がかり：**
- 動画/ウェブページタイトルのキーワード
- 画面上に表示されているテキストコンテンツ
- ウェブサイトの性質（技術サイト vs 娯楽プラットフォーム）
- コンテンツテーマ（プログラミング/技術 vs ゲーム/娯楽/生活）
- プラットフォームだけで判断しない（YouTubeにはチュートリアルも娯楽もあり、Bilibiliには技術もバラエティもある）

**カテゴリー基準（重要：コンテンツ性質に基づいて判断）：**
- **coding**：コード作成、デバッグ、IDE操作、ターミナル、Git、コードレビュー、プログラミングチュートリアルに従った実践
- **writing**：ドキュメント作成、メール、記事、メモ取り、技術ブログ執筆
- **meeting**：ビデオ会議、オンライン会議、技術講演/講義（リアルタイム参加）
- **browsing**：技術資料の確認、ドキュメント/論文の読み、技術チュートリアル動画視聴、技術ブログ、学術研究
  * 含む：技術チュートリアル動画、開発者ドキュメント、Stack Overflow、技術ブログ、学術論文
  * 重要：コンテンツは技術/作業関連の学習でなければならない
- **communication**：作業コミュニケーション、チャットツール、メール確認/返信、AIアシスタントと技術問題を議論
- **design**：デザインツール使用、描画、UI/UXデザイン
- **data_analysis**：データ処理、グラフ作成、データ分析
- **entertainment**：娯楽動画、ゲーム、ソーシャルメディア、ショッピング、生活vlog、ゲーム配信/攻略
  * 含む：ゲーム関連コンテンツ（「チュートリアル」でも）、バラエティ、音楽MV、娯楽配信、カジュアルブラウジング
  * 重要：主な注意力が娯楽/休憩にあり、作業は一時停止
  * ⚠️ バックグラウンド音楽/ポッドキャストはentertainmentにカウントしない（ユーザーが作業中の場合）
- **other**：明確に分類できない

**判断のヒント：**
アプリケーション/プラットフォームだけで判断せず、**コンテンツ性質**を見る：
- YouTube/Bilibiliのプログラミングチュートリアル → browsing/coding
- YouTube/Bilibiliのゲーム動画 → entertainment
- Chromeで技術ドキュメントを閲覧 → browsing
- Chromeでショッピングサイトを閲覧 → entertainment

**返信形式（有効なJSON）：**
{{
  "category": "上記からカテゴリーを1つ選択",
  "description": "詳細説明、50-80文字、何をしているか、どのように、どのツールを使用しているか、作業コンテキストを明記",
  "confidence": 85
}}

**信頼度スコアリング：**
- 90-100：具体的な作業内容、ファイル名、コードロジックを明確に識別でき、マルチスクリーン内容が一致、履歴と高度に関連
- 70-89：作業タイプと主要内容を識別でき、いくつかの詳細を確認できる
- 50-69：アプリケーションタイプと大まかな方向のみを識別でき、画面内容が十分に明確ではない
- 30-49：ウィンドウタイトルのみを確認でき、具体的な内容は確認できない
- 0-29：スクリーンショットがぼやけているか識別できない

**分析のヒント：**
- **第一優先**：現在のコンテンツの**実際の性質**を慎重に識別（技術/作業 vs 娯楽/休憩）
- **第二優先**：ユーザーの**主な注意力**がどこにあるかを判断
- アプリケーション名に惑わされない（YouTubeにはチュートリアルも娯楽もある）
- 履歴記録に支配されない（現在娯楽中なら休憩、以前作業していても）
- **観察の手がかり**：動画タイトル、ウェブページコンテンツ、ウィンドウタイトルのキーワード

**特記事項：**
- スクリーンショット内のテキスト、コード、インターフェース要素を注意深く観察
- 表面的なアプリケーション名に満足せず、作業内容を深く理解
- マルチスクリーンを統合分析、アクティブウィンドウだけを見ない
- 説明は技術を理解する同僚が作業ログを記録するように詳細に

JSONのみ返してください、他のテキストは不要です。
"""

    else:
        # 默认中文
        return get_analysis_prompt('zh', activity, recent_context)


def analyze_screenshot(activity_id: int) -> Dict:
    """
    分析指定活动记录的截图

    Args:
        activity_id: 活动记录的 ID

    Returns:
        Dict: 分析结果字典
            {
                "category": str,
                "description": str,
                "confidence": int
            }

    Raises:
        FileNotFoundError: 截图文件不存在
        Exception: 其他错误
    """
    session = SessionLocal()

    try:
        logger.info(f"开始分析活动记录 ID: {activity_id}")

        # a. 从数据库获取当前 Activity 记录
        activity = session.query(Activity).filter(Activity.id == activity_id).first()

        if not activity:
            raise ValueError(f"未找到 ID 为 {activity_id} 的活动记录")

        # 检查截图文件是否存在
        screenshot_path = activity.screenshot_path
        if not Path(screenshot_path).exists():
            # 文件不存在，标记为已分析并跳过
            logger.warning(f"截图文件不存在，跳过分析: {screenshot_path}")
            activity.analyzed = True
            activity.category = "other"
            activity.description = "截图文件已丢失，无法分析"
            activity.confidence = 0
            session.commit()
            raise FileNotFoundError(f"截图文件不存在: {screenshot_path}")

        # b. 获取历史上下文
        recent_context = get_recent_context(activity_id, count=5)
        logger.debug(f"历史上下文: {recent_context[:100] if recent_context else '无'}")

        # c. 读取截图文件并转为 base64
        with open(screenshot_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        logger.debug(f"截图已编码，大小: {len(image_data)} 字符")

        # d. 获取用户语言设置并构建对应语言的 prompt
        config = get_config()
        user_lang = config.get('language', 'zh')
        prompt = get_analysis_prompt(user_lang, activity, recent_context)

        # e. 调用 OpenAI API
        logger.info("调用 OpenAI API 进行分析...")

        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

        # 使用 Responses API 调用（更适合结构化 + 多模态）
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": "你是专业的工作活动分析助手。只输出一个合法的 JSON 对象。"},
                {"role": "user", "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_data}"}
                ]}
            ]
            # 不传 max_output_tokens，使用模型默认值
        )

        # f. 解析返回的 JSON（Responses API 提供 output_text）
        result_text = (_get_text_from_responses(resp) or "").strip()

        # 去掉可能的 ```json ... ``` 围栏
        if result_text.startswith("```"):
            result_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", result_text, flags=re.S)

        if not result_text:
            # 打印部分原始响应帮助定位（避免过长日志）
            try:
                logger.error("Responses 原始响应(截断): %s", resp.model_dump_json()[:2000])
            except Exception:
                pass
            raise ValueError("Empty output_text from Responses API")

        logger.debug(f"API 返回内容: {result_text}")

        try:
            result = json.loads(result_text)
        except json.JSONDecodeError as e:
            # 兜底：尝试从文本中提取第一个 JSON 对象
            m = re.search(r"\{[\s\S]*\}", result_text)
            if m:
                result = json.loads(m.group(0))
            else:
                try:
                    logger.error("Responses 原始响应(截断): %s", resp.model_dump_json()[:2000])
                except Exception:
                    pass
                logger.error(f"JSON 解析失败: {e}")
                raise

        # 验证返回结果包含必要字段
        required_fields = ['category', 'description', 'confidence']
        for field in required_fields:
            if field not in result:
                logger.warning(f"返回结果缺少字段: {field}")
                result[field] = _get_default_value(field)

        logger.info(
            f"分析完成 | 类别: {result['category']} | "
            f"置信度: {result['confidence']} | "
            f"描述: {result['description'][:60]}..."
        )

        # g. 更新数据库中的 Activity 记录
        activity.category = result['category']
        activity.description = result['description']
        activity.confidence = result['confidence']
        activity.analyzed = True

        session.commit()
        logger.info(f"活动记录 {activity_id} 已更新到数据库")

        # h. 删除截图文件（已分析完成，不再需要）
        try:
            if Path(screenshot_path).exists():
                Path(screenshot_path).unlink()
                logger.info(f"截图文件已删除: {screenshot_path}")
        except Exception as e:
            logger.warning(f"删除截图文件失败: {e}")

        # i. 返回分析结果字典
        return result

    except FileNotFoundError as e:
        logger.error(f"文件错误: {e}")
        raise

    except Exception as e:
        logger.error(f"分析过程发生错误: {e}", exc_info=True)
        session.rollback()

        # 返回默认值
        return {
            "category": "other",
            "description": f"分析失败: {str(e)}",
            "confidence": 0
        }

    finally:
        session.close()


def _get_default_value(field_name: str):
    """
    获取字段的默认值

    Args:
        field_name: 字段名

    Returns:
        默认值
    """
    defaults = {
        'category': 'other',
        'description': '未知活动',
        'confidence': 0
    }
    return defaults.get(field_name, None)


if __name__ == "__main__":
    # 测试代码
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m backend.src.ai.analyzer <activity_id>")
        print("示例: python -m backend.src.ai.analyzer 1")
        sys.exit(1)

    activity_id = int(sys.argv[1])

    print(f"开始分析活动记录 ID: {activity_id}")

    try:
        result = analyze_screenshot(activity_id)

        print("\n分析结果：")
        print(f"  类别: {result['category']}")
        print(f"  描述: {result['description']}")
        print(f"  置信度: {result['confidence']}")

        print("\n✓ 分析完成")

    except Exception as e:
        print(f"\n✗ 分析失败: {e}")
        sys.exit(1)
