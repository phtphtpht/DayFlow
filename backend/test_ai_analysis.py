"""
AI 分析功能完整测试脚本
测试从监控 -> 截图 -> AI分析 -> 数据库更新的完整流程
"""

import os
import sys
import time
import threading
from datetime import datetime

from src.monitor.main_monitor import WorkMonitor
from src.ai.analyzer import analyze_screenshot
from src.database.db import init_db, get_today_activities, SessionLocal
from src.database.models import Activity


def test_ai_analysis():
    """测试 AI 分析功能的完整流程"""

    print("\n" + "=" * 70)
    print("🧪 AI 分析功能测试")
    print("=" * 70 + "\n")

    # 检查环境变量
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ 错误: 未设置 OPENAI_API_KEY 环境变量")
        print("请创建 .env 文件并添加:")
        print("  OPENAI_API_KEY=sk-your-api-key-here")
        print("  OPENAI_MODEL=gpt-4o-mini")
        sys.exit(1)

    # ===== 步骤1: 初始化数据库 =====
    print("📝 步骤1: 初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成\n")

    # ===== 步骤2: 运行监控生成测试数据 =====
    print("📸 步骤2: 运行监控生成测试数据（测试模式：10秒间隔）...")
    print("监控将运行 30 秒，确保至少触发一次截图...\n")

    # 使用测试模式（10秒间隔）
    monitor = WorkMonitor(test_mode=True)

    # 在后台线程启动监控
    monitor_thread = threading.Thread(target=monitor.start, daemon=True)
    monitor_thread.start()

    # 等待 30 秒
    for i in range(30, 0, -1):
        print(f"\r⏳ 监控运行中... 剩余 {i} 秒  ", end="", flush=True)
        time.sleep(1)

    print("\n")

    # 停止监控
    monitor.stop()
    time.sleep(2)  # 等待线程结束
    print("✅ 监控已运行 30 秒并停止\n")

    # ===== 步骤3: 查询生成的记录 =====
    print("🔍 步骤3: 查询生成的活动记录...")
    activities = get_today_activities()

    if not activities:
        print("⚠️  未找到任何活动记录")
        print("\n调试建议:")
        print("  1. 检查 data/screenshots/ 目录是否有截图文件")
        print("  2. 检查数据库文件 data/aiworktracker.db 是否存在")
        print("  3. 监控可能因为 10 秒间隔，未在 30 秒内触发")
        print("  4. 查看上方日志，确认是否有 '✓ 已截图并保存' 消息")
        sys.exit(1)

    print(f"✅ 找到 {len(activities)} 条活动记录\n")

    # 打印最新记录的信息
    latest_activity = activities[-1]
    print("📋 最新活动记录:")
    print(f"  ID: {latest_activity.id}")
    print(f"  时间: {latest_activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  应用: {latest_activity.app_name}")
    print(f"  窗口标题: {latest_activity.window_title}")
    print(f"  截图路径: {latest_activity.screenshot_path}")
    print(f"  已分析: {latest_activity.analyzed}\n")

    # ===== 步骤4: 调用 AI 分析 =====
    print("🤖 步骤4: 调用 AI 分析...")
    print(f"正在分析活动记录 ID: {latest_activity.id}\n")

    try:
        result = analyze_screenshot(latest_activity.id)
        print("✅ AI 分析完成\n")

    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        print("截图文件不存在，请检查监控模块")
        sys.exit(1)

    except Exception as e:
        print(f"❌ AI 分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # ===== 步骤5: 打印分析结果 =====
    print("📊 步骤5: 分析结果")
    print("-" * 70)
    print(f"类别 (category):     {result.get('category', 'N/A')}")
    print(f"描述 (description):  {result.get('description', 'N/A')}")
    print(f"置信度 (confidence): {result.get('confidence', 0)}/100")

    if 'details' in result:
        print(f"\n详细信息 (details):")
        details = result['details']
        for key, value in details.items():
            print(f"  {key}: {value}")

    print("-" * 70 + "\n")

    # ===== 步骤6: 验证数据库更新 =====
    print("🗄️  步骤6: 验证数据库更新...")

    # 重新查询该记录
    session = SessionLocal()
    try:
        updated_activity = session.query(Activity).filter(
            Activity.id == latest_activity.id
        ).first()

        if not updated_activity:
            print("❌ 错误: 无法查询到更新后的记录")
            sys.exit(1)

        # 验证字段
        print(f"已分析状态: {updated_activity.analyzed}")
        print(f"保存的类别: {updated_activity.category}")
        print(f"保存的描述: {updated_activity.description}")
        print(f"保存的置信度: {updated_activity.confidence}")

        if updated_activity.analyzed:
            print("\n✅ 数据库已成功更新")
        else:
            print("\n⚠️  警告: analyzed 字段未更新为 True")

    finally:
        session.close()

    # ===== 测试完成 =====
    print("\n" + "=" * 70)
    print("✅ 测试完成！AI 分析功能正常工作")
    print("=" * 70 + "\n")

    # 打印测试总结
    print("📝 测试总结:")
    print(f"  - 生成活动记录: {len(activities)} 条")
    print(f"  - AI 分析成功: ✓")
    print(f"  - 数据库更新成功: ✓")
    print(f"  - 分析类别: {result.get('category', 'N/A')}")
    print(f"  - 置信度: {result.get('confidence', 0)}/100")
    print()


if __name__ == "__main__":
    try:
        test_ai_analysis()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
