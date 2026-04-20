# K-prototypes clustering configurations.
#
# Design goal: each config is COMPREHENSIVE. A single k-prototypes run on any
# one config should be able to separate every major patient archetype that
# exists in the data — pediatric, maternal, young adult, senior chronic,
# mental-health dominant, high-acuity / frequent-flyer, healthy preventive.
#
# To make that possible, every config covers all of these axes:
#   - life stage          : age (or qaly as alternative)
#   - reproductive        : gender + pregnancy_history  (isolates maternal)
#   - chronic disease     : >=2 disease flags           (isolates chronic-heavy)
#   - severity / burden   : clinical_severity_score OR raw (total_meds +
#                           active_conditions) OR condition_burden
#   - utilization pattern : wellness / routine / acute / severe counts +
#                           distinct_providers_seen
#   - behavioral          : substance_use_profile OR pain_management_tier
#                           OR has_mental_health
#   - care focus          : dominant_careplan and/or dominant_encounter_class
#   - readmission / acuity: readmission_risk_tier OR has_inpatient_history
#   - metabolic snapshot  : bmi_type / bp_risk_category / glucose_risk /
#                           cholesterol_risk_category
#
# The 15 configs differ in WHICH feature fills each axis, not in which axes
# are covered. That lets the 15 runs cross-validate: clusters that appear
# stably across configs are real; ones that only show up under one feature
# choice are artifacts.
#
# Redundancy rules enforced in every config:
#   - `clinical_severity_score` (PCA of total_procedures + total_medications +
#     active_conditions_count) is NEVER combined with any of those three raws.
#   - `medication_intensity` and `is_polypharmacy` are buckets/thresholds of
#     total_medications — never combined with total_medications.
#   - `condition_burden` is a bucket of active_conditions_count — never paired.
#   - `routine_care_count` / `acute_care_count` / `severe_care_count` are
#     aggregates — never paired with their underlying raw encounter counts.
#   - `has_inpatient_history` is never paired with inpatient_count or
#     severe_care_count in the same config.
#   - `age` is never combined with `qaly` (QALY ~ life-years) — v13 drops age
#     and uses qaly instead.

CONFIGS = [
    {
        "version": 1,
        "description": "Canonical comprehensive — severity PCA + aggregated utilization",
        "numerical": [
            "age",
            "clinical_severity_score",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_mental_health",
            "substance_use_profile",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 2,
        "description": "Severity via raw components (meds + conditions) instead of PCA",
        "numerical": [
            "age",
            "total_medications",
            "active_conditions_count",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_diabetes",
            "has_hypertension",
            "has_mental_health",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 3,
        "description": "Chronicity via lifetime_medication_days + severe utilization split",
        "numerical": [
            "age",
            "active_conditions_count",
            "distinct_providers_seen",
            "lifetime_medication_days",
            "acute_care_count",
            "severe_care_count",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_heart_disease",
            "is_polypharmacy",
            "dominant_careplan",
            "readmission_risk_tier",
            "substance_use_profile",
        ],
    },
    {
        "version": 4,
        "description": "Cardio-metabolic emphasis within a full comprehensive frame",
        "numerical": [
            "age",
            "clinical_severity_score",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_heart_disease",
            "bp_risk_category",
            "bmi_type",
            "cholesterol_risk_category",
            "dominant_careplan",
        ],
    },
    {
        "version": 5,
        "description": "Behavioral-health emphasis (MH + substance + pain)",
        "numerical": [
            "age",
            "total_medications",
            "emergency_count",
            "distinct_providers_seen",
            "wellness_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_mental_health",
            "substance_use_profile",
            "pain_management_tier",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 6,
        "description": "Metabolic / diabetes-glucose emphasis in comprehensive frame",
        "numerical": [
            "age",
            "active_conditions_count",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_diabetes",
            "glucose_risk_category",
            "bmi_type",
            "cholesterol_risk_category",
            "dominant_careplan",
            "readmission_risk_tier",
        ],
    },
    {
        "version": 7,
        "description": "Full utilization axes (routine / acute / severe) with PCA severity",
        "numerical": [
            "age",
            "clinical_severity_score",
            "distinct_providers_seen",
            "routine_care_count",
            "acute_care_count",
            "severe_care_count",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_mental_health",
            "dominant_encounter_class",
            "dominant_careplan",
            "readmission_risk_tier",
            "out_of_hours_flyer",
        ],
    },
    {
        "version": 8,
        "description": "Raw encounter counts (emergency / inpatient / wellness) + raw severity",
        "numerical": [
            "age",
            "total_medications",
            "active_conditions_count",
            "emergency_count",
            "inpatient_count",
            "wellness_count",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_diabetes",
            "has_mental_health",
            "substance_use_profile",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 9,
        "description": "Preventive-to-reactive ratio added (separates healthy preventive)",
        "numerical": [
            "age",
            "clinical_severity_score",
            "distinct_providers_seen",
            "preventive_to_reactive_ratio",
            "wellness_count",
            "lifetime_medication_days",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_heart_disease",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
            "substance_use_profile",
        ],
    },
    {
        "version": 10,
        "description": "Respiratory / oncology / renal emphasis (high-acuity detection)",
        "numerical": [
            "age",
            "clinical_severity_score",
            "distinct_providers_seen",
            "acute_care_count",
            "severe_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "respiratory_disease_profile",
            "has_cancer",
            "has_kidney_disease",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 11,
        "description": "Demographic / ethnic disparity axis added to comprehensive frame",
        "numerical": [
            "age",
            "clinical_severity_score",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "race",
            "ethnicity",
            "pregnancy_history",
            "has_diabetes",
            "has_hypertension",
            "dominant_careplan",
            "readmission_risk_tier",
        ],
    },
    {
        "version": 12,
        "description": "Pain / opioid profile within severity-aware comprehensive frame",
        "numerical": [
            "age",
            "total_medications",
            "distinct_providers_seen",
            "acute_care_count",
            "severe_care_count",
            "lifetime_medication_days",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "pain_management_tier",
            "has_mental_health",
            "substance_use_profile",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 13,
        "description": "QALY-driven life-stage (replaces age) — independent life-stage signal",
        "numerical": [
            "qaly",
            "total_medications",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_mental_health",
            "substance_use_profile",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 14,
        "description": "Medication intensity as categorical (bucketed) instead of raw count",
        "numerical": [
            "age",
            "active_conditions_count",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "total_encounter_duration_hours",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "medication_intensity",
            "has_hypertension",
            "has_mental_health",
            "dominant_careplan",
            "readmission_risk_tier",
            "bmi_type",
        ],
    },
    {
        "version": 15,
        "description": "Preventive-ratio + active_conditions raw, lightest severity frame",
        "numerical": [
            "age",
            "active_conditions_count",
            "distinct_providers_seen",
            "wellness_count",
            "acute_care_count",
            "preventive_to_reactive_ratio",
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_hypertension",
            "has_mental_health",
            "dominant_careplan",
            "readmission_risk_tier",
            "out_of_hours_flyer",
            "bmi_type",
        ],
    },
]
