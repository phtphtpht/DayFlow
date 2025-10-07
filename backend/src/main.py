"""
AIWorkTracker 主启动脚本
同时启动监控服务和 API 服务
"""

import threading
import uvicorn
import signal
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from src.monitor.main_monitor import WorkMonitor
from src.api.server import app
from src.database.db import init_db

# 全局变量
monitor = None

def signal_handler(sig, frame):
    """处理 Ctrl+C 信号"""
    print("\n" + "="*60)
    print("⏹️  正在停止服务...")
    print("="*60)

    if monitor:
        monitor.stop()

    print("\n✅ 服务已停止")
    sys.exit(0)

def start_monitor():
    """在新线程中启动监控"""
    global monitor
    monitor = WorkMonitor()
    monitor.start()

def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 AIWorkTracker 启动中...")
    print("="*60)

    # 检查环境变量
    if not os.getenv('OPENAI_API_KEY'):
        print("\n❌ 错误: 未找到 OPENAI_API_KEY")
        print("请在 backend/.env 文件中配置:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)

    # 初始化数据库
    print("\n📦 初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成")

    # 启动监控（在新线程中）
    print("\n👀 启动工作监控...")
    monitor_thread = threading.Thread(
        target=start_monitor,
        daemon=True,
        name="Monitor-Thread"
    )
    monitor_thread.start()
    print("✅ 监控已启动")

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)

    # 启动 API 服务器（主线程）
    print("\n🌐 启动 API 服务器...")
    print("   📍 API 地址: http://localhost:8000")
    print("   📖 API 文档: http://localhost:8000/docs")
    print("\n💡 按 Ctrl+C 停止服务")
    print("="*60 + "\n")

    # 启动 FastAPI
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="warning"  # 降低日志级别，减少输出
    )

if __name__ == "__main__":
    main()
