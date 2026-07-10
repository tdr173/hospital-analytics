from typing import Literal, Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import DashboardResponse
from repository import DashboardRepository
from service import DashboardService
from .dashboard_router import dashboard_router


# plain `def` on purpose, not `async def`: this runs ~10 sync SQLAlchemy
# queries, and async would run them on the event loop thread, blocking
# every other request while the dashboard is slow. def gets the threadpool.
@dashboard_router.get("", response_model=DashboardResponse)
def get_dashboard(
    range: Literal["week", "month", "year", "all"] = Query(default="month"),
    providerId: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    provider_id = providerId if role == "DOCTOR" else None
    return DashboardService(DashboardRepository(db)).get_dashboard(
        range_str=range, provider_id=provider_id
    )
