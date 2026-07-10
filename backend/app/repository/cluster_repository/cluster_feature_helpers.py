"""Cluster detail queries - joins cluster_patient with source tables.

JSONB is only used for features guaranteed to be in every run:
  gender, condition_burden, dominant_careplan.
Everything else queries the original patient/observation/condition/etc. tables.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, case
from sqlalchemy import text

from domain.models.cluster_patient_model import ClusterPatientModel


def _cluster_filters(cluster_id: int) -> list:
    if cluster_id == -1:
        return [ClusterPatientModel.is_outlier == True]
    return [
        ClusterPatientModel.cluster_label == cluster_id,
        ClusterPatientModel.is_outlier == False,
    ]


def _flag_pct_expr(feature: str, value: str):
    return func.round(
        100.0 * func.sum(
            case((ClusterPatientModel.features[feature].astext == value, 1), else_=0)
        ) / func.nullif(func.count(), 0),
        1,
    )


def _mode_expr(feature: str):
    return func.mode().within_group(ClusterPatientModel.features[feature].astext)


def _f(row, attr) -> float:
    return float(getattr(row, attr) or 0)


def _where(cluster_id: int) -> str:
    if cluster_id == -1:
        return "cp.is_outlier = true"
    return "cp.cluster_label = :cluster_id AND cp.is_outlier = false"


def _params(cluster_id: int) -> dict:
    return {} if cluster_id == -1 else {"cluster_id": cluster_id}


def _row_float(row, key: str) -> float:
    return float(row[key] or 0) if row else 0.0


def cluster_size(db: Session, cluster_id: int) -> dict:
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
    return {"count": count, "percentage": round(count * 100.0 / total, 2) if total else 0.0}


def get_vitals(db: Session, cluster_id: int) -> dict:
    sql = text(f"""
        SELECT
            ROUND(AVG(p.age)::numeric, 1)       AS avg_age,
            ROUND(AVG(bmi.v)::numeric, 1)        AS avg_bmi,
            ROUND(AVG(bp.v)::numeric, 1)         AS avg_systolic_bp,
            ROUND(AVG(glu.v)::numeric, 1)        AS avg_glucose,
            ROUND(AVG(qaly.v)::numeric, 2)       AS avg_qaly,
            ROUND(AVG(daly.v)::numeric, 2)       AS avg_daly
        FROM cluster_patient cp
        JOIN patient p ON p.patient_id = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE (description ILIKE '%bmi%' OR description ILIKE '%body mass index%')
              AND value_numeric IS NOT NULL AND value_numeric BETWEEN 10 AND 100
            GROUP BY patient_id
        ) bmi  ON bmi.patient_id  = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%systolic%' AND description ILIKE '%blood pressure%'
              AND value_numeric IS NOT NULL AND value_numeric > 0
            GROUP BY patient_id
        ) bp   ON bp.patient_id   = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%glucose%' AND description NOT ILIKE '%urine%'
              AND value_numeric IS NOT NULL AND value_numeric BETWEEN 1 AND 1000
            GROUP BY patient_id
        ) glu  ON glu.patient_id  = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%qaly%' AND value_numeric IS NOT NULL
            GROUP BY patient_id
        ) qaly ON qaly.patient_id = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%daly%' AND value_numeric IS NOT NULL
            GROUP BY patient_id
        ) daly ON daly.patient_id = cp.patient_id
        WHERE {_where(cluster_id)}
    """)
    row = db.execute(sql, _params(cluster_id)).mappings().first()
    keys = ["avg_age", "avg_bmi", "avg_systolic_bp", "avg_glucose", "avg_qaly", "avg_daly"]
    return {k: _row_float(row, k) for k in keys}


def get_utilization(db: Session, cluster_id: int) -> dict:
    sql = text(f"""
        SELECT
            ROUND(AVG(COALESCE(cond.active_count,   0))::numeric, 1) AS avg_active_conditions,
            ROUND(AVG(COALESCE(med.med_count,        0))::numeric, 1) AS avg_medications,
            ROUND(AVG(COALESCE(proc.proc_count,      0))::numeric, 1) AS avg_procedures,
            ROUND(AVG(COALESCE(enc.days_since,       0))::numeric, 0) AS avg_days_since_encounter,
            ROUND(AVG(COALESCE(enc.routine_care,     0))::numeric, 1) AS avg_routine_care,
            ROUND(AVG(COALESCE(enc.acute_care,       0))::numeric, 1) AS avg_acute_care,
            ROUND(AVG(COALESCE(enc.wellness_care,    0))::numeric, 1) AS avg_wellness_care,
            ROUND(AVG(COALESCE(enc.severe_care,      0))::numeric, 1) AS avg_severe_care,
            ROUND(AVG(COALESCE(enc.distinct_providers,0))::numeric, 1) AS avg_distinct_providers
        FROM cluster_patient cp
        LEFT JOIN (
            SELECT patient_id,
                   COUNT(*) FILTER (WHERE end_date IS NULL) AS active_count
            FROM condition GROUP BY patient_id
        ) cond ON cond.patient_id = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, COUNT(*) AS med_count FROM medication GROUP BY patient_id
        ) med ON med.patient_id = cp.patient_id
        LEFT JOIN (
            SELECT patient_id, COUNT(*) AS proc_count FROM "procedure" GROUP BY patient_id
        ) proc ON proc.patient_id = cp.patient_id
        LEFT JOIN (
            SELECT patient_id,
                   EXTRACT(DAY FROM (CURRENT_DATE - MAX(end_date)))::int AS days_since,
                   COUNT(*) FILTER (WHERE encounter_class IN ('ambulatory','outpatient')) AS routine_care,
                   COUNT(*) FILTER (WHERE encounter_class IN ('emergency','urgentcare'))  AS acute_care,
                   COUNT(*) FILTER (WHERE encounter_class = 'wellness')                   AS wellness_care,
                   COUNT(*) FILTER (WHERE encounter_class IN ('inpatient','snf','hospice')) AS severe_care,
                   COUNT(DISTINCT provider_id) FILTER (WHERE provider_id IS NOT NULL)     AS distinct_providers
            FROM encounter
            WHERE end_date IS NOT NULL
            GROUP BY patient_id
        ) enc ON enc.patient_id = cp.patient_id
        WHERE {_where(cluster_id)}
    """)
    keys = [
        "avg_active_conditions", "avg_medications", "avg_procedures",
        "avg_days_since_encounter", "avg_routine_care", "avg_acute_care",
        "avg_wellness_care", "avg_severe_care", "avg_distinct_providers",
    ]
    row = db.execute(sql, _params(cluster_id)).mappings().first()
    return {**{k: _row_float(row, k) for k in keys}, "avg_clinical_severity_score": None}


def get_disease_prevalence(db: Session, cluster_id: int) -> dict:
    sql = text(f"""
        SELECT
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_diabetes      THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS diabetes_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_hypertension  THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS hypertension_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_heart         THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS heart_disease_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_cancer        THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS cancer_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_respiratory   THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS respiratory_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_mental_health THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS mental_health_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN m.poly              THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1) AS polypharmacy_pct
        FROM cluster_patient cp
        LEFT JOIN (
            SELECT patient_id,
                MAX(CASE WHEN LOWER(description) LIKE '%diabetes%'
                          AND LOWER(description) NOT LIKE '%prediabetes%' THEN 1 ELSE 0 END) = 1 AS has_diabetes,
                MAX(CASE WHEN LOWER(description) LIKE '%hypertension%'
                          AND LOWER(description) NOT LIKE '%prehypertension%' THEN 1 ELSE 0 END) = 1 AS has_hypertension,
                MAX(CASE WHEN LOWER(description) LIKE '%heart failure%'
                          OR LOWER(description) LIKE '%coronary%'
                          OR LOWER(description) LIKE '%myocardial%'
                          OR LOWER(description) LIKE '%atrial fibrillation%' THEN 1 ELSE 0 END) = 1 AS has_heart,
                MAX(CASE WHEN LOWER(description) LIKE '%cancer%'
                          OR LOWER(description) LIKE '%carcinoma%'
                          OR LOWER(description) LIKE '%leukemia%'
                          OR LOWER(description) LIKE '%lymphoma%'
                          OR LOWER(description) LIKE '%malignant%' THEN 1 ELSE 0 END) = 1 AS has_cancer,
                MAX(CASE WHEN LOWER(description) LIKE '%copd%'
                          OR LOWER(description) LIKE '%asthma%'
                          OR LOWER(description) LIKE '%pneumonia%'
                          OR LOWER(description) LIKE '%bronchitis%' THEN 1 ELSE 0 END) = 1 AS has_respiratory,
                MAX(CASE WHEN LOWER(description) LIKE '%depress%'
                          OR LOWER(description) LIKE '%anxiety%'
                          OR LOWER(description) LIKE '%bipolar%'
                          OR LOWER(description) LIKE '%schizophrenia%'
                          OR LOWER(description) LIKE '%ptsd%' THEN 1 ELSE 0 END) = 1 AS has_mental_health
            FROM condition GROUP BY patient_id
        ) d ON d.patient_id = cp.patient_id
        LEFT JOIN (
            SELECT patient_id,
                   COUNT(*) FILTER (WHERE end_date IS NULL) >= 5 AS poly
            FROM medication GROUP BY patient_id
        ) m ON m.patient_id = cp.patient_id
        WHERE {_where(cluster_id)}
    """)
    keys = ["diabetes_pct", "hypertension_pct", "heart_disease_pct", "cancer_pct",
            "respiratory_pct", "mental_health_pct", "polypharmacy_pct"]
    row = db.execute(sql, _params(cluster_id)).mappings().first()
    return {k: _row_float(row, k) for k in keys}


# dominant_careplan comes from cached JSONB; the other two need a join since
# they aren't part of the per-patient feature snapshot.
def get_dominant_categoricals(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    careplan_row = (
        db.query(_mode_expr("dominant_careplan").label("dominant_careplan"))
        .select_from(ClusterPatientModel)
        .filter(*filters)
        .first()
    )
    dominant_careplan = (careplan_row.dominant_careplan if careplan_row else None) or "N/A"

    enc_sql = text(f"""
        SELECT MODE() WITHIN GROUP (ORDER BY e.encounter_class) AS dominant_encounter_class
        FROM cluster_patient cp
        JOIN encounter e ON e.patient_id = cp.patient_id
        WHERE {_where(cluster_id)}
    """)
    enc_row = db.execute(enc_sql, _params(cluster_id)).mappings().first()
    dominant_encounter_class = (enc_row["dominant_encounter_class"] if enc_row else None) or "N/A"

    marital_sql = text(f"""
        SELECT MODE() WITHIN GROUP (ORDER BY p.marital) AS dominant_marital
        FROM cluster_patient cp
        JOIN patient p ON p.patient_id = cp.patient_id
        WHERE {_where(cluster_id)}
    """)
    marital_row = db.execute(marital_sql, _params(cluster_id)).mappings().first()
    dominant_marital = (marital_row["dominant_marital"] if marital_row else None) or "N/A"

    return {
        "dominant_careplan": dominant_careplan,
        "dominant_encounter_class": dominant_encounter_class,
        "dominant_marital": dominant_marital,
    }


def get_gender_distribution(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = (
        db.query(
            _flag_pct_expr("gender", "F").label("female_pct"),
            _flag_pct_expr("gender", "M").label("male_pct"),
        )
        .select_from(ClusterPatientModel)
        .filter(*filters)
        .first()
    )
    if not row:
        return {"F": 0.0, "M": 0.0}
    return {"F": _f(row, "female_pct"), "M": _f(row, "male_pct")}


def get_marital_distribution(db: Session, cluster_id: int) -> dict:
    sql = text(f"""
        SELECT
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.marital = 'M')
                / NULLIF(COUNT(*), 0), 1) AS married,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.marital IN ('S', 'unmarried') OR p.marital IS NULL)
                / NULLIF(COUNT(*), 0), 1) AS single,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.marital = 'D')
                / NULLIF(COUNT(*), 0), 1) AS divorced,
            ROUND(100.0 * COUNT(*) FILTER (WHERE p.marital = 'W')
                / NULLIF(COUNT(*), 0), 1) AS widowed
        FROM cluster_patient cp
        JOIN patient p ON p.patient_id = cp.patient_id
        WHERE {_where(cluster_id)}
    """)
    row = db.execute(sql, _params(cluster_id)).mappings().first()
    if not row:
        return {"M": 0.0, "S": 0.0, "D": 0.0, "W": 0.0}
    return {
        "M": float(row["married"]  or 0),
        "S": float(row["single"]   or 0),
        "D": float(row["divorced"] or 0),
        "W": float(row["widowed"]  or 0),
    }


def get_smoking_distribution(db: Session, cluster_id: int) -> dict:
    sql = text(f"""
        WITH cluster_pts AS (
            SELECT patient_id FROM cluster_patient cp WHERE {_where(cluster_id)}
        ),
        patient_smoking AS (
            SELECT patient_id,
                CASE
                    WHEN LOWER(MAX(value)) LIKE '%daily%' OR LOWER(MAX(value)) LIKE '%current%' THEN 'current'
                    WHEN LOWER(MAX(value)) LIKE '%ex-smoker%' OR LOWER(MAX(value)) LIKE '%former%' THEN 'former'
                    ELSE 'never'
                END AS status
            FROM observation
            WHERE description ILIKE '%tobacco smoking status%' AND value IS NOT NULL
            GROUP BY patient_id
        )
        SELECT
            ROUND(100.0 * COUNT(*) FILTER (WHERE COALESCE(s.status, 'never') = 'current')
                / NULLIF(COUNT(*), 0), 1) AS current_pct,
            ROUND(100.0 * COUNT(*) FILTER (WHERE s.status = 'former')
                / NULLIF(COUNT(*), 0), 1) AS former_pct,
            ROUND(100.0 * COUNT(*) FILTER (WHERE COALESCE(s.status, 'never') = 'never')
                / NULLIF(COUNT(*), 0), 1) AS never_pct
        FROM cluster_pts cp
        LEFT JOIN patient_smoking s ON s.patient_id = cp.patient_id
    """)
    row = db.execute(sql, _params(cluster_id)).mappings().first()
    if not row:
        return {"current": 0.0, "former": 0.0, "never": 0.0}
    return {
        "current": float(row["current_pct"] or 0),
        "former":  float(row["former_pct"]  or 0),
        "never":   float(row["never_pct"]   or 0),
    }


def get_condition_burden_distribution(db: Session, cluster_id: int) -> dict:
    filters = _cluster_filters(cluster_id)
    row = (
        db.query(
            _flag_pct_expr("condition_burden", "low").label("low"),
            _flag_pct_expr("condition_burden", "medium").label("medium"),
            _flag_pct_expr("condition_burden", "high").label("high"),
        )
        .select_from(ClusterPatientModel)
        .filter(*filters)
        .first()
    )
    if not row:
        return {"low": 0.0, "medium": 0.0, "high": 0.0}
    return {"low": _f(row, "low"), "medium": _f(row, "medium"), "high": _f(row, "high")}


# baseline for the AI prompt to compare a cluster against; outliers excluded
# so extreme patients don't skew the population averages.
def get_population_stats(db: Session) -> dict:
    sql = text("""
        SELECT
            ROUND(AVG(p.age)::numeric, 1)                        AS pop_avg_age,
            ROUND(AVG(bmi.v)::numeric, 1)                        AS pop_avg_bmi,
            ROUND(AVG(bp.v)::numeric, 1)                         AS pop_avg_systolic_bp,
            ROUND(AVG(glu.v)::numeric, 1)                        AS pop_avg_glucose,
            ROUND(AVG(qaly.v)::numeric, 2)                       AS pop_avg_qaly,
            ROUND(AVG(daly.v)::numeric, 2)                       AS pop_avg_daly,
            ROUND(AVG(COALESCE(med.cnt, 0))::numeric, 1)         AS pop_avg_meds,
            ROUND(AVG(COALESCE(proc.cnt, 0))::numeric, 1)        AS pop_avg_procedures,
            ROUND(AVG(COALESCE(cond.active, 0))::numeric, 1)     AS pop_avg_conditions,
            ROUND(AVG(COALESCE(enc.days_since, 0))::numeric, 0)  AS pop_avg_days_since,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_diabetes     THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1)   AS pop_diabetes_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_hypertension THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1)   AS pop_hypertension_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_heart        THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1)   AS pop_heart_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.has_cancer       THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1)   AS pop_cancer_pct,
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN m.poly             THEN cp.patient_id END)
                / NULLIF(COUNT(DISTINCT cp.patient_id), 0), 1)   AS pop_polypharmacy_pct
        FROM cluster_patient cp
        JOIN patient p ON p.patient_id = cp.patient_id
        LEFT JOIN (SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE (description ILIKE '%bmi%' OR description ILIKE '%body mass index%')
              AND value_numeric BETWEEN 10 AND 100 GROUP BY patient_id
        ) bmi  ON bmi.patient_id  = cp.patient_id
        LEFT JOIN (SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%systolic%' AND description ILIKE '%blood pressure%'
              AND value_numeric > 0 GROUP BY patient_id
        ) bp   ON bp.patient_id   = cp.patient_id
        LEFT JOIN (SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%glucose%' AND description NOT ILIKE '%urine%'
              AND value_numeric BETWEEN 1 AND 1000 GROUP BY patient_id
        ) glu  ON glu.patient_id  = cp.patient_id
        LEFT JOIN (SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%qaly%' AND value_numeric IS NOT NULL GROUP BY patient_id
        ) qaly ON qaly.patient_id = cp.patient_id
        LEFT JOIN (SELECT patient_id, AVG(value_numeric) AS v FROM observation
            WHERE description ILIKE '%daly%' AND value_numeric IS NOT NULL GROUP BY patient_id
        ) daly ON daly.patient_id = cp.patient_id
        LEFT JOIN (SELECT patient_id, COUNT(*) AS cnt FROM medication GROUP BY patient_id
        ) med  ON med.patient_id  = cp.patient_id
        LEFT JOIN (SELECT patient_id, COUNT(*) AS cnt FROM "procedure" GROUP BY patient_id
        ) proc ON proc.patient_id = cp.patient_id
        LEFT JOIN (SELECT patient_id, COUNT(*) FILTER (WHERE end_date IS NULL) AS active
            FROM condition GROUP BY patient_id
        ) cond ON cond.patient_id = cp.patient_id
        LEFT JOIN (SELECT patient_id,
                EXTRACT(DAY FROM (CURRENT_DATE - MAX(end_date)))::int AS days_since
            FROM encounter WHERE end_date IS NOT NULL GROUP BY patient_id
        ) enc  ON enc.patient_id  = cp.patient_id
        LEFT JOIN (SELECT patient_id,
                MAX(CASE WHEN LOWER(description) LIKE '%diabetes%'
                          AND LOWER(description) NOT LIKE '%prediabetes%' THEN 1 ELSE 0 END) = 1 AS has_diabetes,
                MAX(CASE WHEN LOWER(description) LIKE '%hypertension%'   THEN 1 ELSE 0 END) = 1 AS has_hypertension,
                MAX(CASE WHEN LOWER(description) LIKE '%heart failure%'
                          OR  LOWER(description) LIKE '%coronary%'       THEN 1 ELSE 0 END) = 1 AS has_heart,
                MAX(CASE WHEN LOWER(description) LIKE '%cancer%'
                          OR  LOWER(description) LIKE '%carcinoma%'
                          OR  LOWER(description) LIKE '%malignant%'      THEN 1 ELSE 0 END) = 1 AS has_cancer
            FROM condition GROUP BY patient_id
        ) d    ON d.patient_id    = cp.patient_id
        LEFT JOIN (SELECT patient_id,
                COUNT(*) FILTER (WHERE end_date IS NULL) >= 5 AS poly
            FROM medication GROUP BY patient_id
        ) m    ON m.patient_id    = cp.patient_id
        WHERE cp.is_outlier = false
    """)
    row = db.execute(sql).mappings().first()
    if not row:
        return {}
    return {k: (float(row[k]) if row[k] is not None else None) for k in row.keys()}
