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
                "confidence": int,
                "details": dict
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

        # d. 构建详细的 prompt
        prompt = f"""你是一个工作活动分析助手。请分析这张多屏幕截图，识别用户正在进行的工作。

**重要提示：这是多屏幕截图**
- 图片包含用户的所有显示器内容
- 当前活跃窗口（用户正在操作的）：{activity.app_name}
- 但请综合**所有屏幕**的内容来判断用户真正在做什么

**最近的工作上下文（过去50分钟）：**
{recent_context if recent_context else "无历史记录（这是今天的第一条记录）"}

**分析任务：**
1. 查看所有屏幕上的内容
2. 判断用户当前的主要工作任务
3. 结合历史上下文，判断是：
   - 延续之前的工作（请在描述中体现连贯性）
   - 切换到新的工作任务（请明确说明切换）
   - 临时中断/休息

**当前信息：**
- 活跃应用：{activity.app_name}
- 窗口标题：{activity.window_title}
- 时间：{activity.timestamp.strftime('%H:%M')}

**综合判断示例：**
❌ 差："使用VSCode编程"
✅ 好："继续调试用户认证模块，现在在查看API文档（Chrome副屏），同时在终端运行测试"
✅ 好："从编程工作切换到文档编写，正在更新项目README"

**分类标准：**
- **coding**：编写代码、调试程序、查看代码、使用IDE、终端操作、Git操作
- **writing**：写文档、写邮件、写文章、编辑文本、做笔记
- **meeting**：视频会议、在线会议、演示文稿展示
- **browsing**：浏览网页、查阅资料、阅读技术文档、搜索信息
- **communication**：聊天工具（Slack/Teams/微信）、查看/回复邮件
- **design**：使用设计工具（Figma/Photoshop等）、绘图、UI设计
- **data_analysis**：查看数据表格、制作图表、数据分析工具
- **entertainment**：社交媒体、视频网站、游戏、购物
- **other**：其他活动或无法明确分类

**返回格式（必须是有效的JSON）：**
{{
  "category": "选择上述分类之一",
  "description": "结合上下文和多屏幕内容的具体描述，20-30字",
  "confidence": 85,
  "details": {{
    "tool_or_platform": "主要工具",
    "specific_content": "识别到的具体内容",
    "is_work_related": true,
    "task_continuity": "continuing或switched或interrupted",
    "all_visible_apps": ["识别到的应用列表"]
  }}
}}

**confidence 打分标准：**
- 90-100：能清晰识别具体工作内容，多屏幕内容一致，与历史高度相关
- 70-89：能识别工作类型和主要内容，但细节不够清晰
- 50-69：只能识别应用类型，屏幕内容模糊
- 30-49：信息不足，难以判断
- 0-29：无法识别

只返回JSON，不要任何其他文字。
"""

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
            ],
            max_output_tokens=2000,  # 增加到 2000，给 reasoning 和 output 足够空间
            # 不要传 temperature/top_p；不少新模型不支持
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
            f"描述: {result['description'][:30]}..."
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
            "description": "分析失败",
            "confidence": 0,
            "details": {
                "error": str(e)
            }
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
        'confidence': 0,
        'details': {}
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
        if 'details' in result:
            print(f"  详细信息: {json.dumps(result['details'], indent=2, ensure_ascii=False)}")

        print("\n✓ 分析完成")

    except Exception as e:
        print(f"\n✗ 分析失败: {e}")
        sys.exit(1)
