"""
Cluster feature helper functions.

Each function accepts (db, cluster_id) and runs a focused query against
cluster_patient.features (JSONB).  They are designed to be called
individually from the cluster detail endpoint, or composed together inside
get_ai_analysis.

Private helpers (_cluster_filters, _avg_expr, _flag_pct_expr, _mode_expr)
build the reusable SQLAlchemy expressions so the query logic is defined
exactly once.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, case, Numeric

from domain.models.cluster_patient_model import ClusterPatientModel


# ---------------------------------------------------------------------------
# Private expression builders
# ---------------------------------------------------------------------------

def _cluster_filters(cluster_id: int) -> list:
    """WHERE clause for a given cluster_id (-1 = outlier group)."""
    if cluster_id == -1:
        return [ClusterPatientModel.is_outlier == True]
    return [
        ClusterPatientModel.cluster_label == cluster_id,
        ClusterPatientModel.is_outlier == False,
    ]


def _avg_expr(feature: str, decimals: int = 1):
    """round(avg(features->>feature), decimals)"""
    return func.round(
        func.avg(cast(ClusterPatientModel.features[feature].astext, Numeric)),
        decimals,
    )


def _flag_pct_expr(feature: str, value: str):
    """Percentage of rows where features->>feature = value (0–100)."""
    return func.round(
        100.0 * func.sum(
            case((ClusterPatientModel.features[feature].astext == value, 1), else_=0)
        ) / func.nullif(func.count(), 0),
        1,
    )


def _mode_expr(feature: str):
    """Most frequent value of features->>feature."""
    return func.mode().within_group(
        ClusterPatientModel.features[feature].astext
    )


# ---------------------------------------------------------------------------
# cluster_size  — count + percentage of main population
# ---------------------------------------------------------------------------

def cluster_size(db: Session, cluster_id: int) -> dict:
    """
    Returns {"count": int, "percentage": float}.

    Percentage is relative to the non-outlier population for regular clusters,
    and relative to ALL patients for the outlier cluster (-1).
    """
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


# ---------------------------------------------------------------------------
# Vitals & quality of life
# ---------------------------------------------------------------------------

def get_avg_age(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("age", 1)).filter(*filters).scalar() or 0)


def get_avg_bmi(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("avg_bmi", 1)).filter(*filters).scalar() or 0)


def get_avg_systolic_bp(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("avg_systolic_bp", 1)).filter(*filters).scalar() or 0)


def get_avg_glucose(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("avg_glucose", 1)).filter(*filters).scalar() or 0)


def get_avg_qaly(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("qaly", 2)).filter(*filters).scalar() or 0)


def get_avg_daly(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("daly", 2)).filter(*filters).scalar() or 0)


# ---------------------------------------------------------------------------
# Clinical burden & utilization
# ---------------------------------------------------------------------------

def get_avg_active_conditions(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("active_conditions_count", 1)).filter(*filters).scalar() or 0)


def get_avg_medications(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("total_medications", 1)).filter(*filters).scalar() or 0)


def get_avg_procedures(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("total_procedures", 1)).filter(*filters).scalar() or 0)


def get_avg_days_since_encounter(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("days_since_last_encounter", 0)).filter(*filters).scalar() or 0)


def get_avg_clinical_severity_score(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("clinical_severity_score", 2)).filter(*filters).scalar() or 0)


def get_clinical_severity_components(db: Session, cluster_id: int) -> dict:
    """
    Returns the three raw inputs that feed the PCA-derived clinical_severity_score:
    avg_active_conditions, avg_medications, avg_procedures.
    """
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _avg_expr("active_conditions_count", 1).label("avg_active_conditions"),
        _avg_expr("total_medications", 1).label("avg_medications"),
        _avg_expr("total_procedures", 1).label("avg_procedures"),
    ).filter(*filters).first()

    if not row:
        return {"avg_active_conditions": 0.0, "avg_medications": 0.0, "avg_procedures": 0.0}
    return {
        "avg_active_conditions": float(row.avg_active_conditions or 0),
        "avg_medications": float(row.avg_medications or 0),
        "avg_procedures": float(row.avg_procedures or 0),
    }


def get_avg_routine_care(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("routine_care_count", 1)).filter(*filters).scalar() or 0)


def get_avg_acute_care(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("acute_care_count", 1)).filter(*filters).scalar() or 0)


def get_avg_wellness_care(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("wellness_count", 1)).filter(*filters).scalar() or 0)


def get_avg_severe_care(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("severe_care_count", 1)).filter(*filters).scalar() or 0)


def get_avg_distinct_providers(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_avg_expr("distinct_providers_seen", 1)).filter(*filters).scalar() or 0)


# ---------------------------------------------------------------------------
# Disease prevalence flags  (all return 0–100 %)
# ---------------------------------------------------------------------------

def get_diabetes_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("has_diabetes", "Yes")).filter(*filters).scalar() or 0)


def get_hypertension_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("has_hypertension", "Yes")).filter(*filters).scalar() or 0)


def get_heart_disease_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("has_heart_disease", "Yes")).filter(*filters).scalar() or 0)


def get_cancer_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("has_cancer", "Yes")).filter(*filters).scalar() or 0)


def get_respiratory_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("has_respiratory_disease", "Yes")).filter(*filters).scalar() or 0)


def get_mental_health_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("has_mental_health", "Yes")).filter(*filters).scalar() or 0)


def get_polypharmacy_pct(db: Session, cluster_id: int) -> float:
    filters = _cluster_filters(cluster_id)
    return float(db.query(_flag_pct_expr("is_polypharmacy", "Yes")).filter(*filters).scalar() or 0)


# ---------------------------------------------------------------------------
# Demographics distributions  (grouped queries — one round-trip per group)
# ---------------------------------------------------------------------------

def get_gender_distribution(db: Session, cluster_id: int) -> dict:
    """{"F": float, "M": float} — percentages."""
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("gender", "F").label("female_pct"),
        _flag_pct_expr("gender", "M").label("male_pct"),
    ).filter(*filters).first()
    if not row:
        return {"F": 0.0, "M": 0.0}
    return {"F": float(row.female_pct or 0), "M": float(row.male_pct or 0)}


def get_marital_distribution(db: Session, cluster_id: int) -> dict:
    """{"M": float, "S": float, "D": float, "W": float} — percentages."""
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
        "M": float(row.married or 0),
        "S": float(row.single or 0),
        "D": float(row.divorced or 0),
        "W": float(row.widowed or 0),
    }


def get_smoking_distribution(db: Session, cluster_id: int) -> dict:
    """{"current": float, "former": float, "never": float} — percentages."""
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("smoking_status", "current").label("current"),
        _flag_pct_expr("smoking_status", "former").label("former"),
        _flag_pct_expr("smoking_status", "never").label("never"),
    ).filter(*filters).first()
    if not row:
        return {"current": 0.0, "former": 0.0, "never": 0.0}
    return {
        "current": float(row.current or 0),
        "former": float(row.former or 0),
        "never": float(row.never or 0),
    }


def get_condition_burden_distribution(db: Session, cluster_id: int) -> dict:
    """{"none": float, "low": float, "moderate": float, "high": float, "very_high": float} — percentages."""
    filters = _cluster_filters(cluster_id)
    row = db.query(
        _flag_pct_expr("condition_burden", "none").label("none"),
        _flag_pct_expr("condition_burden", "low").label("low"),
        _flag_pct_expr("condition_burden", "moderate").label("moderate"),
        _flag_pct_expr("condition_burden", "high").label("high"),
        _flag_pct_expr("condition_burden", "very_high").label("very_high"),
    ).filter(*filters).first()
    if not row:
        return {"none": 0.0, "low": 0.0, "moderate": 0.0, "high": 0.0, "very_high": 0.0}
    return {
        "none": float(row.none or 0),
        "low": float(row.low or 0),
        "moderate": float(row.moderate or 0),
        "high": float(row.high or 0),
        "very_high": float(row.very_high or 0),
    }


# ---------------------------------------------------------------------------
# Dominant categorical values
# ---------------------------------------------------------------------------

def get_dominant_careplan(db: Session, cluster_id: int) -> str:
    filters = _cluster_filters(cluster_id)
    return db.query(_mode_expr("dominant_careplan")).filter(*filters).scalar() or "N/A"


def get_dominant_encounter_class(db: Session, cluster_id: int) -> str:
    filters = _cluster_filters(cluster_id)
    return db.query(_mode_expr("dominant_encounter_class")).filter(*filters).scalar() or "N/A"


def get_dominant_marital(db: Session, cluster_id: int) -> str:
    filters = _cluster_filters(cluster_id)
    return db.query(_mode_expr("marital")).filter(*filters).scalar() or "N/A"


# ---------------------------------------------------------------------------
# Population-wide averages  (used as reference values in the AI prompt)
# ---------------------------------------------------------------------------

def get_population_stats(db: Session) -> dict:
    """
    Single query returning population averages and disease rates across all
    non-outlier patients.  Used by get_ai_analysis for the comparison baseline.
    """
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
