from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Numeric

from app.domain.models.organization_model import OrganizationModel


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_total_organizations(self) -> int:
        return self.db.query(func.count(OrganizationModel.organization_id)).scalar()

    def get_top_cities(self, limit: int = 10):
        total = self.get_total_organizations()

        rows = (
            self.db.query(
                OrganizationModel.city.label("label"),
                func.count(OrganizationModel.organization_id).label("count"),
            )
            .group_by(OrganizationModel.city)
            .order_by(func.count(OrganizationModel.organization_id).desc())
            .limit(limit)
            .all()
        )
        return self._with_percentage(rows, total)

    def get_utilization_stats(self):
        result = self.db.query(
            func.min(OrganizationModel.utilization).label("min"),
            func.max(OrganizationModel.utilization).label("max"),
            func.round(cast(func.avg(OrganizationModel.utilization), Numeric), 2).label("avg"),
            func.round(
                cast(
                    func.percentile_cont(0.5).within_group(OrganizationModel.utilization),
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

    @staticmethod
    def _with_percentage(rows, total):
        return [
            {
                "label": row.label,
                "count": row.count,
                "percentage": round(row.count * 100.0 / total, 2) if total else 0,
            }
            for row in rows
        ]
