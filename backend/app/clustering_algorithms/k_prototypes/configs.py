CONFIGS = [
#     # v1 — Adjusted Baseline with Maternity  (6+4)
#     # Isolates the 100% maternity cluster from other high-utilizers to prevent skew.
#     {
#         "version": 1,
#         "numerical": [
#             "routine_care_count", "acute_care_count", "wellness_count",
#             "severe_care_count", "age", "clinical_severity_score",
#         ],
#         "categorical": [
#             "bmi_type", "gender", "dominant_careplan", "pregnancy_history",
#         ],
#     },
#
#     # v2 — Raw severity, no CSS  (5+6)
#     # Hypothesis: does active_conditions_count + lifetime_medication_days beat the
#     # PCA compression of clinical_severity_score at separating chronic archetypes?
#     # Utilization: severe_care_count + distinct_providers_seen = 2  ✓
#     {
#         "version": 2,
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "severe_care_count",
#             "distinct_providers_seen",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "has_hypertension",
#             "has_heart_disease",
#             "readmission_risk_tier",
#         ],
#     },
#
#     # v3 — Behavioral + readmission focus  (5+7)
#     # Hypothesis: substance use, pain tier, and out-of-hours behaviour separate
#     # high-risk patients more cleanly than utilization counts alone.
#     # Utilization: acute_care_count = 1  ✓
#     {
#         "version": 3,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "acute_care_count",
#             "preventive_to_reactive_ratio",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "substance_use_profile",
#             "pain_management_tier",
#             "out_of_hours_flyer",
#         ],
#     },
#
#     # v4 — Cardiometabolic deep-dive  (5+7)
#     # Hypothesis: combining the three chronic disease flags with cholesterol risk
#     # and care focus separates the cardio-metabolic patient spectrum cleanly.
#     # Utilization: distinct_providers_seen + total_encounter_duration_hours = 2  ✓
#     {
#         "version": 4,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_diabetes",
#             "has_hypertension",
#             "has_heart_disease",
#             "cholesterol_risk_category",
#             "dominant_careplan",
#         ],
#     },
#
#     # v5 — Respiratory + behavioral, lean numerical  (4+7)
#     # Hypothesis: a thin numerical side lets 7 strong categoricals dominate;
#     # respiratory profile and substance use should split the acute cluster.
#     # Utilization: acute_care_count = 1  ✓
#     {
#         "version": 5,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "acute_care_count",
#             "lifetime_medication_days",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "respiratory_disease_profile",
#             "substance_use_profile",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v6 — QALY replaces age  (5+6)
#     # Hypothesis: quality-adjusted life-years carries a different life-stage signal
#     # than raw age and may produce better separation for elderly/frail patients.
#     # Utilization: severe_care_count + distinct_providers_seen = 2  ✓
#     {
#         "version": 6,
#         "numerical": [
#             "qaly",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "severe_care_count",
#             "distinct_providers_seen",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "has_hypertension",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v7 — Care-continuity / system engagement  (5+6)
#     # Hypothesis: how patients interact with the system (fragmented vs. loyal,
#     # preventive vs. reactive) is a stronger clustering axis than disease flags.
#     # Utilization: distinct_providers_seen + total_encounter_duration_hours = 2  ✓
#     {
#         "version": 7,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "preventive_to_reactive_ratio",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_encounter_class",
#             "dominant_careplan",
#             "out_of_hours_flyer",
#             "readmission_risk_tier",
#         ],
#     },
#
#     # v8 — Dense categorical  (4+8)
#     # Hypothesis: 4 strong numericals + 8 well-chosen categoricals give the
#     # categorical side enough weight to drive richer clinical archetypes.
#     # Utilization: acute_care_count = 1  ✓
#     {
#         "version": 8,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "acute_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "has_diabetes",
#             "has_heart_disease",
#             "readmission_risk_tier",
#             "bmi_type",
#             "substance_use_profile",
#         ],
#     },
#
#     # v9 — Chronic disease flags + raw burden  (5+7)
#     # Hypothesis: raw active_conditions_count + disease flags (no CSS) combined
#     # with metabolic categoricals separates chronic subtypes better than PCA.
#     # Utilization: total_encounter_duration_hours + distinct_providers_seen = 2  ✓
#     {
#         "version": 9,
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "total_encounter_duration_hours",
#             "distinct_providers_seen",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "has_diabetes",
#             "has_hypertension",
#             "has_heart_disease",
#             "bmi_type",
#         ],
#     },
#
#     # v10 — Pain + substance + cholesterol  (5+7)
#     # Hypothesis: chronic pain management tier and cholesterol risk have not been
#     # combined before; this tests whether metabolic-behavioral overlap forms a
#     # distinct archetype separate from the standard chronic cluster.
#     # Utilization: severe_care_count + total_encounter_duration_hours = 2  ✓
#     {
#         "version": 10,
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "severe_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "pain_management_tier",
#             "substance_use_profile",
#             "cholesterol_risk_category",
#             "has_hypertension",
#         ],
#     },
#
#     # v11 — Lean categorical, rich numerical  (6+4)
#     # Hypothesis: tests the opposite extreme of v8 — 6 numericals drive separation
#     # while 4 strong categoricals anchor interpretation.
#     # Utilization: acute_care_count + distinct_providers_seen = 2  ✓
#     {
#         "version": 11,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "acute_care_count",
#             "distinct_providers_seen",
#             "preventive_to_reactive_ratio",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "readmission_risk_tier",
#         ],
#     },
#
#     # v12 — Balanced clinical + behavioral  (5+7)
#     # Hypothesis: 4 orthogonal axes (demographic, clinical, metabolic, behavioral)
#     # with no signal duplication; preventive_to_reactive_ratio replaces raw utilization.
#     {
#         "version": 12,
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "preventive_to_reactive_ratio",
#             "distinct_providers_seen",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "has_mental_health",
#             "bmi_type",
#             "substance_use_profile",
#             "readmission_risk_tier",
#         ],
#     },
#
#     # v13 — Care Continuity & System Engagement
#     {
#         "version": 13,
#         "numerical": [
#             "age",
#             "routine_care_count",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "preventive_to_reactive_ratio"
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_encounter_class",
#             "has_mental_health",
#             "pain_management_tier"
#         ]
#     },
#
#     # v14 — Canonical comprehensive — severity PCA + aggregated utilization
#     {
#         "version": 14,
#         "description": "Canonical comprehensive — severity PCA + aggregated utilization",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_mental_health",
#             "substance_use_profile",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v15 — Severity via raw components (meds + conditions) instead of PCA
#     {
#         "version": 15,
#         "description": "Severity via raw components (meds + conditions) instead of PCA",
#         "numerical": [
#             "age",
#             "total_medications",
#             "active_conditions_count",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_diabetes",
#             "has_hypertension",
#             "has_mental_health",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v16 — Chronicity via lifetime_medication_days + severe utilization split
#     {
#         "version": 16,
#         "description": "Chronicity via lifetime_medication_days + severe utilization split",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "distinct_providers_seen",
#             "lifetime_medication_days",
#             "acute_care_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "substance_use_profile",
#         ],
#     },
#
#     # v17 — Cardio-metabolic emphasis within a full comprehensive frame
#     {
#         "version": 17,
#         "description": "Cardio-metabolic emphasis within a full comprehensive frame",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_heart_disease",
#             "bp_risk_category",
#             "bmi_type",
#             "cholesterol_risk_category",
#             "dominant_careplan",
#         ],
#     },
#
#     # v18 — Behavioral-health emphasis (MH + substance + pain)
#     {
#         "version": 18,
#         "description": "Behavioral-health emphasis (MH + substance + pain)",
#         "numerical": [
#             "age",
#             "total_medications",
#             "emergency_count",
#             "distinct_providers_seen",
#             "wellness_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_mental_health",
#             "substance_use_profile",
#             "pain_management_tier",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v19 — Metabolic / diabetes-glucose emphasis in comprehensive frame
#     {
#         "version": 19,
#         "description": "Metabolic / diabetes-glucose emphasis in comprehensive frame",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_diabetes",
#             "glucose_risk_category",
#             "bmi_type",
#             "cholesterol_risk_category",
#             "dominant_careplan",
#             "readmission_risk_tier",
#         ],
#     },
#
#     # v20 — Full utilization axes (routine / acute / severe) with PCA severity
#     {
#         "version": 20,
#         "description": "Full utilization axes (routine / acute / severe) with PCA severity",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "routine_care_count",
#             "acute_care_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_mental_health",
#             "dominant_encounter_class",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "out_of_hours_flyer",
#         ],
#     },
#
#     # v21 — Raw encounter counts (emergency / inpatient / wellness) + raw severity
#     {
#         "version": 21,
#         "description": "Raw encounter counts (emergency / inpatient / wellness) + raw severity",
#         "numerical": [
#             "age",
#             "total_medications",
#             "active_conditions_count",
#             "emergency_count",
#             "inpatient_count",
#             "wellness_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_diabetes",
#             "has_mental_health",
#             "substance_use_profile",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v22 — Preventive-to-reactive ratio added (separates healthy preventive)
#     {
#         "version": 22,
#         "description": "Preventive-to-reactive ratio added (separates healthy preventive)",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "preventive_to_reactive_ratio",
#             "wellness_count",
#             "lifetime_medication_days",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_heart_disease",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#             "substance_use_profile",
#         ],
#     },
#
#     # v23 — Respiratory / oncology / renal emphasis (high-acuity detection)
#     {
#         "version": 23,
#         "description": "Respiratory / oncology / renal emphasis (high-acuity detection)",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "acute_care_count",
#             "severe_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "respiratory_disease_profile",
#             "has_cancer",
#             "has_kidney_disease",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v24 — Demographic / ethnic disparity axis added to comprehensive frame
#     {
#         "version": 24,
#         "description": "Demographic / ethnic disparity axis added to comprehensive frame",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "race",
#             "ethnicity",
#             "pregnancy_history",
#             "has_diabetes",
#             "has_hypertension",
#             "dominant_careplan",
#             "readmission_risk_tier",
#         ],
#     },
#
#     # v25 — Pain / opioid profile within severity-aware comprehensive frame
#     {
#         "version": 25,
#         "description": "Pain / opioid profile within severity-aware comprehensive frame",
#         "numerical": [
#             "age",
#             "total_medications",
#             "distinct_providers_seen",
#             "acute_care_count",
#             "severe_care_count",
#             "lifetime_medication_days",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "pain_management_tier",
#             "has_mental_health",
#             "substance_use_profile",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v26 — QALY-driven life-stage (replaces age) — independent life-stage signal
#     {
#         "version": 26,
#         "description": "QALY-driven life-stage (replaces age) — independent life-stage signal",
#         "numerical": [
#             "qaly",
#             "total_medications",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_mental_health",
#             "substance_use_profile",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v27 — Medication intensity as categorical (bucketed) instead of raw count
#     {
#         "version": 27,
#         "description": "Medication intensity as categorical (bucketed) instead of raw count",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "medication_intensity",
#             "has_hypertension",
#             "has_mental_health",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "bmi_type",
#         ],
#     },
#
#     # v28 — Preventive-ratio + active_conditions raw, lightest severity frame
#     {
#         "version": 28,
#         "description": "Preventive-ratio + active_conditions raw, lightest severity frame",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "distinct_providers_seen",
#             "wellness_count",
#             "acute_care_count",
#             "preventive_to_reactive_ratio",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_hypertension",
#             "has_mental_health",
#             "dominant_careplan",
#             "readmission_risk_tier",
#             "out_of_hours_flyer",
#             "bmi_type",
#         ],
#     },
#
#     # v29 — Baseline refined: tightest proven feature set
#     {
#         "version": 29,
#         "description": "Baseline refined: tightest proven feature set",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "has_hypertension",
#             "has_diabetes",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v30 — v29 with PCA severity swap (clinical_severity_score instead of raw conditions)
#     {
#         "version": 30,
#         "description": "v29 with PCA severity swap (clinical_severity_score instead of raw conditions)",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "has_hypertension",
#             "has_diabetes",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v31 — v29 + condition_burden bucketed (swap active_conditions_count → condition_burden categorical)
#     {
#         "version": 31,
#         "description": "v29 + condition_burden bucketed (swap active_conditions_count → condition_burden categorical)",
#         "numerical": [
#             "age",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#             "total_medications",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "condition_burden",
#             "has_diabetes",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v32 — v29 trimmed to 5+7 features (removes weakest slot each side)
#     {
#         "version": 32,
#         "description": "v29 trimmed to 5+7 features (removes weakest slot each side)",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "has_diabetes",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v33 — v29 + cholesterol_risk_category (swap bmi_type for best untested metabolic categorical)
#     {
#         "version": 33,
#         "description": "v29 + cholesterol_risk_category (swap bmi_type for best untested metabolic categorical)",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "has_hypertension",
#             "has_diabetes",
#             "dominant_careplan",
#             "cholesterol_risk_category",
#         ],
#     },
#
#     # v34 — v29 with glucose_risk_category replacing has_diabetes (graded vs binary)
#     {
#         "version": 34,
#         "description": "v29 with glucose_risk_category replacing has_diabetes (graded vs binary)",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "has_hypertension",
#             "glucose_risk_category",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v35 — v29 + routine_care_count replacing wellness_count (broader preventive signal)
#     {
#         "version": 35,
#         "description": "v29 + routine_care_count replacing wellness_count (broader preventive signal)",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "routine_care_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "is_polypharmacy",
#             "has_hypertension",
#             "has_diabetes",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v36 — Dual-severity stress test (violates redundancy rule — diagnostic only)
    {
        "version": 36,
        "description": "Corrected config: Kept clinical_severity_score, removed raw conditions to fix redundancy error",
        "numerical": [
            "age",
            "clinical_severity_score",
            "lifetime_medication_days",
            "wellness_count",
            "severe_care_count"
        ],
        "categorical": [
            "gender",
            "pregnancy_history",
            "has_heart_disease",
            "is_polypharmacy",
            "has_hypertension",
            "has_diabetes",
            "dominant_careplan",
            "bmi_type"
        ]
    },
#
#     # v37 — Maximal high-k config: 3 chronic flags + 2 graded metabolic (pushes k>=5 separation)
#     {
#         "version": 37,
#         "description": "Maximal high-k config: 3 chronic flags + 2 graded metabolic (pushes k>=5 separation)",
#         "numerical": [
#             "age",
#             "clinical_severity_score",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "has_diabetes",
#             "has_hypertension",
#             "cholesterol_risk_category",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v38 — Minimal 4+4 ablation — does k=4 survive feature starvation?
#     {
#         "version": 38,
#         "description": "Minimal 4+4 ablation — does k=4 survive feature starvation?",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "wellness_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "bmi_type",
#         ],
#     },
#
#     # v39 — Redundancy-free canonical reference — the clean baseline
#     {
#         "version": 39,
#         "description": "Redundancy-free canonical reference — the clean baseline",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "has_diabetes",
#             "has_hypertension",
#             "dominant_careplan",
#             "bmi_type",
#             "substance_use_profile",
#         ],
#     },
#
#     # v40 — Severity-only — drop all utilization signals
#     {
#         "version": 40,
#         "description": "Severity-only — drop all utilization signals",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "total_medications",
#             "lifetime_medication_days",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "has_diabetes",
#             "has_hypertension",
#             "condition_burden",
#             "bmi_type",
#             "cholesterol_risk_category",
#         ],
#     },
#
#     # v41 — Utilization-only — drop severity/chronicity signals
#     {
#         "version": 41,
#         "description": "Utilization-only — drop severity/chronicity signals",
#         "numerical": [
#             "age",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#             "routine_care_count",
#             "total_encounter_duration_hours",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "dominant_encounter_class",
#             "out_of_hours_flyer",
#             "pain_management_tier",
#         ],
#     },
#
#     # v42 — Demographics-only sanity baseline (expect worst result)
#     {
#         "version": 42,
#         "description": "Demographics-only sanity baseline (expect worst result)",
#         "numerical": [
#             "age",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "race",
#             "ethnicity",
#         ],
#     },
#
#     # v43 — Bucketed-categorical emphasis — condition_burden + medication_intensity
#     {
#         "version": 43,
#         "description": "Bucketed-categorical emphasis — condition_burden + medication_intensity",
#         "numerical": [
#             "age",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "condition_burden",
#             "medication_intensity",
#             "has_heart_disease",
#             "has_diabetes",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v44 — Balanced axes — one feature per clinical dimension, nothing duplicated
#     {
#         "version": 44,
#         "description": "Balanced axes — one feature per clinical dimension, nothing duplicated",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "has_diabetes",
#             "bmi_type",
#             "dominant_careplan",
#         ],
#     },
#
#     # v45 — No disease flags — test whether clusters survive without direct condition labels
#     {
#         "version": 45,
#         "description": "No disease flags — test whether clusters survive without direct condition labels",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "dominant_careplan",
#             "bmi_type",
#             "substance_use_profile",
#         ],
#     },
#
#     # v46 — No age — does life-stage re-emerge from medical features alone?
#     {
#         "version": 46,
#         "description": "No age — does life-stage re-emerge from medical features alone?",
#         "numerical": [
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "qaly",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "has_diabetes",
#             "has_hypertension",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
#
#     # v47 — Thesis final candidate — the configuration to defend in Chapter 4
#     {
#         "version": 47,
#         "description": "Thesis final candidate — the configuration to defend in Chapter 4",
#         "numerical": [
#             "age",
#             "active_conditions_count",
#             "lifetime_medication_days",
#             "distinct_providers_seen",
#             "wellness_count",
#             "severe_care_count",
#         ],
#         "categorical": [
#             "gender",
#             "pregnancy_history",
#             "has_heart_disease",
#             "has_diabetes",
#             "has_hypertension",
#             "dominant_careplan",
#             "bmi_type",
#         ],
#     },
]