"""
数据库操作模块
提供数据库初始化和基础 CRUD 操作
"""

import logging
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Activity, DailySummary

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库路径（相对于项目根目录）
DB_DIR = "data"
DB_NAME = "aiworktracker.db"


def get_db_path() -> Path:
    """
    获取数据库文件路径

    Returns:
        Path: 数据库文件的绝对路径
    """
    # 获取项目根目录（backend/src/database -> 向上3级）
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    db_path = project_root / DB_DIR / DB_NAME
    return db_path


# 创建数据库引擎
db_path = get_db_path()
engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},  # SQLite 多线程配置
    echo=False  # 设为 True 可查看 SQL 语句
)

# 创建 Session 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    初始化数据库
    创建数据库文件和所有表
    """
    try:
        # 确保数据目录存在
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        logger.info(f"数据库初始化成功: {db_path}")
        logger.info(f"已创建表: {list(Base.metadata.tables.keys())}")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def save_activity(
    app_name: str,
    window_title: str,
    screenshot_path: str
) -> int:
    """
    保存一条活动记录

    Args:
        app_name: 应用名称
        window_title: 窗口标题
        screenshot_path: 截图文件路径

    Returns:
        int: 新创建记录的 ID

    Raises:
        Exception: 数据库操作失败时抛出异常
    """
    session = SessionLocal()
    try:
        # 创建活动记录
        activity = Activity(
            timestamp=datetime.now(),
            app_name=app_name,
            window_title=window_title,
            screenshot_path=screenshot_path,
            analyzed=False
        )

        # 保存到数据库
        session.add(activity)
        session.commit()
        session.refresh(activity)

        logger.info(f"活动记录已保存: ID={activity.id}, App={app_name}")
        return activity.id

    except Exception as e:
        session.rollback()
        logger.error(f"保存活动记录失败: {e}")
        raise

    finally:
        session.close()


def get_today_activities() -> List[Activity]:
    """
    获取今日所有活动记录

    Returns:
        List[Activity]: 今日活动列表（按时间升序）
    """
    session = SessionLocal()
    try:
        today = date.today()

        # 查询今天的所有记录
        activities = session.query(Activity).filter(
            Activity.timestamp >= datetime(today.year, today.month, today.day)
        ).order_by(Activity.timestamp.asc()).all()

        logger.info(f"获取今日活动: {len(activities)} 条")
        return activities

    except Exception as e:
        logger.error(f"获取今日活动失败: {e}")
        return []

    finally:
        session.close()


def get_activities_by_date(target_date: date) -> List[Activity]:
    """
    获取指定日期的所有活动

    Args:
        target_date: 目标日期（datetime.date 对象）

    Returns:
        List[Activity]: 该日期的活动列表（按时间升序）
    """
    session = SessionLocal()
    try:
        # 计算日期范围
        start_time = datetime(target_date.year, target_date.month, target_date.day)
        end_time = datetime(
            target_date.year,
            target_date.month,
            target_date.day,
            23, 59, 59
        )

        # 查询指定日期的所有记录
        activities = session.query(Activity).filter(
            Activity.timestamp >= start_time,
            Activity.timestamp <= end_time
        ).order_by(Activity.timestamp.asc()).all()

        logger.info(f"获取 {target_date} 的活动: {len(activities)} 条")
        return activities

    except Exception as e:
        logger.error(f"获取活动失败: {e}")
        return []

    finally:
        session.close()


def save_summary(target_date: date, summary_text: str):
    """
    保存或更新每日摘要

    Args:
        target_date: 日期
        summary_text: 摘要内容

    Raises:
        Exception: 数据库操作失败时抛出异常
    """
    session = SessionLocal()
    try:
        # 查询是否已存在该日期的摘要
        existing_summary = session.query(DailySummary).filter(
            DailySummary.date == target_date
        ).first()

        if existing_summary:
            # 更新已有摘要
            existing_summary.summary_text = summary_text
            existing_summary.generated_at = datetime.now()
            logger.info(f"更新每日摘要: {target_date}")
        else:
            # 创建新摘要
            new_summary = DailySummary(
                date=target_date,
                summary_text=summary_text,
                generated_at=datetime.now()
            )
            session.add(new_summary)
            logger.info(f"创建每日摘要: {target_date}")

        session.commit()

    except Exception as e:
        session.rollback()
        logger.error(f"保存摘要失败: {e}")
        raise

    finally:
        session.close()


def get_summary(target_date: date) -> Optional[DailySummary]:
    """
    获取指定日期的摘要

    Args:
        target_date: 目标日期

    Returns:
        Optional[DailySummary]: 摘要对象，不存在则返回 None
    """
    session = SessionLocal()
    try:
        summary = session.query(DailySummary).filter(
            DailySummary.date == target_date
        ).first()

        if summary:
            logger.info(f"获取摘要成功: {target_date}")
        else:
            logger.info(f"未找到摘要: {target_date}")

        return summary

    except Exception as e:
        logger.error(f"获取摘要失败: {e}")
        return None

    finally:
        session.close()


def get_recent_context(current_activity_id: int, count: int = 5) -> str:
    """
    获取最近几次的分析结果作为上下文
    如果任意两条记录间隔超过24小时，则截断，丢弃更早的记录

    Args:
        current_activity_id: 当前活动记录的 ID
        count: 获取最近的记录数量，默认 5 条

    Returns:
        str: 格式化的上下文文本
    """
    from datetime import timedelta

    session = SessionLocal()
    try:
        # 查询当前记录之前的最近 N 条已分析记录
        # 先获取当前记录的时间戳
        current_activity = session.query(Activity).filter(
            Activity.id == current_activity_id
        ).first()

        if not current_activity:
            return ""

        # 按时间戳查询（比当前记录早的）
        recent_activities = session.query(Activity).filter(
            Activity.timestamp < current_activity.timestamp,
            Activity.analyzed == True
        ).order_by(Activity.timestamp.desc()).limit(count).all()

        # 过滤掉间隔超过24小时的记录
        filtered_activities = []
        prev_timestamp = current_activity.timestamp

        for activity in recent_activities:
            time_diff = prev_timestamp - activity.timestamp

            # 如果间隔超过24小时，截断，后面的都不要了
            if time_diff > timedelta(hours=24):
                logger.debug(f"检测到24小时间隔，截断上下文（{prev_timestamp} -> {activity.timestamp}）")
                break

            filtered_activities.append(activity)
            prev_timestamp = activity.timestamp

        # 格式化为上下文文本（从旧到新排列）
        context_text = ""
        for activity in reversed(filtered_activities):
            time_str = activity.timestamp.strftime('%H:%M')
            context_text += f"- {time_str}: {activity.description}\n"

        if context_text:
            logger.debug(f"获取上下文: {len(recent_activities)} 条记录")
        else:
            logger.debug("未找到历史上下文")

        return context_text

    except Exception as e:
        logger.error(f"获取上下文失败: {e}")
        return ""

    finally:
        session.close()


def get_unanalyzed_activities(limit: int = 5) -> List[Activity]:
    """
    获取未分析的活动记录

    Args:
        limit: 最多返回的记录数量，默认 5 条

    Returns:
        List[Activity]: 未分析的活动列表（按 ID 升序）
    """
    session = SessionLocal()
    try:
        activities = session.query(Activity).filter(
            Activity.analyzed == False
        ).order_by(Activity.id.asc()).limit(limit).all()

        logger.debug(f"获取未分析活动: {len(activities)} 条")
        return activities

    except Exception as e:
        logger.error(f"获取未分析活动失败: {e}")
        return []

    finally:
        session.close()


if __name__ == "__main__":
    # 测试代码
    print("测试数据库操作...")

    # 1. 初始化数据库
    print("\n1. 初始化数据库")
    init_db()

    # 2. 保存活动记录
    print("\n2. 保存测试活动")
    activity_id = save_activity(
        app_name="Chrome",
        window_title="GitHub - AIWorkTracker",
        screenshot_path="/path/to/screenshot.png"
    )
    print(f"✓ 活动已保存，ID: {activity_id}")

    # 3. 获取今日活动
    print("\n3. 获取今日活动")
    today_activities = get_today_activities()
    print(f"✓ 找到 {len(today_activities)} 条活动")

    # 4. 保存摘要
    print("\n4. 保存每日摘要")
    save_summary(
        target_date=date.today(),
        summary_text="今天主要进行了 AIWorkTracker 项目开发。"
    )
    print("✓ 摘要已保存")

    # 5. 获取摘要
    print("\n5. 获取今日摘要")
    summary = get_summary(date.today())
    if summary:
        print(f"✓ 摘要内容: {summary.summary_text[:50]}...")
    else:
        print("✗ 未找到摘要")

    print("\n✓ 所有测试完成")
