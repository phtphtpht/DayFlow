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

        # d. 构建详细的 prompt
        prompt = f"""你是一个专业的工作活动分析助手。请**深入分析**这张多屏幕截图，详细识别用户正在进行的工作。

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

2. **理解具体的工作内容**
   - 不要只说"使用VSCode"，而要说明在VSCode中做什么（写代码？调试？看文件？）
   - 如果能看到代码，识别编程语言和正在处理的功能
   - 如果是浏览器，识别具体网站和页面内容
   - 如果是终端，识别正在执行的命令

3. **分析工作的上下文和目的**
   - 结合历史上下文，判断工作的连续性
   - 推断用户为什么这样工作（如：边写代码边查文档是在学习新技术）
   - 识别工作流程（如：编码→测试→调试的循环）

4. **判断任务状态**
   - 延续之前的工作？（请在描述中体现"继续..."、"接着..."）
   - 切换到新任务？（请明确说明"从...切换到..."）
   - 临时中断？（如：查看通知、休息）

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

**分类标准：**
- **coding**：编写代码、调试程序、查看代码、使用IDE、终端操作、Git操作、代码审查
- **writing**：写文档、写邮件、写文章、编辑文本、做笔记、撰写技术文档
- **meeting**：视频会议、在线会议、演示文稿展示、屏幕共享讨论
- **browsing**：浏览网页、查阅资料、阅读技术文档、搜索信息、学习新知识
- **communication**：聊天工具（Slack/Teams/微信/Discord）、查看/回复邮件、与AI助手对话
- **design**：使用设计工具（Figma/Photoshop/Sketch等）、绘图、UI/UX设计
- **data_analysis**：查看数据表格、制作图表、使用数据分析工具、处理数据
- **entertainment**：社交媒体、视频网站、游戏、购物、休闲浏览
- **other**：其他活动或无法明确分类

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

**特别提醒：**
- 仔细观察截图中的文字、代码、界面元素
- 不要满足于表面的应用名称，要深入理解工作内容
- 多屏幕要整合分析，不要只看活跃窗口
- 描述要像一个了解技术的同事在记录工作日志一样详细

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
