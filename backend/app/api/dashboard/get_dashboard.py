from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from api._scope import Scope, scope_dep
from domain import DashboardResponse
from repository import DashboardRepository
from service import DashboardService
from .dashboard_router import dashboard_router


@dashboard_router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    scope: Scope = Depends(scope_dep),
):
    return DashboardService(DashboardRepository(db)).get_dashboard(scope)
