"""
摘要生成模块
根据一天的 Activity 记录，调用 OpenAI Responses API 生成每日工作摘要
"""

from datetime import datetime
from openai import OpenAI
import os
import re
import logging
from collections import Counter
from dotenv import load_dotenv

from ..database.db import get_activities_by_date, save_summary
from ..utils.config import get_config

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

def _get_text_from_responses(resp):
    """从 Responses API 响应中提取文本"""
    try:
        if hasattr(resp, "output_text"):
            return resp.output_text
        elif hasattr(resp, "choices") and len(resp.choices) > 0:
            return resp.choices[0].message.content
        else:
            return None
    except Exception as e:
        logger.error(f"提取响应文本失败: {e}")
        return None


def get_summary_prompt(lang: str, target_date, weekday_name: str, work_hours: float,
                       record_count: int, category_breakdown: str, main_tools: str,
                       morning_activities: str, afternoon_activities: str, evening_activities: str) -> tuple:
    """
    根据语言返回对应的摘要生成 prompt 和 system message

    Args:
        lang: 语言代码 ('zh', 'en', 'ja')
        target_date: 目标日期
        weekday_name: 星期几的名称
        work_hours: 工作小时数
        record_count: 记录数量
        category_breakdown: 分类统计
        main_tools: 主要工具
        morning_activities: 上午活动
        afternoon_activities: 下午活动
        evening_activities: 晚上活动

    Returns:
        tuple: (prompt, system_message)
    """

    if lang == 'zh':
        system_msg = "你是一个专业的活动记录分析助手，擅长将零散的活动记录整合成连贯、有价值的每日总结。只输出总结内容，不要添加其他格式。"
        prompt = f"""请根据以下活动记录，生成一份清晰的每日总结。

**日期：** {target_date.strftime('%Y年%m月%d日')} {weekday_name}

**活动统计：**
- 活跃时长：约 {work_hours:.1f} 小时（{record_count} 条记录）
- 活动类型分布：
{category_breakdown}
- 主要使用的工具：{main_tools}

**时段活动详情：**

上午（9:00-12:00）：
{morning_activities}

下午（12:00-18:00）：
{afternoon_activities}

晚上（18:00-24:00）：
{evening_activities}

**生成要求：**
1. 用叙事性的中文写作，字数在 250-350 字之间
2. 按时间段组织内容（上午、下午、晚上）
3. 整合相关的活动，不要逐条罗列，而要形成连贯的叙述
4. 突出主要内容和具体成果，提及关键的工具和技术
5. 如果有明显的专注时段或活动切换，要特别指出
6. 语气自然友好，就像给自己写一份简明的每日回顾
7. 避免流水账式的描述，要提炼出重点和亮点

**输出格式示例：**
今天主要在 [项目/学习/创作等]。上午 [时段] 主要在 [具体内容]，使用 [工具] 完成了 [成果]。期间查阅了 [资料/文档] 来解决 [问题]。

下午重心转向 [另一活动]，在 [具体操作] 方面有所进展。

整体来看，今天在 [总结性描述] 方面进展顺利/收获不少。

**注意：**
- 不要简单列举"使用了VSCode"这样的表述
- 要说明在工具中做了什么、达成了什么
- 相关活动要整合，如"编程"+"查文档"+"测试" = "开发某功能"
- 如果包含学习、娱乐等非工作活动，自然地描述即可，不要刻意回避
- 直接输出总结内容，不要添加标题或其他格式

现在请生成每日总结：
"""
        return prompt, system_msg

    elif lang == 'en':
        system_msg = "You are a professional activity analysis assistant, skilled at integrating scattered activity records into coherent and valuable daily summaries. Only output the summary content without additional formatting."
        prompt = f"""Please generate a clear daily summary based on the following activity records.

**Date:** {target_date.strftime('%B %d, %Y')} ({weekday_name})

**Activity Statistics:**
- Active Duration: approximately {work_hours:.1f} hours ({record_count} records)
- Activity Type Distribution:
{category_breakdown}
- Main Tools Used: {main_tools}

**Activity Details by Time Period:**

Morning (9:00-12:00):
{morning_activities}

Afternoon (12:00-18:00):
{afternoon_activities}

Evening (18:00-24:00):
{evening_activities}

**Generation Requirements:**
1. Write in narrative English, 250-350 words
2. Organize content by time periods (morning, afternoon, evening)
3. Integrate related activities into coherent narrative, not just listing
4. Highlight main content and specific achievements, mention key tools and techniques
5. Point out focused periods or activity transitions if notable
6. Natural and friendly tone, like writing a brief daily review for yourself
7. Avoid trivial details, extract key points and highlights

**Output Format Example:**
Today mainly focused on [project/learning/creation]. In the morning [period], primarily worked on [specific content], using [tools] to complete [achievements]. Referenced [materials/docs] to solve [problems].

In the afternoon, focus shifted to [another activity], making progress in [specific operations].

Overall, today made good progress/gained valuable experience in [summary].

**Notes:**
- Don't just list "used VSCode"
- Explain what was done with the tools and what was achieved
- Integrate related activities, e.g., "coding"+"checking docs"+"testing" = "developing a feature"
- If including learning, entertainment, or non-work activities, describe them naturally without avoiding
- Output summary content directly without adding titles or other formatting

Now please generate the daily summary:
"""
        return prompt, system_msg

    elif lang == 'ja':
        system_msg = "あなたはプロの活動記録分析アシスタントで、散在する活動記録を首尾一貫した価値のある日次サマリーに統合することに長けています。サマリーの内容のみを出力し、他の書式は追加しないでください。"
        prompt = f"""以下の活動記録に基づいて、明確な日次サマリーを作成してください。

**日付：** {target_date.strftime('%Y年%m月%d日')} ({weekday_name})

**活動統計：**
- アクティブ時間：約{work_hours:.1f}時間（{record_count}件の記録）
- 活動タイプの分布：
{category_breakdown}
- 主な使用ツール：{main_tools}

**時間帯別の活動詳細：**

午前（9:00-12:00）：
{morning_activities}

午後（12:00-18:00）：
{afternoon_activities}

夜間（18:00-24:00）：
{evening_activities}

**生成要件：**
1. 日本語で叙述的に、250-350文字で記述
2. 時間帯別に内容を整理（午前、午後、夜間）
3. 関連する活動を統合し、リスト形式ではなく一貫したナラティブに
4. 主な内容と具体的な成果を強調し、重要なツールや技術に言及
5. 集中期間や活動の切り替えがあれば特に指摘
6. 自然で親しみやすい口調で、自分用の簡潔な日次レビューを書くように
7. 細かい詳細を避け、要点とハイライトを抽出

**出力形式例：**
今日は主に[プロジェクト/学習/創作]に取り組みました。午前中は[具体的な内容]に取り組み、[ツール]を使用して[成果]を完成させました。[問題]を解決するために[資料/ドキュメント]を参照しました。

午後は[別の活動]に重点を移し、[具体的な操作]で進展がありました。

全体的に、今日は[要約的な説明]において順調に進展/良い収穫がありました。

**注意：**
- 「VSCodeを使用した」のような単純な列挙を避ける
- ツールで何をしたか、何を達成したかを説明する
- 関連する活動を統合（「コーディング」+「ドキュメント確認」+「テスト」=「機能開発」）
- 学習、娯楽などの非作業活動が含まれる場合は、自然に記述し、回避しない
- サマリー内容を直接出力し、タイトルや他の書式を追加しない

それでは、日次サマリーを生成してください：
"""
        return prompt, system_msg

    else:
        # 默认使用中文
        return get_summary_prompt('zh', target_date, weekday_name, work_hours, record_count,
                                 category_breakdown, main_tools, morning_activities,
                                 afternoon_activities, evening_activities)

