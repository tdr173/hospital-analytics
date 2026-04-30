from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from domain.models.provider_model import ProviderModel
from domain.models.encounter_model import EncounterModel
from repository.statistics_repository._common import (
    compute_min_date, with_percentage,
)


class ProviderRepository:
    def __init__(self, db: Session, range_str: str = "all", provider_id: Optional[str] = None):
        self.db = db
        self._filters = []
        # Providers have no intrinsic date column — range narrows to the set
        # of providers who had encounters within the window.
        min_date = compute_min_date(db, EncounterModel.start_date, range_str)
        if min_date is not None:
            active_ids = (
                db.query(EncounterModel.provider_id)
                .filter(EncounterModel.start_date >= min_date)
                .distinct()
                .subquery()
            )
            self._filters.append(ProviderModel.provider_id.in_(active_ids))
        if provider_id:
            self._filters.append(ProviderModel.provider_id == provider_id)

    def _apply(self, q):
        for f in self._filters:
            q = q.filter(f)
        return q

    def get_total_providers(self) -> int:
        return self._apply(
            self.db.query(func.count(ProviderModel.provider_id))
        ).scalar()

    def get_unique_specialities(self) -> int:
        return self._apply(
            self.db.query(func.count(func.distinct(ProviderModel.speciality)))
        ).scalar()

    def get_gender_distribution(self, total: Optional[int] = None):
        if total is None:
            total = self.get_total_providers()

        rows = self._apply(
            self.db.query(
                ProviderModel.gender.label("label"),
                func.count(ProviderModel.provider_id).label("count"),
            )
        ).group_by(ProviderModel.gender).order_by(
            func.count(ProviderModel.provider_id).desc()
        ).all()
        return with_percentage(rows, total)

    def get_top_specialities(self, limit: int = 15, total: Optional[int] = None):
        if total is None:
            total = self.get_total_providers()

        rows = self._apply(
            self.db.query(
                ProviderModel.speciality.label("label"),
                func.count(ProviderModel.provider_id).label("count"),
            )
        ).group_by(ProviderModel.speciality).order_by(
            func.count(ProviderModel.provider_id).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_top_cities(self, limit: int = 10, total: Optional[int] = None):
        if total is None:
            total = self.get_total_providers()

        rows = self._apply(
            self.db.query(
                ProviderModel.city.label("label"),
                func.count(ProviderModel.provider_id).label("count"),
            )
        ).group_by(ProviderModel.city).order_by(
            func.count(ProviderModel.provider_id).desc()
        ).limit(limit).all()
        return with_percentage(rows, total)

    def get_utilization_stats(self):
        result = self._apply(
            self.db.query(
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
            )
        ).one()

        return {
            "min": result.min or 0,
            "max": result.max or 0,
            "avg": float(result.avg or 0),
            "median": float(result.median or 0),
        }
