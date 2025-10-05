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

    morning_activities = "\n".join(morning_acts[:5]) if morning_acts else "无"
    afternoon_activities = "\n".join(afternoon_acts[:5]) if afternoon_acts else "无"
    evening_activities = "\n".join(evening_acts[:5]) if evening_acts else "无"

    # 构建 Prompt
    weekday_map = {
        0: "星期一", 1: "星期二", 2: "星期三",
        3: "星期四", 4: "星期五", 5: "星期六", 6: "星期日"
    }
    weekday = weekday_map[target_date.weekday()]
    prompt = f"""请根据以下工作记录，生成一份专业的每日工作日志。

**日期：** {target_date.strftime('%Y年%m月%d日')} {weekday}

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
                    "content": "你是一个专业的工作日志撰写助手，擅长将零散的工作记录整合成连贯、有价值的工作总结。只输出工作日志内容，不要添加其他格式。"
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt}
                    ]
                }
            ],
            max_output_tokens=2000
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