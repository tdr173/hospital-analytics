from sqlalchemy import func, cast, Numeric
from sqlalchemy.orm import Session


def with_percentage(rows, total):
    return [
        {
            "label": row.label,
            "count": row.count,
            "percentage": round(row.count * 100.0 / total, 2) if total else 0,
        }
        for row in rows
    ]


def per_patient_stats(db: Session, model, code_col):
    subquery = (
        db.query(
            model.patient_id,
            func.count(code_col).label("cnt"),
        )
        .group_by(model.patient_id)
        .subquery()
    )

    result = db.query(
        func.round(cast(func.avg(subquery.c.cnt), Numeric), 2).label("avg"),
        func.min(subquery.c.cnt).label("min"),
        func.max(subquery.c.cnt).label("max"),
    ).one()

    return {
        "avg": float(result.avg or 0),
        "min": result.min or 0,
        "max": result.max or 0,
    }
