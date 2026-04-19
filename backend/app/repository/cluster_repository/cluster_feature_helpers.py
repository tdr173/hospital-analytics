"""Grouped aggregation queries over cluster_patient.features (JSONB)."""

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, case, Numeric

from domain.models.cluster_patient_model import ClusterPatientModel


def _cluster_filters(cluster_id: int) -> list:
    """Cluster -1 means the outlier group."""
    if cluster_id == -1:
        return [ClusterPatientModel.is_outlier == True]
    return [
        ClusterPatientModel.cluster_label == cluster_id,
        ClusterPatientModel.is_outlier == False,
    ]


def _avg_expr(feature: str, decimals: int = 1):
    return func.round(
        func.avg(cast(ClusterPatientModel.features[feature].astext, Numeric)),
        decimals,
    )


def _flag_pct_expr(feature: str, value: str):
    return func.round(
        100.0 * func.sum(
            case((ClusterPatientModel.features[feature].astext == value, 1), else_=0)
        ) / func.nullif(func.count(), 0),
        1,
    )


def _mode_expr(feature: str):
    return func.mode().within_group(
        ClusterPatientModel.features[feature].astext
    )


def _f(row, attr) -> float:
    return float(getattr(row, attr) or 0)


def cluster_size(db: Session, cluster_id: int) -> dict:
    """Outlier (-1) percentage is vs ALL patients; regular clusters are vs non-outliers."""
    filters = _cluster_filters(cluster_id)
    count = (
        db.query(func.count())
        .select_from(ClusterPatientModel)
        .filter(*filters)
        .scalar() or 0
    )

    if cluster_id == -1:
        total = db.query(func.count()).select_from(ClusterPatientModel).scalar() or 0
    else:
        total = (
            db.query(func.count())
            .select_from(ClusterPatientModel)
            .filter(ClusterPatientModel.is_outlier == False)
            .scalar() or 0
        )

    pct = round(count * 100.0 / total, 2) if total else 0.0
    return {"count": count, "percentage": pct}


def get_vitals(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _avg_expr("age", 1).label("avg_age"),
        _avg_expr("avg_bmi", 1).label("avg_bmi"),
        _avg_expr("avg_systolic_bp", 1).label("avg_systolic_bp"),
        _avg_expr("avg_glucose", 1).label("avg_glucose"),
        _avg_expr("qaly", 2).label("avg_qaly"),
        _avg_expr("daly", 2).label("avg_daly"),
    ).filter(*filters).first()

    keys = ["avg_age", "avg_bmi", "avg_systolic_bp", "avg_glucose", "avg_qaly", "avg_daly"]
    if not row:
        return {k: 0.0 for k in keys}
    return {k: _f(row, k) for k in keys}


def get_utilization(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _avg_expr("active_conditions_count", 1).label("avg_active_conditions"),
        _avg_expr("total_medications", 1).label("avg_medications"),
        _avg_expr("total_procedures", 1).label("avg_procedures"),
        _avg_expr("days_since_last_encounter", 0).label("avg_days_since_encounter"),
        _avg_expr("clinical_severity_score", 2).label("avg_clinical_severity_score"),
        _avg_expr("routine_care_count", 1).label("avg_routine_care"),
        _avg_expr("acute_care_count", 1).label("avg_acute_care"),
        _avg_expr("wellness_count", 1).label("avg_wellness_care"),
        _avg_expr("severe_care_count", 1).label("avg_severe_care"),
        _avg_expr("distinct_providers_seen", 1).label("avg_distinct_providers"),
    ).filter(*filters).first()

    keys = [
        "avg_active_conditions", "avg_medications", "avg_procedures",
        "avg_days_since_encounter", "avg_clinical_severity_score",
        "avg_routine_care", "avg_acute_care", "avg_wellness_care",
        "avg_severe_care", "avg_distinct_providers",
    ]
    if not row:
        return {k: 0.0 for k in keys}
    return {k: _f(row, k) for k in keys}


def get_disease_prevalence(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("has_diabetes", "Yes").label("diabetes_pct"),
        _flag_pct_expr("has_hypertension", "Yes").label("hypertension_pct"),
        _flag_pct_expr("has_heart_disease", "Yes").label("heart_disease_pct"),
        _flag_pct_expr("has_cancer", "Yes").label("cancer_pct"),
        _flag_pct_expr("has_respiratory_disease", "Yes").label("respiratory_pct"),
        _flag_pct_expr("has_mental_health", "Yes").label("mental_health_pct"),
        _flag_pct_expr("is_polypharmacy", "Yes").label("polypharmacy_pct"),
    ).filter(*filters).first()

    keys = [
        "diabetes_pct", "hypertension_pct", "heart_disease_pct", "cancer_pct",
        "respiratory_pct", "mental_health_pct", "polypharmacy_pct",
    ]
    if not row:
        return {k: 0.0 for k in keys}
    return {k: _f(row, k) for k in keys}


