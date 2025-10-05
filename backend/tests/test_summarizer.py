"""
测试摘要生成功能
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

# 切换到 backend 目录（确保数据库路径正确）
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(backend_dir)

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, backend_dir)

from src.ai.summarizer import generate_daily_summary
from src.database.db import get_activities_by_date, get_summary

def test_generate_summary():
    """测试生成今日摘要"""
    print("=" * 60)
    print("测试摘要生成功能")
    print("=" * 60)

    # 使用今天的日期
    today = date.today()
    print(f"\n📅 目标日期: {today.strftime('%Y年%m月%d日')}\n")

    # 检查是否有活动记录
    activities = get_activities_by_date(today)
    analyzed_count = len([a for a in activities if a.analyzed])

    print(f"📊 数据统计:")
    print(f"  - 总活动记录: {len(activities)} 条")
    print(f"  - 已分析记录: {analyzed_count} 条")

    if analyzed_count == 0:
        print("\n⚠️  警告: 今天没有已分析的活动记录")
        print("提示: 请先运行监控程序并等待 AI 分析完成")
        return

    print(f"\n🚀 开始生成摘要...\n")

    # 生成摘要
    summary = generate_daily_summary(today)

    print("\n" + "=" * 60)
    print("📝 生成的摘要:")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    # 验证是否保存到数据库
    saved_summary = get_summary(today)
    if saved_summary:
        print(f"\n✅ 摘要已保存到数据库")
        print(f"   创建时间: {saved_summary.generated_at}")
    else:
        print(f"\n❌ 摘要未保存到数据库")

if __name__ == "__main__":
    test_generate_summary()
