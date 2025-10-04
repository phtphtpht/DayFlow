"""
智能采样模块
负责决定何时需要截图
"""

import logging
import time
from typing import Tuple

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartSampler:
    """
    智能采样器
    固定时间间隔截图（10分钟一次）
    """

    def __init__(self, test_mode: bool = False):
        """
        初始化采样器

        Args:
            test_mode: 测试模式，设为 True 时间隔为 10 秒
        """
        self.last_capture_time = 0
        if test_mode:
            self.capture_interval = 10  # 测试模式：10秒
            logger.info("采样器已启动（测试模式：10秒间隔）")
        else:
            self.capture_interval = 600  # 正常模式：10分钟 = 600秒
            logger.info("采样器已启动（正常模式：10分钟间隔）")

    def should_capture(self, current_app: str, current_title: str) -> Tuple[bool, str]:
        """
        判断是否需要截图

        规则：距离上次截图超过10分钟就截图

        Args:
            current_app: 当前应用名称（保留参数以保持接口兼容）
            current_title: 当前窗口标题（保留参数以保持接口兼容）

        Returns:
            Tuple[bool, str]: (是否截图, 原因说明)
        """
        now = time.time()

        if now - self.last_capture_time >= self.capture_interval:
            self.last_capture_time = now
            return True, "定时截图（10分钟间隔）"

        remaining = int(self.capture_interval - (now - self.last_capture_time))
        return False, f"距离上次截图还有 {remaining} 秒"

    def reset(self):
        """重置计时器"""
        self.last_capture_time = 0
        logger.info("采样器状态已重置")


if __name__ == "__main__":
    # 测试代码
    print("测试智能采样器（10分钟定时截图）...")

    sampler = SmartSampler()

    # 测试场景1: 首次运行（立即截图）
    should, reason = sampler.should_capture("Chrome", "Google")
    print(f"场景1 - 首次运行: {should}, 原因: {reason}")
    assert should is True, "首次运行应该截图"

    # 测试场景2: 1秒后（不截图）
    time.sleep(1)
    should, reason = sampler.should_capture("Chrome", "GitHub")
    print(f"场景2 - 1秒后: {should}, 原因: {reason}")
    assert should is False, "未超过10分钟不应该截图"

    # 测试场景3: 模拟10分钟后（应该截图）
    sampler.last_capture_time = time.time() - 601  # 601秒前
    should, reason = sampler.should_capture("VSCode", "main.py")
    print(f"场景3 - 10分钟后: {should}, 原因: {reason}")
    assert should is True, "超过10分钟应该截图"

    print("\n✓ 所有测试通过")
