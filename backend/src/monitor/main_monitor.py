"""
主监控模块
整合截图、窗口追踪、智能采样功能
"""

import logging
import time
import threading
from datetime import datetime

from .screenshot import take_screenshot
from .tracker import get_active_window
from .sampler import SmartSampler
from ..database.db import init_db, save_activity
from ..ai.analyzer import analyze_screenshot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkMonitor:
    """
    工作监控器
    持续监控用户活动，智能截图
    """

    def __init__(self, test_mode: bool = False):
        """
        初始化监控器

        Args:
            test_mode: 测试模式，设为 True 时截图间隔为 10 秒
        """
        self.sampler = SmartSampler(test_mode=test_mode)
        self.is_running = False
        logger.info("工作监控器已初始化")

    def start(self):
        """
        启动监控
        进入无限循环，每秒检查一次窗口状态
        """
        if self.is_running:
            logger.warning("监控器已经在运行中")
            return

        # 初始化数据库
        logger.info("初始化数据库...")
        init_db()

        self.is_running = True
        logger.info("=" * 60)
        logger.info("工作监控器已启动")
        logger.info("=" * 60)

        try:
            while self.is_running:
                self._monitor_cycle()
                time.sleep(1)  # 每秒检查一次

        except KeyboardInterrupt:
            logger.info("\n检测到 Ctrl+C，正在停止监控...")
            self.stop()

        except Exception as e:
            logger.error(f"监控过程发生错误: {e}", exc_info=True)
            self.stop()

    def _monitor_cycle(self):
        """
        单次监控循环
        获取窗口信息 -> 判断是否截图 -> 执行截图
        """
        try:
            # 1. 获取当前活跃窗口信息
            window_info = get_active_window()
            current_app = window_info["app_name"]
            current_title = window_info["title"]

            # 2. 判断是否需要截图
            should_capture, reason = self.sampler.should_capture(
                current_app, current_title
            )

            # 3. 记录日志
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if should_capture:
                # 执行截图
                screenshot_path = take_screenshot()

                if screenshot_path:
                    # 保存到数据库
                    try:
                        activity_id = save_activity(
                            app_name=current_app,
                            window_title=current_title,
                            screenshot_path=screenshot_path
                        )
                        logger.info(
                            f"[{timestamp}] ✓ 已截图并保存 | "
                            f"记录ID: {activity_id} | "
                            f"应用: {current_app} | "
                            f"标题: {current_title[:50]} | "
                            f"原因: {reason}"
                        )

                        # 立即进行 AI 分析
                        logger.info(f"🤖 开始 AI 分析记录 #{activity_id}...")
                        try:
                            result = analyze_screenshot(activity_id)
                            logger.info(
                                f"✅ AI 分析完成 #{activity_id} | "
                                f"{result.get('category', 'N/A')} | "
                                f"{result.get('description', 'N/A')}"
                            )
                        except Exception as e:
                            logger.error(f"AI 分析失败: {e}")

                    except Exception as e:
                        logger.error(f"保存活动记录失败: {e}")
                else:
                    logger.error(f"[{timestamp}] ✗ 截图失败")
            else:
                # 不截图时，使用 debug 级别（减少输出噪音）
                logger.debug(
                    f"[{timestamp}] - 监控中 | "
                    f"应用: {current_app} | "
                    f"标题: {current_title[:50]}"
                )

        except Exception as e:
            logger.error(f"监控循环出错: {e}", exc_info=True)
            # 出错后继续运行，不中断监控

    def stop(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("监控器未在运行")
            return

        self.is_running = False
        logger.info("=" * 60)
        logger.info("工作监控器已停止")
        logger.info("=" * 60)


if __name__ == "__main__":
    # 测试代码：运行监控器
    print("启动 AIWorkTracker 监控器...")
    print("按 Ctrl+C 停止监控\n")

    monitor = WorkMonitor(test_mode=True)  # 测试模式：10秒间隔
    monitor.start()
