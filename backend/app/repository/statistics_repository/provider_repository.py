from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from domain.models.provider_model import ProviderModel
from repository.statistics_repository._common import with_percentage


class ProviderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_providers(self) -> int:
        return self.db.query(func.count(ProviderModel.provider_id)).scalar()

    def get_unique_specialities(self) -> int:
        return self.db.query(func.count(func.distinct(ProviderModel.speciality))).scalar()

    def get_gender_distribution(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_providers()

        rows = (
            self.db.query(
                ProviderModel.gender.label("label"),
                func.count(ProviderModel.provider_id).label("count"),
            )
            .group_by(ProviderModel.gender)
            .order_by(func.count(ProviderModel.provider_id).desc())
            .all()
        )
        return with_percentage(rows, total)

    def get_top_specialities(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_providers()

        rows = (
            self.db.query(
                ProviderModel.speciality.label("label"),
                func.count(ProviderModel.provider_id).label("count"),
            )
            .group_by(ProviderModel.speciality)
            .order_by(func.count(ProviderModel.provider_id).desc())
            .limit(limit)
            .all()
        )
        return with_percentage(rows, total)

    def get_top_cities(self, limit: int = 10, total: Optional[int] = None):
        if total is None:
            total = self.get_total_providers()

        rows = (
            self.db.query(
                ProviderModel.city.label("label"),
                func.count(ProviderModel.provider_id).label("count"),
            )
            .group_by(ProviderModel.city)
            .order_by(func.count(ProviderModel.provider_id).desc())
            .limit(limit)
            .all()
        )
        return with_percentage(rows, total)

    def get_utilization_stats(self):
        result = self.db.query(
            func.min(ProviderModel.encounters).label("min"),
            func.max(ProviderModel.encounters).label("max"),
            func.round(cast(func.avg(ProviderModel.encounters), Numeric), 2).label("avg"),
            func.round(
                cast(
                    func.percentile_cont(0.5).within_group(ProviderModel.encounters),
                    Numeric,
                ),
                2,
            ).label("median"),
        ).one()

        return {
            "min": result.min or 0,
            "max": result.max or 0,
            "avg": float(result.avg or 0),
            "median": float(result.median or 0),
        }
