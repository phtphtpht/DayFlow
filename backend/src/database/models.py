"""
数据库模型定义
使用 SQLAlchemy ORM
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    Boolean,
    create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 创建基类
Base = declarative_base()


class Activity(Base):
    """
    活动记录模型
    记录每次截图及其相关信息
    """
    __tablename__ = "activities"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    timestamp = Column(DateTime, nullable=False, index=True, comment="截图时间")
    app_name = Column(String(255), nullable=False, comment="应用名称")
    window_title = Column(String(500), comment="窗口标题")
    screenshot_path = Column(String(500), nullable=False, comment="截图文件路径")

    # AI 分析结果
    category = Column(String(100), nullable=True, comment="工作类型分类")
    description = Column(Text, nullable=True, comment="活动详细描述")
    confidence = Column(Integer, nullable=True, comment="AI分析置信度 0-100")
    analyzed = Column(Boolean, default=False, nullable=False, comment="是否已AI分析")

    def __repr__(self):
        return (
            f"<Activity(id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"app={self.app_name}, "
            f"analyzed={self.analyzed})>"
        )


class DailySummary(Base):
    """
    每日摘要模型
    存储AI生成的每日工作总结
    """
    __tablename__ = "daily_summaries"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 摘要信息
    date = Column(Date, unique=True, nullable=False, index=True, comment="日期")
    summary_text = Column(Text, nullable=False, comment="摘要内容")
    generated_at = Column(DateTime, nullable=False, comment="生成时间")

    def __repr__(self):
        return (
            f"<DailySummary(id={self.id}, "
            f"date={self.date}, "
            f"generated_at={self.generated_at})>"
        )


if __name__ == "__main__":
    # 测试代码：创建示例数据库
    from pathlib import Path

    # 创建临时测试数据库
    test_db_path = Path(__file__).parent.parent.parent.parent / "data" / "test.db"
    test_db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{test_db_path}", echo=True)

    # 创建所有表
    Base.metadata.create_all(engine)

    print(f"\n✓ 数据库表创建成功: {test_db_path}")
    print(f"✓ 表: {list(Base.metadata.tables.keys())}")