def generate_daily_summary(date=None) -> str:
    """
    生成指定日期的每日工作摘要。

    Args:
        date (datetime.date or datetime.datetime, optional): 目标日期，默认为今天

    Returns:
        str: 摘要文本，或失败提示
    """
    # 确定目标日期
    if date is None:
        date = datetime.today()
    if isinstance(date, datetime):
        target_date = date.date()
    else:
        target_date = date

    # 查询当天已分析的活动
    activities = get_activities_by_date(target_date)
    analyzed_activities = [a for a in activities if a.analyzed]
    if not analyzed_activities:
        return f"{target_date.strftime('%Y年%m月%d日')} 暂无工作记录"

    # 基本统计
    record_count = len(analyzed_activities)
    work_minutes = record_count * 10
    work_hours = work_minutes / 60

    # 分类分布
    categories = [a.category for a in analyzed_activities]
    category_counter = Counter(categories)
    total = len(categories)
    category_breakdown = "\n".join([
        f"  - {cat}: {count}次 ({count/total*100:.1f}%)"
        for cat, count in category_counter.most_common()
    ])

    # 主要工具
    apps = [a.app_name for a in analyzed_activities]
    app_counter = Counter(apps)
    main_tools = ", ".join([app for app, _ in app_counter.most_common(5)])

    # 时段活动
    def get_time_period(ts):
        h = ts.hour
        if 6 <= h < 12:
            return "morning"
        elif 12 <= h < 18:
            return "afternoon"
        elif 18 <= h < 24:
            return "evening"
        else:
            return "night"

    morning_acts, afternoon_acts, evening_acts = [], [], []
    for act in analyzed_activities:
        period = get_time_period(act.timestamp)
        time_str = act.timestamp.strftime("%H:%M")
        desc = act.description or "进行工作"
        if period == "morning":
            morning_acts.append(f"  {time_str} - {desc}")
        elif period == "afternoon":
            afternoon_acts.append(f"  {time_str} - {desc}")
        elif period == "evening":
            evening_acts.append(f"  {time_str} - {desc}")

    # 获取用户语言配置
    config = get_config()
    user_lang = config.get('language', 'zh')

    # 根据语言设置"无活动"的文本和星期几的名称
    if user_lang == 'zh':
        no_activity_text = "无"
        weekday_map = {
            0: "星期一", 1: "星期二", 2: "星期三",
            3: "星期四", 4: "星期五", 5: "星期六", 6: "星期日"
        }
    elif user_lang == 'en':
        no_activity_text = "None"
        weekday_map = {
            0: "Monday", 1: "Tuesday", 2: "Wednesday",
            3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"
        }
    elif user_lang == 'ja':
        no_activity_text = "なし"
        weekday_map = {
            0: "月曜日", 1: "火曜日", 2: "水曜日",
            3: "木曜日", 4: "金曜日", 5: "土曜日", 6: "日曜日"
        }
    else:
        no_activity_text = "无"
        weekday_map = {
            0: "星期一", 1: "星期二", 2: "星期三",
            3: "星期四", 4: "星期五", 5: "星期六", 6: "星期日"
        }

    weekday = weekday_map[target_date.weekday()]

    morning_activities = "\n".join(morning_acts[:5]) if morning_acts else no_activity_text
    afternoon_activities = "\n".join(afternoon_acts[:5]) if afternoon_acts else no_activity_text
    evening_activities = "\n".join(evening_acts[:5]) if evening_acts else no_activity_text

    # 构建多语言 Prompt
    prompt, system_msg = get_summary_prompt(
        user_lang, target_date, weekday, work_hours, record_count,
        category_breakdown, main_tools,
        morning_activities, afternoon_activities, evening_activities
    )

    # 调用 OpenAI API
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("调用 OpenAI API 生成摘要...")
        model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
        resp = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": system_msg
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt}
                    ]
                }
            ]
        )
        result_text = (_get_text_from_responses(resp) or "").strip()
        if result_text.startswith("```"):
            result_text = re.sub(r"^```(?:markdown|text)?\s*|\s*```$", "", result_text, flags=re.S)
        if not result_text:
            logger.error("OpenAI API 返回空内容")
            raise ValueError("Empty output from OpenAI API")
        summary_text = result_text.strip()
        save_summary(target_date, summary_text)
        logger.info(f"✅ 摘要生成成功: {len(summary_text)} 字")
        print(f"✅ 摘要生成成功: {len(summary_text)} 字")
        return summary_text
    except Exception as e:
        error_msg = f"生成摘要时出错: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return f"{target_date.strftime('%Y年%m月%d日')} 的工作摘要生成失败"