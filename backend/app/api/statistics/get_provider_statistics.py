from fastapi import Depends, Query
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.provider_service import ProviderService
from domain.schemas.statistics_schemas.provider_schema import ProviderStatisticsResponse


@statistics_router.get("/providers", response_model=ProviderStatisticsResponse)
async def get_provider_statistics(
    range: str = Query("all", pattern="^(all|week|month)$"),
    db: Session = Depends(get_db),
):
    service = ProviderService(db, range)
    return service.get_provider_summary()
