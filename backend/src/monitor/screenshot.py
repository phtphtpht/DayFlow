"""
截图模块
负责截取屏幕并保存到本地目录
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from mss import mss
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 截图保存目录（相对于项目根目录）
SCREENSHOT_DIR = "data/screenshots"


def ensure_screenshot_dir() -> str:
    """
    确保截图目录存在

    Returns:
        str: 截图目录的绝对路径
    """
    try:
        # 获取项目根目录（backend/src/monitor -> 向上3级）
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        screenshot_path = project_root / SCREENSHOT_DIR

        # 创建目录（如果不存在）
        screenshot_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"截图目录已确认: {screenshot_path}")
        return str(screenshot_path)

    except Exception as e:
        logger.error(f"创建截图目录失败: {e}")
        raise


def take_screenshot() -> str | None:
    """
    截取所有显示器的屏幕
    对于多显示器环境，会截取包含所有屏幕的完整画面

    Returns:
        str | None: 成功返回截图文件的完整路径，失败返回 None
    """
    try:
        # 确保目录存在
        screenshot_dir = ensure_screenshot_dir()

        # 生成文件名：screenshot_20250104_143022.png
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = os.path.join(screenshot_dir, filename)

        # 使用 mss 截取所有显示器
        with mss() as sct:
            # monitor 0 是所有显示器的合集（包含主屏幕和外接显示器）
            monitor = sct.monitors[0]

            # 截图
            screenshot = sct.grab(monitor)

            # 转换为 PIL Image 并保存
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.save(filepath, "PNG")

            logger.info(f"截图已保存: {filepath}")
            return filepath

    except Exception as e:
        logger.error(f"截图失败: {e}")
        return None


if __name__ == "__main__":
    # 测试代码
    print("测试截图功能...")
    result = take_screenshot()
    if result:
        print(f"✓ 截图成功: {result}")
    else:
        print("✗ 截图失败")
