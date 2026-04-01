from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from .statistics_router import statistics_router
from service.statistics_service.allergy_service import AllergyService
from domain.schemas.statistics_schemas.allergy_schema import AllergyStatisticsResponse


@statistics_router.get("/allergies", response_model=AllergyStatisticsResponse)
async def get_allergy_statistics(db: Session = Depends(get_db)):
    service = AllergyService(db)
    return service.get_allergy_summary()
