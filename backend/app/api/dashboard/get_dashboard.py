from typing import Literal, Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import DashboardResponse
from repository import DashboardRepository
from service import DashboardService
from .dashboard_router import dashboard_router


# NOTE: plain `def` (not `async def`) on purpose. This handler runs ~10
# synchronous SQLAlchemy queries. An `async def` runs them on the single
# event-loop thread, so a slow query freezes the WHOLE server (every other
# endpoint, including Swagger). As a plain `def`, FastAPI runs it in the
# threadpool, so a slow dashboard can't block unrelated requests.
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
