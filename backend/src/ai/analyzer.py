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
        # 中文 prompt（重构版：分类仅看当前截图；叙事可参考历史但不能改分类）
        return f"""你是“工作活动分析助手”。请基于当前这张【多屏幕截图】进行分析，并仅输出结构化 JSON 结果。

    【硬性规则（若与其他指示冲突，以此为准）】
    - 任务分类（category）必须只依据当前截图中的可见内容与前景/主要可视区域；**禁止**使用或参考任何历史信息（包括 recent_context）、Dock/任务栏、后台窗口、应用图标。
    - 平台≠内容：YouTube/B站等既有教程也有娱乐，必须根据标题/正文/界面元素判断内容性质。
    - 若无法清晰辨认具体内容，降低 confidence，不臆测；必要时归为 other。

    【输入变量】
    - 活跃应用：{activity.app_name}
    - 窗口标题：{activity.window_title}
    - 时间：{activity.timestamp.strftime('%H:%M')}
    - 最近50分钟上下文（仅用于叙事衔接，**不得影响分类**）：{recent_context if recent_context else "无"}

    【两阶段任务】
    1) 任务判断（只看当前截图，**不得使用历史/Dock**）  
    - 先识别各屏幕主要可视区域与前景窗口；以主要注意力所在区域为判断依据。  
    - 依据**内容性质**分类（见下方标准）。  
    - 分类结果一旦确定，**在后续叙事中不得被历史覆盖或修改**。

    2) 叙事生成（可参考 recent_context 仅用于语言衔接）  
    - 在不改变第1步分类结果的前提下，生成50–80字中文描述；  
    - 若当前与历史明显一致，可用“正在/继续…”；若明显不同，可用“从…切换到…”。  
    - 禁止输出推理过程或分步说明，只给结论性描述。

    【多屏分析提示】
    - 整合所有屏幕内容，但以前景/全屏/占据面积最大的区域为主；小窗/后台仅作环境参考，**不得左右分类**。
    - 会议/视频界面：若出现明显麦克风/摄像头/参会UI→ meeting；视频全屏为娱乐内容→ entertainment；技术会议/教程→ browsing（若同时在IDE明确实践，可判 coding）。

    【分类标准（基于内容性质）】
    - coding：编写/调试代码、IDE/终端/Git、跟随编程教程**且截图中可见明确代码编辑或运行**  
    - writing：写文档/邮件/博客/笔记  
    - meeting：实时会议/语音视频通话（工作）  
    - browsing：技术资料/文档/论文/技术教程视频/技术博客/官方文档等的阅读与研究  
    - communication：工作沟通、邮件往来、与AI讨论技术问题  
    - design：UI/UX/绘图/白板/原型  
    - data_analysis：数据处理/可视化/统计分析  
    - entertainment：娱乐视频/综艺/游戏/购物/生活vlog/娱乐直播/游戏攻略等（注意力转向休息娱乐）  
    - other：无法明确分类或因隐私无法展开分析

    【判断要点/示例】
    - 浏览器显示论文/技术文档/API 手册/技术教程页面 → browsing  
    - IDE/终端为前景且可见代码编辑/调试/运行 → coding  
    - 技术教程 + 同屏清晰可见 IDE 实践 → coding（否则为 browsing）  
    - 全屏或主区域为游戏/综艺/vlog/娱乐直播 → entertainment  
    - 背景音乐/播客 ≠ entertainment（若主要在工作）

    【描述质量要求】
    - 50–80字中文；具体说明“做什么/怎么做/用到哪些工具/工作情境/是否多任务”
    - 仅围绕当前截图；可用 recent_context 做**措辞衔接**，但不得改变分类结论
    - 避免空泛表述（如“使用XXX”），禁止输出中间推理

    【confidence 打分标准（与历史无关）】
    - 90–100：能清晰识别具体内容/文件名/代码/页面主题，主要可视区域明确  
    - 70–89：能判断活动类型与主要内容，细节可见度一般  
    - 50–69：只能判断大致方向或依赖窗口标题  
    - 30–49：仅见标题/图标/模糊画面  
    - 0–29：几乎不可辨识

    【仅输出以下有效 JSON（不要任何额外文本）】：
    {{
    "category": "选择上述分类之一",
    "description": "50-80字中文描述；可做语言衔接但不得改变分类结论",
    "confidence": 85
    }}
    """
    elif lang == 'en':
    # English prompt (reworked: classification uses ONLY the current screenshot; narrative may reference history for wording but MUST NOT change the category)
        return f"""You are a "Work Activity Analyzer". Analyze the current **multi-screen screenshot** and output a structured JSON result.

[Hard Rules — override all else if in conflict]
- The activity **category** MUST be decided **only from the current screenshot’s visible content** (foreground / main visual area). Do **NOT** use or reference any history (including recent_context), Dock/Taskbar, background windows, or app icons.
- Platform ≠ content: YouTube/Bilibili host both tutorials and entertainment. Judge by titles/body/UI elements, not platform alone.
- If concrete content is unclear, lower confidence and avoid guessing; use `other` when appropriate.

[Inputs]
- Active App: {activity.app_name}
- Window Title: {activity.window_title}
- Time: {activity.timestamp.strftime('%H:%M')}
- Recent 50-min Context (use ONLY for phrasing in description; **MUST NOT affect category**): {recent_context if recent_context else "None"}

[Two-Stage Task]
1) Categorization (current screenshot ONLY; **no history/Dock**)
   - Identify main visual/foreground region across screens; base the decision on where attention is likely focused.
   - Classify by **content nature** (see standards below).
   - Once chosen, the category is final and **cannot be altered by history**.

2) Narrative Description (may reference `recent_context` for wording ONLY)
   - Without changing the category from step 1, produce a 50–80 word English description.
   - If clearly consistent with history, you may use “continuing…”. If clearly different, you may use “switched from… to…”.
   - Do NOT output chain-of-thought or step-by-step reasoning—only the conclusion.

[Multi-Screen Guidance]
- Consider all screens but prioritize foreground/fullscreen/largest occupied area. Small overlays/background panes are environment only and **must not sway categorization**.
- Meetings/videos: obvious mic/camera/participants UI → meeting. Fullscreen entertainment video → entertainment. Tech talk/tutorial → browsing (if IDE practice is clearly visible at the same time, coding may apply).

[Category Standards — judge by content nature]
- coding: Editing/debugging/running code in IDE/terminal/Git **clearly visible in the screenshot** or actively practicing a programming tutorial with visible code changes.
- writing: Writing docs/emails/blogs/notes.
- meeting: Live work meeting / voice-video conference UI.
- browsing: Reading technical docs/papers/tutorial pages/tech blogs/official docs.
- communication: Work communication, email triage, discussing tech issues with AI assistants.
- design: UI/UX, drawing, whiteboards, prototyping tools.
- data_analysis: Data processing/visualization/statistical analysis.
- entertainment: Entertainment videos, games, social media, shopping, lifestyle vlogs, entertainment streams/guides (attention shifted to rest).
- other: Unclear or privacy-limited content.

[Judgment Hints / Examples]
- Browser shows paper/technical docs/API manual/tutorial page → browsing.
- IDE/terminal foreground with code editing/debugging/running → coding.
- Tech tutorial + clearly visible simultaneous IDE practice → coding (otherwise browsing).
- Fullscreen or dominant area is game/variety/vlog/entertainment stream → entertainment.
- Background music/podcast ≠ entertainment if the main task is work.

[Description Requirements]
- 50–80 words; specify **what/how/tools/context/whether multi-tasking**.
- Focus on the current screenshot; `recent_context` may smooth wording but **must not alter the category**.
- Avoid vague phrases (“using XXX”); no intermediate reasoning in output.

[Confidence Scoring (independent of history)]
- 90–100: Specific content/filenames/code/page topic are clear; main region is unambiguous.
- 70–89: Task type and main content are identifiable; some details visible.
- 50–69: Only broad direction or reliance on window title.
- 30–49: Only title/icons/blurred content visible.
- 0–29: Nearly unidentifiable.

[Return ONLY valid JSON — no extra text]:
{{
  "category": "choose one from coding, writing, meeting, browsing, communication, design, data_analysis, entertainment, other",
  "description": "50-80 word English description; may use wording continuity but must not change category",
  "confidence": 85
}}
"""

    elif lang == 'ja':
    # 日本語プロンプト（再設計：カテゴリ判定は現在のスクショのみ／叙述は履歴を表現上のみ参照可）
        return f"""あなたは「作業活動分析アシスタント」です。現在の**マルチスクリーン・スクリーンショット**を分析し、構造化JSONのみを出力してください。

【最優先ルール（他指示と矛盾する場合は本ルールを優先）】
- 活動の **category** は、**現在のスクリーンショットに可視な内容（前景／主要表示領域）だけ**から決定すること。recent_context を含む過去情報、Dock/タスクバー、背面ウィンドウ、アプリアイコンは**参照禁止**。
- プラットフォーム≠コンテンツ：YouTube/Bilibili にはチュートリアルも娯楽もある。必ずタイトル／本文／UI要素で内容性質を判断すること。
- 内容が不鮮明な場合は confidence を下げ、推測で断定しない。必要なら other を用いる。

【入力変数】
- アクティブアプリ: {activity.app_name}
- ウィンドウタイトル: {activity.window_title}
- 時刻: {activity.timestamp.strftime('%H:%M')}
- 直近50分の文脈（**叙述の言い回しにのみ使用可／カテゴリには影響不可**）: {recent_context if recent_context else "なし"}

【二段階タスク】
1) カテゴリ判定（現在スクショのみ／**履歴やDockは使用不可**）  
   - 画面全体を見て主要表示領域（前景・全画面・最大面積）を特定し、**注意の主対象**に基づき判定。  
   - 下記の**内容性質**に従って分類。  
   - いったん決めた category は、この後の叙述で**履歴によって変更してはならない**。

2) 叙述生成（`recent_context` は表現の**連結目的に限り使用可**）  
   - 第1段階の category を変更せず、50〜80文字の日本語説明を生成。  
   - 履歴と明確に整合するなら「継続…」、明確に異なるなら「…から…に切り替え」を用いてよい。  
   - 推論過程や手順は出力しない。結論のみ記述。

【マルチスクリーン指針】
- すべての画面を考慮しつつ、前景／全画面／最大面積の領域を優先。小ウィンドウや背面は環境情報に留め、**カテゴリを左右してはならない**。  
- 会議／動画：マイク・カメラ・参加者UIが明確→ meeting。娯楽動画が全画面→ entertainment。技術講演／チュートリアル→ browsing（かつIDEでの同時実装が**明確に可視**なら coding）。

【カテゴリ基準（内容性質で判断）】
- coding：IDE/ターミナル/Git での**明確な**コード編集・デバッグ・実行、またはプログラミングチュートリアルを**画面上で実装**している様子が可視  
- writing：文書・メール・ブログ・ノート作成  
- meeting：業務のオンライン会議UI（音声/映像/参加者UI）  
- browsing：技術ドキュメント／論文／チュートリアルページ／技術ブログ／公式ドキュメント等の読解  
- communication：業務連絡、メール対応、AIアシスタントとの技術議論  
- design：UI/UX、描画、ホワイトボード、プロトタイピング  
- data_analysis：データ処理・可視化・統計分析  
- entertainment：娯楽動画・ゲーム・SNS・ショッピング・生活vlog・娯楽配信／攻略（注意が休憩へ）  
- other：不明瞭またはプライバシーのため詳細不可

【判定ヒント／例】
- ブラウザで論文／技術文書／APIマニュアル／チュートリアルページ → browsing  
- IDE/ターミナルが前景でコード編集／デバッグ／実行が可視 → coding  
- 技術チュートリアル＋同時にIDE実装が**明確** → coding（それ以外は browsing）  
- 全画面または主領域がゲーム／バラエティ／vlog／娯楽配信 → entertainment  
- 作業中のBGM/ポッドキャストは entertainment に数えない

【説明要件】
- 50〜80文字の日本語。**何を／どうやって／使用ツール／状況／マルチタスクの有無**を具体的に。  
- 焦点は現在のスクショ。`recent_context` は**言い回しの連結**にのみ使用し、カテゴリは変えない。  
- 「XXXを使用」などの曖昧表現は避ける。中間推論は出力しない。

【confidence（履歴と無関係）】
- 90–100：具体的内容／ファイル名／コード／ページ主題が明確で主要領域が一意  
- 70–89：作業タイプと主要内容が判別可能、詳細は一部可視  
- 50–69：大まかな方向のみ、タイトル依存  
- 30–49：タイトル／アイコンのみ、内容は不鮮明  
- 0–29：ほぼ判別不能

【出力は以下の有効なJSONのみ（余計な文は不可）】：
{{
  "category": "coding | writing | meeting | browsing | communication | design | data_analysis | entertainment | other のいずれか1つ",
  "description": "50〜80文字の日本語説明。連結表現は可だがカテゴリは不変更",
  "confidence": 85
}}
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
