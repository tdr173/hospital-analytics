from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.api.statistics.statistics_router import statistics_router
from app.service.statistics_service.allergy_service import AllergyService
from app.domain.schemas.statistics_schema.allergy_schema import AllergyStatisticsResponse


@statistics_router.get("/allergies", response_model=AllergyStatisticsResponse)
async def get_allergy_statistics(db: Session = Depends(get_db)):
    service = AllergyService(db)
    return service.get_allergy_summary()
