"""
数据库集成测试脚本
测试监控器与数据库的完整集成
"""

import time
import threading
from pathlib import Path
from datetime import datetime

from src.database.db import init_db, get_today_activities
from src.monitor.main_monitor import WorkMonitor


def test_monitoring_with_database():
    """测试监控器与数据库集成"""

    print("=" * 70)
    print("AIWorkTracker 数据库集成测试")
    print("=" * 70)

    # 1. 初始化数据库
    print("\n[步骤 1] 初始化数据库...")
    init_db()
    print("✓ 数据库初始化完成")

    # 2. 启动监控器（在单独线程中运行）
    print("\n[步骤 2] 启动监控器（运行 20 秒）...")
    monitor = WorkMonitor()

    # 在后台线程启动监控
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()

    # 等待 20 秒
    for i in range(20, 0, -1):
        print(f"\r监控中... 剩余 {i} 秒", end="", flush=True)
        time.sleep(1)

    print("\n")

    # 3. 停止监控
    print("[步骤 3] 停止监控...")
    monitor.stop()
    time.sleep(1)  # 等待线程结束
    print("✓ 监控已停止")

    # 4. 查询今日活动
    print("\n[步骤 4] 查询今日活动记录...")
    activities = get_today_activities()

    if not activities:
        print("⚠️  未找到任何活动记录")
        print("提示：可能因为 10 分钟截图间隔，20 秒内未触发截图")
        return

    print(f"✓ 找到 {len(activities)} 条记录\n")

    # 打印所有记录
    print("-" * 70)
    for idx, activity in enumerate(activities, 1):
        print(f"\n记录 #{idx} (ID: {activity.id})")
        print(f"  时间: {activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  应用: {activity.app_name}")
        print(f"  窗口标题: {activity.window_title}")
        print(f"  截图路径: {activity.screenshot_path}")
        print(f"  已分析: {activity.analyzed}")
        if activity.category:
            print(f"  分类: {activity.category}")
        if activity.description:
            print(f"  描述: {activity.description}")
    print("-" * 70)

    # 5. 验证数据库文件是否存在
    print("\n[步骤 5] 验证数据库文件...")
    db_path = Path(__file__).parent.parent / "data" / "aiworktracker.db"

    if db_path.exists():
        file_size = db_path.stat().st_size
        print(f"✓ 数据库文件已生成: {db_path}")
        print(f"  文件大小: {file_size:,} 字节")
    else:
        print(f"✗ 数据库文件不存在: {db_path}")

    # 6. 验证截图文件
    print("\n[步骤 6] 验证截图文件...")
    screenshot_dir = Path(__file__).parent.parent / "data" / "screenshots"
    if screenshot_dir.exists():
        screenshots = list(screenshot_dir.glob("*.png"))
        print(f"✓ 截图目录: {screenshot_dir}")
        print(f"  截图数量: {len(screenshots)} 个")
    else:
        print(f"✗ 截图目录不存在: {screenshot_dir}")

    # 测试总结
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_monitoring_with_database()
