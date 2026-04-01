from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from db.db_connector import get_db
from domain import PatientListResponse
from repository import PatientRepository
from service import PatientService
from .patient_router import patient_router


@patient_router.get("", response_model=PatientListResponse)
async def get_patients(
    search: Optional[str] = None,
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    status: Optional[str] = None,
    race: Optional[str] = None,
    marital: Optional[str] = None,
    city: Optional[str] = None,
    page: int = 1,
    rows: int = 25,
    sort_by: str = "last_name",
    sort_type: str = "asc",
    db: Session = Depends(get_db),
):
    service = PatientService(PatientRepository(db))
    return service.get_patients(
        search=search,
        gender=gender,
        age_group=age_group,
        status=status,
        race=race,
        marital=marital,
        city=city,
        page=page,
        rows=rows,
        sort_by=sort_by,
        sort_type=sort_type,
    )
