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
        system_msg = "你是一个专业的工作日志撰写助手，擅长将零散的工作记录整合成连贯、有价值的工作总结。只输出工作日志内容，不要添加其他格式。"
        prompt = f"""请根据以下工作记录，生成一份专业的每日工作日志。

**日期：** {target_date.strftime('%Y年%m月%d日')} {weekday_name}

**工作统计：**
- 有效工作时长：约 {work_hours:.1f} 小时（{record_count} 条记录）
- 工作类型分布：
{category_breakdown}
- 使用的主要工具：{main_tools}

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
3. 整合相关的工作活动，不要逐条罗列，而要形成连贯的叙述
4. 突出主要工作内容和具体成果，提及关键的工具和技术
5. 如果有明显的专注时段或任务切换，要特别指出
6. 语气专业但友好，就像向同事或上级汇报一天的工作
7. 避免流水账式的描述，要提炼出工作的重点和亮点

**输出格式示例：**
今天的工作主要集中在 [项目/领域]。上午 [时段] 主要处理 [具体任务]，使用 [工具] 完成了 [成果]。期间查阅了 [资料/文档] 以解决 [问题]。

下午工作重心转向 [另一任务]，在 [具体操作] 方面取得了 [进展]。

整体来看，今天在 [总结性描述] 方面进展顺利。

**注意：**
- 不要简单列举"使用了VSCode"这样的表述
- 要说明在工具中做了什么、达成了什么
- 相关活动要整合，如"编程"+"查文档"+"测试" = "开发某功能"
- 直接输出日志内容，不要添加标题或其他格式

现在请生成工作日志：
"""
        return prompt, system_msg

    elif lang == 'en':
        system_msg = "You are a professional work log writer who excels at integrating scattered work records into coherent and valuable work summaries. Only output the work log content without any additional formatting."
        prompt = f"""Please generate a professional daily work log based on the following work records.

**Date:** {target_date.strftime('%Y-%m-%d')} {weekday_name}

**Work Statistics:**
- Effective work duration: approximately {work_hours:.1f} hours ({record_count} records)
- Work type distribution:
{category_breakdown}
- Main tools used: {main_tools}

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
3. Integrate related work activities into a coherent narrative, rather than listing them one by one
4. Highlight main work content and concrete achievements, mentioning key tools and technologies
5. Point out any obvious periods of focus or task switching
6. Use a professional but friendly tone, as if reporting the day's work to colleagues or supervisors
7. Avoid itemized descriptions; extract key points and highlights

**Output Format Example:**
Today's work mainly focused on [project/area]. In the morning [time period], I primarily handled [specific task], using [tool] to complete [achievement]. During this time, I consulted [resources/documents] to solve [problem].

In the afternoon, the focus shifted to [another task], making [progress] in [specific operations].

Overall, today made good progress in [summary description].

**Notes:**
- Don't simply list things like "used VSCode"
- Explain what was done in the tool and what was achieved
- Related activities should be integrated, e.g., "coding" + "checking docs" + "testing" = "developing a feature"
- Output the log content directly without adding titles or other formatting

Now please generate the work log:
"""
        return prompt, system_msg

    elif lang == 'ja':
        system_msg = "あなたはプロの作業ログ作成アシスタントで、断片的な作業記録をまとまりのある価値のある作業サマリーに統合することが得意です。作業ログの内容のみを出力し、他のフォーマットは追加しないでください。"
        prompt = f"""以下の作業記録に基づいて、プロフェッショナルな毎日の作業ログを生成してください。

**日付：** {target_date.strftime('%Y年%m月%d日')} {weekday_name}

**作業統計：**
- 有効作業時間：約 {work_hours:.1f} 時間（{record_count} 件の記録）
- 作業タイプの分布：
{category_breakdown}
- 主に使用したツール：{main_tools}

**時間帯別の活動詳細：**

午前（9:00-12:00）：
{morning_activities}

午後（12:00-18:00）：
{afternoon_activities}

夜間（18:00-24:00）：
{evening_activities}

**生成要件：**
1. 物語調の日本語で書き、250～350文字程度
2. 時間帯ごとに内容を整理（午前、午後、夜間）
3. 関連する作業活動を統合し、一つずつ列挙するのではなく、まとまりのある叙述を形成する
4. 主な作業内容と具体的な成果を強調し、重要なツールや技術について言及する
5. 明らかな集中時間帯やタスクの切り替えがあれば、特に指摘する
6. プロフェッショナルだが親しみやすい口調で、同僚や上司に一日の作業を報告するように
7. 箇条書き的な説明を避け、作業のポイントとハイライトを抽出する

**出力形式の例：**
今日の作業は主に[プロジェクト/分野]に集中しました。午前[時間帯]は主に[具体的なタスク]を処理し、[ツール]を使用して[成果]を完成させました。その間、[問題]を解決するために[資料/ドキュメント]を参照しました。

午後は作業の重点が[別のタスク]に移り、[具体的な操作]において[進展]を遂げました。

全体的に見て、今日は[要約的な説明]において順調に進展しました。

**注意：**
- 単に「VSCodeを使った」のような表現を列挙しないでください
- ツールで何をしたか、何を達成したかを説明してください
- 関連する活動を統合してください。例：「コーディング」+「ドキュメント確認」+「テスト」=「機能の開発」
- ログの内容を直接出力し、タイトルや他のフォーマットを追加しないでください

それでは作業ログを生成してください：
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