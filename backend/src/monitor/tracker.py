"""
窗口追踪模块
负责获取当前活跃的应用和窗口标题
支持检测系统锁屏和睡眠状态
"""

import logging
import platform
from typing import Dict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_active_window() -> Dict[str, str]:
    """
    获取当前活跃的窗口信息

    Returns:
        Dict[str, str]: 包含 app_name 和 title 的字典
                       {"app_name": "应用名称", "title": "窗口标题"}
                       失败时返回 {"app_name": "Unknown", "title": "Unknown"}
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            return _get_active_window_macos()
        elif system == "Windows":
            return _get_active_window_windows()
        elif system == "Linux":
            return _get_active_window_linux()
        else:
            logger.warning(f"不支持的操作系统: {system}")
            return {"app_name": "Unknown", "title": "Unknown"}

    except Exception as e:
        logger.error(f"获取活跃窗口失败: {e}")
        return {"app_name": "Unknown", "title": "Unknown"}


def _get_active_window_macos() -> Dict[str, str]:
    """
    macOS 平台获取活跃窗口信息
    使用 AppKit 和 Quartz 框架

    Returns:
        Dict[str, str]: 窗口信息字典
    """
    try:
        from AppKit import NSWorkspace
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        # 获取当前活跃应用
        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        app_name = active_app.get('NSApplicationName', 'Unknown')

        # 获取窗口标题
        window_list = CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )

        # 查找活跃应用的窗口
        title = ""
        for window in window_list:
            if window.get('kCGWindowOwnerName', '') == app_name:
                window_title = window.get('kCGWindowName', '')
                if window_title:
                    title = window_title
                    break

        # 如果没找到标题，使用应用名
        if not title:
            title = app_name

        logger.debug(f"活跃窗口: {app_name} - {title}")
        return {"app_name": app_name, "title": title}

    except ImportError as e:
        logger.error(f"macOS 依赖库未安装: {e}")
        return {"app_name": "Unknown", "title": "Unknown"}
    except Exception as e:
        logger.error(f"macOS 获取窗口失败: {e}")
        return {"app_name": "Unknown", "title": "Unknown"}


def _get_active_window_windows() -> Dict[str, str]:
    """
    Windows 平台获取活跃窗口信息
    使用 pygetwindow

    Returns:
        Dict[str, str]: 窗口信息字典
    """
    try:
        import pygetwindow as gw

        # 获取当前活跃窗口
        active_window = gw.getActiveWindow()

        if active_window:
            title = active_window.title
            # 简单提取应用名（从标题推测）
            app_name = title.split('-')[-1].strip() if '-' in title else title

            logger.debug(f"活跃窗口: {app_name} - {title}")
            return {"app_name": app_name, "title": title}
        else:
            return {"app_name": "Unknown", "title": "Unknown"}

    except ImportError:
        logger.error("Windows 依赖库未安装，请运行: pip install pygetwindow")
        return {"app_name": "Unknown", "title": "Unknown"}
    except Exception as e:
        logger.error(f"Windows 获取窗口失败: {e}")
        return {"app_name": "Unknown", "title": "Unknown"}


def _get_active_window_linux() -> Dict[str, str]:
    """
    Linux 平台获取活跃窗口信息
    暂时返回模拟数据

    Returns:
        Dict[str, str]: 窗口信息字典
    """
    logger.warning("Linux 平台支持暂未实现，返回模拟数据")
    return {"app_name": "LinuxApp", "title": "Linux Window"}


def is_system_locked_or_sleeping() -> bool:
    """
    检测系统是否处于锁屏或睡眠状态

    Returns:
        bool: True 表示系统已锁屏或睡眠，False 表示正常活跃状态
    """
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            return _is_locked_macos()
        elif system == "Windows":
            return _is_locked_windows()
        elif system == "Linux":
            return _is_locked_linux()
        else:
            logger.warning(f"不支持的操作系统: {system}")
            return False

    except Exception as e:
        logger.error(f"检测系统锁屏状态失败: {e}")
        return False


def _is_locked_macos() -> bool:
    """
    检测 macOS 系统是否锁屏

    使用 Quartz.CGSessionCopyCurrentDictionary() 检测
    当屏幕锁定时，字典中会包含 'CGSSessionScreenIsLocked' 键

    Returns:
        bool: True 表示已锁屏，False 表示未锁屏
    """
    try:
        from Quartz import CGSessionCopyCurrentDictionary

        session_dict = CGSessionCopyCurrentDictionary()

        # 如果返回 None（例如 SSH 会话），假定为未锁屏
        if session_dict is None:
            return False

        # 检查是否包含锁屏标志
        is_locked = session_dict.get("CGSSessionScreenIsLocked", 0) == 1

        if is_locked:
            logger.debug("系统已锁屏")
        return is_locked

    except ImportError as e:
        logger.error(f"macOS Quartz 库未安装: {e}")
        return False
    except Exception as e:
        logger.error(f"检测 macOS 锁屏状态失败: {e}")
        return False


def _is_locked_windows() -> bool:
    """
    检测 Windows 系统是否锁屏

    TODO: 实现 Windows 锁屏检测
    可以使用 ctypes 调用 Windows API

    Returns:
        bool: True 表示已锁屏，False 表示未锁屏
    """
    logger.warning("Windows 锁屏检测暂未实现")
    return False


def _is_locked_linux() -> bool:
    """
    检测 Linux 系统是否锁屏

    TODO: 实现 Linux 锁屏检测
    不同桌面环境（GNOME, KDE, etc.）需要不同的方法

    Returns:
        bool: True 表示已锁屏，False 表示未锁屏
    """
    logger.warning("Linux 锁屏检测暂未实现")
    return False


if __name__ == "__main__":
    # 测试代码
    print("测试窗口追踪功能...")
    print(f"当前操作系统: {platform.system()}")

    window_info = get_active_window()
    print(f"\n当前活跃窗口:")
    print(f"  应用名称: {window_info['app_name']}")
    print(f"  窗口标题: {window_info['title']}")

    if window_info['app_name'] != "Unknown":
        print("\n✓ 窗口追踪功能正常")
    else:
        print("\n✗ 窗口追踪功能异常")
