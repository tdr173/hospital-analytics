from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.provider_service import ProviderService
from app.domain.schemas.statistics_schema.provider_schema import ProviderStatisticsResponse


@statistics_router.get("/providers", response_model=ProviderStatisticsResponse)
async def get_provider_statistics(db: Session = Depends(get_db)):
    service = ProviderService(db)
    return service.get_provider_summary()