def get_dominant_categoricals(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _mode_expr("dominant_careplan").label("dominant_careplan"),
        _mode_expr("dominant_encounter_class").label("dominant_encounter_class"),
        _mode_expr("marital").label("dominant_marital"),
    ).filter(*filters).first()

    keys = ["dominant_careplan", "dominant_encounter_class", "dominant_marital"]
    if not row:
        return {k: "N/A" for k in keys}
    return {k: (getattr(row, k) or "N/A") for k in keys}


def get_gender_distribution(db: Session, cluster_id: int) -> dict:
    """{"F": float, "M": float} percentages."""
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("gender", "F").label("female_pct"),
        _flag_pct_expr("gender", "M").label("male_pct"),
    ).filter(*filters).first()
    if not row:
        return {"F": 0.0, "M": 0.0}
    return {"F": _f(row, "female_pct"), "M": _f(row, "male_pct")}


def get_marital_distribution(db: Session, cluster_id: int) -> dict:
    """{"M": married, "S": single, "D": divorced, "W": widowed} percentages."""
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("marital", "M").label("married"),
        _flag_pct_expr("marital", "S").label("single"),
        _flag_pct_expr("marital", "D").label("divorced"),
        _flag_pct_expr("marital", "W").label("widowed"),
    ).filter(*filters).first()
    if not row:
        return {"M": 0.0, "S": 0.0, "D": 0.0, "W": 0.0}
    return {
        "M": _f(row, "married"),
        "S": _f(row, "single"),
        "D": _f(row, "divorced"),
        "W": _f(row, "widowed"),
    }


def get_smoking_distribution(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("smoking_status", "current").label("current"),
        _flag_pct_expr("smoking_status", "former").label("former"),
        _flag_pct_expr("smoking_status", "never").label("never"),
    ).filter(*filters).first()
    if not row:
        return {"current": 0.0, "former": 0.0, "never": 0.0}
    return {
        "current": _f(row, "current"),
        "former": _f(row, "former"),
        "never": _f(row, "never"),
    }


def get_condition_burden_distribution(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("condition_burden", "low").label("low"),
        _flag_pct_expr("condition_burden", "medium").label("medium"),
        _flag_pct_expr("condition_burden", "high").label("high"),
    ).filter(*filters).first()
    if not row:
        return {"low": 0.0, "medium": 0.0, "high": 0.0}
    return {
        "low": _f(row, "low"),
        "medium": _f(row, "medium"),
        "high": _f(row, "high"),
    }


def get_population_stats(db: Session) -> dict:
    """Averages & disease rates across non-outlier patients - baseline for AI prompts."""
    row = db.query(
        _avg_expr("age", 1).label("avg_age"),
        _avg_expr("avg_bmi", 1).label("avg_bmi"),
        _avg_expr("avg_systolic_bp", 1).label("avg_systolic_bp"),
        _avg_expr("avg_glucose", 1).label("avg_glucose"),
        _avg_expr("qaly", 2).label("avg_qaly"),
        _avg_expr("daly", 2).label("avg_daly"),
        _avg_expr("total_medications", 1).label("avg_meds"),
        _avg_expr("total_procedures", 1).label("avg_procedures"),
        _avg_expr("active_conditions_count", 1).label("avg_conditions"),
        _avg_expr("days_since_last_encounter", 0).label("avg_days_since"),
        _flag_pct_expr("has_diabetes", "Yes").label("diabetes_pct"),
        _flag_pct_expr("has_hypertension", "Yes").label("hypertension_pct"),
        _flag_pct_expr("has_heart_disease", "Yes").label("heart_pct"),
        _flag_pct_expr("has_cancer", "Yes").label("cancer_pct"),
        _flag_pct_expr("is_polypharmacy", "Yes").label("polypharmacy_pct"),
    ).filter(ClusterPatientModel.is_outlier == False).first()

    if not row:
        return {}

    return {
        "pop_avg_age": row.avg_age,
        "pop_avg_bmi": row.avg_bmi,
        "pop_avg_systolic_bp": row.avg_systolic_bp,
        "pop_avg_glucose": row.avg_glucose,
        "pop_avg_qaly": row.avg_qaly,
        "pop_avg_daly": row.avg_daly,
        "pop_avg_meds": row.avg_meds,
        "pop_avg_procedures": row.avg_procedures,
        "pop_avg_conditions": row.avg_conditions,
        "pop_avg_days_since": row.avg_days_since,
        "pop_diabetes_pct": row.diabetes_pct,
        "pop_hypertension_pct": row.hypertension_pct,
        "pop_heart_pct": row.heart_pct,
        "pop_cancer_pct": row.cancer_pct,
        "pop_polypharmacy_pct": row.polypharmacy_pct,
    }
