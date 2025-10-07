"""
FastAPI Web API 服务
提供 RESTful API 供前端访问后端数据
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.db import (
    get_activities_by_date,
    get_summary,
    init_db,
    SessionLocal
)
from src.database.models import Activity, DailySummary
from src.ai.summarizer import generate_daily_summary

# 创建 FastAPI 应用
app = FastAPI(
    title="AIWorkTracker API",
    description="AI工作追踪系统API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 响应模型 ============

class ActivityResponse(BaseModel):
    id: int
    timestamp: str
    app_name: str
    window_title: str
    category: Optional[str] = None
    description: Optional[str] = None
    confidence: Optional[int] = None
    analyzed: bool

    class Config:
        from_attributes = True


class SummaryResponse(BaseModel):
    date: str
    summary_text: str
    generated_at: str


class StatsResponse(BaseModel):
    total_records: int
    analyzed_records: int
    work_hours: float
    category_distribution: dict


# ============ API 端点 ============

@app.get("/")
def root():
    """根路径"""
    return {
        "message": "AIWorkTracker API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "message": "AIWorkTracker API is running"
    }


@app.get("/api/activities/today", response_model=List[ActivityResponse])
def get_today_activities():
    """获取今日所有活动"""
    today = datetime.now().date()
    activities = get_activities_by_date(today)

    return [
        ActivityResponse(
            id=a.id,
            timestamp=a.timestamp.isoformat(),
            app_name=a.app_name,
            window_title=a.window_title or "",
            category=a.category,
            description=a.description,
            confidence=a.confidence,
            analyzed=a.analyzed
        )
        for a in activities
    ]


@app.get("/api/activities", response_model=List[ActivityResponse])
def get_activities(date: Optional[str] = None):
    """
    获取指定日期的活动

    参数:
        date: 日期字符串，格式 YYYY-MM-DD，不传则返回今天
    """
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
    else:
        target_date = datetime.now().date()

    activities = get_activities_by_date(target_date)

    return [
        ActivityResponse(
            id=a.id,
            timestamp=a.timestamp.isoformat(),
            app_name=a.app_name,
            window_title=a.window_title or "",
            category=a.category,
            description=a.description,
            confidence=a.confidence,
            analyzed=a.analyzed
        )
        for a in activities
    ]


@app.get("/api/summary/today")
def get_today_summary():
    """获取今日摘要"""
    today = datetime.now().date()
    summary = get_summary(today)

    if not summary:
        return {
            "date": today.isoformat(),
            "summary_text": None,
            "generated_at": None
        }

    return {
        "date": summary.date.isoformat(),
        "summary_text": summary.summary_text,
        "generated_at": summary.generated_at.isoformat()
    }


@app.get("/api/summary/{date}")
def get_summary_by_date(date: str):
    """
    获取指定日期的摘要

    参数:
        date: 日期字符串，格式 YYYY-MM-DD
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="日期格式错误，请使用 YYYY-MM-DD 格式"
        )

    summary = get_summary(target_date)

    if not summary:
        return {
            "date": date,
            "summary_text": None,
            "generated_at": None
        }

    return {
        "date": summary.date.isoformat(),
        "summary_text": summary.summary_text,
        "generated_at": summary.generated_at.isoformat()
    }


@app.post("/api/summary/generate")
def generate_summary_endpoint(date: Optional[str] = None):
    """
    生成摘要

    参数:
        date: 日期字符串，格式 YYYY-MM-DD，不传则生成今天的摘要
    """
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="日期格式错误，请使用 YYYY-MM-DD 格式"
            )
    else:
        target_date = datetime.now().date()

    try:
        summary_text = generate_daily_summary(target_date)
        return {
            "success": True,
            "date": target_date.isoformat(),
            "summary_text": summary_text
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成摘要失败: {str(e)}"
        )


@app.get("/api/stats/today", response_model=StatsResponse)
def get_today_stats():
    """获取今日统计数据"""
    today = datetime.now().date()
    activities = get_activities_by_date(today)
    analyzed = [a for a in activities if a.analyzed]

    # 计算类别分布
    category_dist = {}
    for a in analyzed:
        cat = a.category or 'other'
        category_dist[cat] = category_dist.get(cat, 0) + 1

    return StatsResponse(
        total_records=len(activities),
        analyzed_records=len(analyzed),
        work_hours=round(len(activities) * 10 / 60, 1),
        category_distribution=category_dist
    )


# ============ 启动配置 ============

if __name__ == "__main__":
    import uvicorn

    print("初始化数据库...")
    init_db()

    print("启动 API 服务器...")
    print("API 地址: http://localhost:8000")
    print("API 文档: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
