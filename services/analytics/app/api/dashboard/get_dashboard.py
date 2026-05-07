from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_clinical_db, get_ml_db
from domain import DashboardResponse
from repository import DashboardRepository
from service import DashboardService
from .dashboard_router import dashboard_router


@dashboard_router.get("", response_model=DashboardResponse)
async def get_dashboard(
    clinical_db: Session = Depends(get_clinical_db),
    ml_db: Session = Depends(get_ml_db),
):
    return DashboardService(DashboardRepository(clinical_db, ml_db)).get_dashboard()
