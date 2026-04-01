# Statistics - SQL Queries & Endpoint Results

All queries are written as plain SQL equivalent of the SQLAlchemy ORM calls in
`app/repository/statistics_repository/`.

---

## 1. Patients - `GET /statistics/patients`

### SQL Queries

```sql
-- Total patients
SELECT COUNT(patient_id) FROM patients;

-- Age group distribution
SELECT
  CASE
    WHEN age BETWEEN 0  AND 18 THEN '0-18'
    WHEN age BETWEEN 19 AND 35 THEN '19-35'
    WHEN age BETWEEN 36 AND 50 THEN '36-50'
    WHEN age BETWEEN 51 AND 65 THEN '51-65'
    ELSE '65+'
  END AS label,
  COUNT(patient_id) AS count
FROM patients
GROUP BY label
ORDER BY label;

-- Gender distribution
SELECT gender AS label, COUNT(patient_id) AS count
FROM patients
GROUP BY gender
ORDER BY COUNT(patient_id) DESC;

-- Race distribution
SELECT race AS label, COUNT(patient_id) AS count
FROM patients
GROUP BY race
ORDER BY COUNT(patient_id) DESC;

-- Ethnicity distribution
SELECT ethnicity AS label, COUNT(patient_id) AS count
FROM patients
GROUP BY ethnicity
ORDER BY COUNT(patient_id) DESC;

-- Marital status distribution
SELECT marital AS label, COUNT(patient_id) AS count
FROM patients
GROUP BY marital
ORDER BY COUNT(patient_id) DESC;

-- Vital status (alive / deceased)
SELECT
  CASE WHEN deathdate IS NULL THEN 'Alive' ELSE 'Deceased' END AS label,
  COUNT(patient_id) AS count
FROM patients
GROUP BY label;

-- Top cities by patient count
SELECT city AS label, COUNT(patient_id) AS count
FROM patients
GROUP BY city
ORDER BY COUNT(patient_id) DESC;
```

### Endpoint Response

```json
{
  "total_patients": 1171,
  "age_groups": [
    {"name": "0-18",  "value": 178.0, "tooltip": "0-18: 178 patients (15.2%)"},
    {"name": "19-35", "value": 258.0, "tooltip": "19-35: 258 patients (22.03%)"},
    {"name": "36-50", "value": 203.0, "tooltip": "36-50: 203 patients (17.34%)"},
    {"name": "51-65", "value": 261.0, "tooltip": "51-65: 261 patients (22.29%)"},
    {"name": "65+",   "value": 271.0, "tooltip": "65+: 271 patients (23.14%)"}
  ],
  "gender": [
    {"name": "F", "value": 609.0, "tooltip": "F: 609 patients (52.01%)"},
    {"name": "M", "value": 562.0, "tooltip": "M: 562 patients (47.99%)"}
  ],
  "race": [
    {"name": "white",  "value": 965.0, "tooltip": "white: 965 patients (82.41%)"},
    {"name": "black",  "value": 101.0, "tooltip": "black: 101 patients (8.63%)"},
    {"name": "asian",  "value":  90.0, "tooltip": "asian: 90 patients (7.69%)"},
    {"name": "native", "value":  13.0, "tooltip": "native: 13 patients (1.11%)"},
    {"name": "other",  "value":   2.0, "tooltip": "other: 2 patients (0.17%)"}
  ],
  "ethnicity": [
    {"name": "nonhispanic", "value": 1058.0, "tooltip": "nonhispanic: 1058 patients (90.35%)"},
    {"name": "hispanic",    "value":  113.0, "tooltip": "hispanic: 113 patients (9.65%)"}
  ],
  "marital_status": [
    {"name": "M", "value": 638.0, "tooltip": "M: 638 patients (54.48%)"},
    {"name": "S", "value": 533.0, "tooltip": "S: 533 patients (45.52%)"}
  ],
  "vital_status": [
    {"name": "Deceased", "value": 171.0,  "tooltip": "Deceased: 171 patients (14.6%)"},
    {"name": "Alive",    "value": 1000.0, "tooltip": "Alive: 1000 patients (85.4%)"}
  ],
  "top_cities": [
    {"name": "Boston",      "value": 116.0, "tooltip": "Boston: 116 patients (9.91%)"},
    {"name": "Worcester",   "value":  31.0, "tooltip": "Worcester: 31 patients (2.65%)"},
    {"name": "Cambridge",   "value":  27.0, "tooltip": "Cambridge: 27 patients (2.31%)"},
    {"name": "Springfield", "value":  23.0, "tooltip": "Springfield: 23 patients (1.96%)"},
    {"name": "Quincy",      "value":  20.0, "tooltip": "Quincy: 20 patients (1.71%)"},
    {"name": "Fall River",  "value":  19.0, "tooltip": "Fall River: 19 patients (1.62%)"},
    {"name": "Lowell",      "value":  18.0, "tooltip": "Lowell: 18 patients (1.54%)"},
    {"name": "Lynn",        "value":  18.0, "tooltip": "Lynn: 18 patients (1.54%)"},
    {"name": "New Bedford", "value":  17.0, "tooltip": "New Bedford: 17 patients (1.45%)"},
    {"name": "Others",      "value": 882.0, "tooltip": "Others: 882 patients (75.32%)"}
  ]
}
```

---

## 2. Encounters - `GET /statistics/encounters`

### SQL Queries

```sql
-- Total encounters
SELECT COUNT(encounter_id) FROM encounters;

-- Encounter class distribution
SELECT encounter_class AS label, COUNT(encounter_id) AS count
FROM encounters
GROUP BY encounter_class
ORDER BY COUNT(encounter_id) DESC;

-- Duration stats per encounter class
SELECT
  encounter_class AS label,
  COUNT(encounter_id) AS count,
  ROUND(CAST(MIN(duration) AS NUMERIC), 2) AS min_duration,
  ROUND(CAST(MAX(duration) AS NUMERIC), 2) AS max_duration,
  ROUND(CAST(AVG(duration) AS NUMERIC), 2) AS avg_duration
FROM encounters
GROUP BY encounter_class
ORDER BY COUNT(encounter_id) DESC;

-- Top 10 encounter descriptions
SELECT description AS label, COUNT(encounter_id) AS count
FROM encounters
GROUP BY description
ORDER BY COUNT(encounter_id) DESC
LIMIT 10;

-- Top 10 reason descriptions (excluding NULL)
SELECT reason_description AS label, COUNT(encounter_id) AS count
FROM encounters
WHERE reason_description IS NOT NULL
GROUP BY reason_description
ORDER BY COUNT(encounter_id) DESC
LIMIT 10;
```

### Endpoint Response

```json
{
  "total_encounters": 53346,
  "encounter_class": [
    {"name": "wellness",    "value": 19106.0, "tooltip": "wellness: 19106 encounters (35.82%)"},
    {"name": "ambulatory",  "value": 18936.0, "tooltip": "ambulatory: 18936 encounters (35.5%)"},
    {"name": "outpatient",  "value":  9003.0, "tooltip": "outpatient: 9003 encounters (16.88%)"},
    {"name": "urgentcare",  "value":  2373.0, "tooltip": "urgentcare: 2373 encounters (4.45%)"},
    {"name": "emergency",   "value":  2090.0, "tooltip": "emergency: 2090 encounters (3.92%)"},
    {"name": "inpatient",   "value":  1838.0, "tooltip": "inpatient: 1838 encounters (3.45%)"}
  ],
  "duration_stats": [
    {"name": "wellness",   "count": 19106, "min_duration": 15.0,   "max_duration": 77.0,    "avg_duration": 22.37,   "median_duration": 0.0},
    {"name": "ambulatory", "count": 18936, "min_duration": 15.0,   "max_duration": 480.0,   "avg_duration": 69.02,   "median_duration": 0.0},
    {"name": "outpatient", "count":  9003, "min_duration": 15.0,   "max_duration": 1440.0,  "avg_duration": 39.48,   "median_duration": 0.0},
    {"name": "urgentcare", "count":  2373, "min_duration": 15.0,   "max_duration": 15.0,    "avg_duration": 15.0,    "median_duration": 0.0},
    {"name": "emergency",  "count":  2090, "min_duration": 60.0,   "max_duration": 4320.0,  "avg_duration": 84.2,    "median_duration": 0.0},
    {"name": "inpatient",  "count":  1838, "min_duration": 1440.0, "max_duration": 43200.0, "avg_duration": 1656.63, "median_duration": 0.0}
  ],
  "top_descriptions": [
    {"name": "General examination of patient (procedure)", "value": 14946.0, "tooltip": "General examination of patient (procedure): 14946 encounters (28.02%)"},
    {"name": "Encounter for problem (procedure)",          "value":  5196.0, "tooltip": "Encounter for problem (procedure): 5196 encounters (9.74%)"},
    {"name": "Encounter for check up (procedure)",        "value":  4515.0, "tooltip": "Encounter for check up (procedure): 4515 encounters (8.46%)"},
    {"name": "Well child visit (procedure)",               "value":  4144.0, "tooltip": "Well child visit (procedure): 4144 encounters (7.77%)"},
    {"name": "Encounter for symptom",                     "value":  3929.0, "tooltip": "Encounter for symptom: 3929 encounters (7.37%)"},
    {"name": "Prenatal visit",                            "value":  2676.0, "tooltip": "Prenatal visit: 2676 encounters (5.02%)"},
    {"name": "Urgent care clinic (procedure)",             "value":  2373.0, "tooltip": "Urgent care clinic (procedure): 2373 encounters (4.45%)"},
    {"name": "Encounter for problem",                     "value":  2291.0, "tooltip": "Encounter for problem: 2291 encounters (4.29%)"},
    {"name": "Follow-up encounter",                       "value":  2282.0, "tooltip": "Follow-up encounter: 2282 encounters (4.28%)"},
    {"name": "Patient encounter procedure",               "value":  1624.0, "tooltip": "Patient encounter procedure: 1624 encounters (3.04%)"}
  ],
  "top_reason_descriptions": [
    {"name": "no_reason_specified",                          "value": 39569.0, "tooltip": "no_reason_specified: 39569 encounters (74.17%)"},
    {"name": "Normal pregnancy",                             "value":  3779.0, "tooltip": "Normal pregnancy: 3779 encounters (7.08%)"},
    {"name": "Hyperlipidemia",                               "value":  2273.0, "tooltip": "Hyperlipidemia: 2273 encounters (4.26%)"},
    {"name": "Viral sinusitis (disorder)",                   "value":  1378.0, "tooltip": "Viral sinusitis (disorder): 1378 encounters (2.58%)"},
    {"name": "Acute viral pharyngitis (disorder)",           "value":   691.0, "tooltip": "Acute viral pharyngitis (disorder): 691 encounters (1.3%)"},
    {"name": "Acute bronchitis (disorder)",                  "value":   690.0, "tooltip": "Acute bronchitis (disorder): 690 encounters (1.29%)"},
    {"name": "Chronic congestive heart failure (disorder)",  "value":   620.0, "tooltip": "Chronic congestive heart failure (disorder): 620 encounters (1.16%)"},
    {"name": "Malignant neoplasm of breast (disorder)",      "value":   585.0, "tooltip": "Malignant neoplasm of breast (disorder): 585 encounters (1.1%)"},
    {"name": "Child attention deficit disorder",             "value":   287.0, "tooltip": "Child attention deficit disorder: 287 encounters (0.54%)"},
    {"name": "Sinusitis (disorder)",                         "value":   265.0, "tooltip": "Sinusitis (disorder): 265 encounters (0.5%)"}
  ]
}
```

---

## 3. Conditions - `GET /statistics/conditions`

### SQL Queries

```sql
-- Total condition records
SELECT COUNT(condition_code) FROM conditions;

-- Unique condition codes
SELECT COUNT(DISTINCT condition_code) FROM conditions;

-- Active vs Resolved
SELECT
  CASE WHEN end_date IS NULL THEN 'Active' ELSE 'Resolved' END AS label,
  COUNT(condition_code) AS count
FROM conditions
GROUP BY label;

-- Top 20 conditions by frequency
SELECT description AS label, COUNT(condition_code) AS count
FROM conditions
GROUP BY description
ORDER BY COUNT(condition_code) DESC
LIMIT 20;

-- Per-patient condition stats
SELECT
  ROUND(CAST(AVG(cnt) AS NUMERIC), 2) AS avg,
  MIN(cnt) AS min,
  MAX(cnt) AS max
FROM (
  SELECT patient_id, COUNT(condition_code) AS cnt
  FROM conditions
  GROUP BY patient_id
) AS per_patient;
```

### Endpoint Response

```json
{
  "total_conditions": 8376,
  "unique_conditions": 129,
  "per_patient": {"avg": 7.27, "min": 1, "max": 25},
  "active_vs_resolved": [
    {"name": "Active",   "value": 3811.0, "tooltip": "Active: 3811 (45.5%)"},
    {"name": "Resolved", "value": 4565.0, "tooltip": "Resolved: 4565 (54.5%)"}
  ],
  "top_conditions": [
    {"name": "Viral sinusitis (disorder)",                "value": 1248.0, "tooltip": "Viral sinusitis (disorder): 1248 (14.9%)"},
    {"name": "Acute viral pharyngitis (disorder)",        "value":  653.0, "tooltip": "Acute viral pharyngitis (disorder): 653 (7.8%)"},
    {"name": "Acute bronchitis (disorder)",               "value":  563.0, "tooltip": "Acute bronchitis (disorder): 563 (6.72%)"},
    {"name": "Normal pregnancy",                          "value":  516.0, "tooltip": "Normal pregnancy: 516 (6.16%)"},
    {"name": "Body mass index 30+ - obesity (finding)",   "value":  449.0, "tooltip": "Body mass index 30+ - obesity (finding): 449 (5.36%)"},
    {"name": "Prediabetes",                               "value":  317.0, "tooltip": "Prediabetes: 317 (3.78%)"},
    {"name": "Hypertension",                              "value":  302.0, "tooltip": "Hypertension: 302 (3.61%)"},
    {"name": "Anemia (disorder)",                         "value":  300.0, "tooltip": "Anemia (disorder): 300 (3.58%)"},
    {"name": "Chronic sinusitis (disorder)",              "value":  236.0, "tooltip": "Chronic sinusitis (disorder): 236 (2.82%)"},
    {"name": "Miscarriage in first trimester",            "value":  221.0, "tooltip": "Miscarriage in first trimester: 221 (2.64%)"},
    {"name": "Otitis media",                              "value":  196.0, "tooltip": "Otitis media: 196 (2.34%)"},
    {"name": "Streptococcal sore throat (disorder)",      "value":  157.0, "tooltip": "Streptococcal sore throat (disorder): 157 (1.87%)"},
    {"name": "Hyperlipidemia",                            "value":  136.0, "tooltip": "Hyperlipidemia: 136 (1.62%)"},
    {"name": "Sprain of ankle",                           "value":  134.0, "tooltip": "Sprain of ankle: 134 (1.6%)"},
    {"name": "Polyp of colon",                            "value":   79.0, "tooltip": "Polyp of colon: 79 (0.94%)"},
    {"name": "Concussion with no loss of consciousness",  "value":   77.0, "tooltip": "Concussion with no loss of consciousness: 77 (0.92%)"},
    {"name": "Diabetes",                                  "value":   76.0, "tooltip": "Diabetes: 76 (0.91%)"},
    {"name": "Metabolic syndrome X (disorder)",           "value":   74.0, "tooltip": "Metabolic syndrome X (disorder): 74 (0.88%)"},
    {"name": "Hypertriglyceridemia (disorder)",           "value":   74.0, "tooltip": "Hypertriglyceridemia (disorder): 74 (0.88%)"},
    {"name": "Acute bacterial sinusitis (disorder)",      "value":   69.0, "tooltip": "Acute bacterial sinusitis (disorder): 69 (0.82%)"}
  ]
}
```

---

## 4. Observations - `GET /statistics/observations`

### SQL Queries

```sql
-- Total observation records
SELECT COUNT(observation_code) FROM observations;

-- Unique observation types
SELECT COUNT(DISTINCT observation_code) FROM observations;

-- Top 15 observation types by frequency
SELECT description AS label, COUNT(observation_code) AS count
FROM observations
GROUP BY description
ORDER BY COUNT(observation_code) DESC
LIMIT 15;

-- Numeric observation stats (top 25 by patient coverage)
SELECT
  o.description AS label,
  COUNT(o.observation_code) AS count,
  COUNT(DISTINCT o.patient_id) AS patient_count,
  ROUND(CAST(MIN(o.value_numeric) AS NUMERIC), 2) AS min_value,
  ROUND(CAST(MAX(o.value_numeric) AS NUMERIC), 2) AS max_value,
  ROUND(CAST(AVG(o.value_numeric) AS NUMERIC), 2) AS avg_value,
  o.units
FROM observations o
WHERE o.value_numeric IS NOT NULL
GROUP BY o.description, o.units
ORDER BY COUNT(DISTINCT o.patient_id) DESC
LIMIT 25;

-- Per-patient observation stats
SELECT
  ROUND(CAST(AVG(cnt) AS NUMERIC), 2) AS avg,
  MIN(cnt) AS min,
  MAX(cnt) AS max
FROM (
  SELECT patient_id, COUNT(observation_code) AS cnt
  FROM observations
  GROUP BY patient_id
) AS per_patient;
```

### Endpoint Response

```json
{
  "total_observations": 299697,
  "unique_observation_types": 125,
  "per_patient": {"avg": 255.93, "min": 34, "max": 9023},
  "top_observation_types": [
    {"name": "Pain severity - 0-10 verbal numeric rating [Score] - Reported", "value": 16820.0},
    {"name": "Systolic Blood Pressure",   "value": 12963.0},
    {"name": "Diastolic Blood Pressure",  "value": 12963.0},
    {"name": "Body Weight",               "value": 12552.0},
    {"name": "Respiratory rate",          "value": 12552.0},
    {"name": "Body Height",               "value": 12552.0},
    {"name": "Heart rate",                "value": 12552.0},
    {"name": "Tobacco smoking status NHIS","value": 12552.0},
    {"name": "Body Mass Index",           "value": 11451.0},
    {"name": "QALY",                      "value": 10121.0},
    {"name": "DALY",                      "value": 10121.0},
    {"name": "QOLS",                      "value": 10121.0},
    {"name": "Calcium",                   "value":  6515.0},
    {"name": "Creatinine",                "value":  6515.0},
    {"name": "Glucose",                   "value":  6515.0}
  ],
  "numeric_stats": [
    {"name": "Pain severity - 0-10 verbal numeric rating [Score] - Reported", "count": 16820, "patient_count": 1171, "percentage": 100.0, "min_value": 0.0,   "max_value": 10.0,   "avg_value": 2.63,   "units": "{score}"},
    {"name": "Leukocytes [#/volume] in Blood by Automated count",             "count":  2558, "patient_count": 1171, "percentage": 100.0, "min_value": 0.5,   "max_value": 10.5,   "avg_value": 6.28,   "units": "10*3/uL"},
    {"name": "Diastolic Blood Pressure",                                      "count": 12963, "patient_count": 1171, "percentage": 100.0, "min_value": 67.0,  "max_value": 121.0,  "avg_value": 81.0,   "units": "mm[Hg]"},
    {"name": "Body Weight",                                                   "count": 12552, "patient_count": 1171, "percentage": 100.0, "min_value": 1.8,   "max_value": 140.9,  "avg_value": 66.39,  "units": "kg"},
    {"name": "MCV [Entitic volume] by Automated count",                       "count":  2639, "patient_count": 1171, "percentage": 100.0, "min_value": 80.0,  "max_value": 95.0,   "avg_value": 87.38,  "units": "fL"},
    {"name": "Platelet mean volume [Entitic volume] in Blood by Automated count", "count": 2639, "patient_count": 1171, "percentage": 100.0, "min_value": 9.4, "max_value": 12.3,  "avg_value": 10.84,  "units": "fL"},
    {"name": "Platelet distribution width [Entitic volume] in Blood by Automated count", "count": 2639, "patient_count": 1171, "percentage": 100.0, "min_value": 150.1, "max_value": 520.0, "avg_value": 335.12, "units": "fL"},
    {"name": "Systolic Blood Pressure",                                       "count": 12963, "patient_count": 1171, "percentage": 100.0, "min_value": 98.0,  "max_value": 201.0,  "avg_value": 122.45, "units": "mm[Hg]"},
    {"name": "Platelets [#/volume] in Blood by Automated count",              "count":  2639, "patient_count": 1171, "percentage": 100.0, "min_value": 150.0, "max_value": 449.9,  "avg_value": 299.51, "units": "10*3/uL"},
    {"name": "Hematocrit [Volume Fraction] of Blood by Automated count",      "count":  2558, "patient_count": 1171, "percentage": 100.0, "min_value": 25.0,  "max_value": 50.0,   "avg_value": 42.09,  "units": "%"},
    {"name": "Hemoglobin [Mass/volume] in Blood",                             "count":  2645, "patient_count": 1171, "percentage": 100.0, "min_value": 6.0,   "max_value": 17.5,   "avg_value": 14.42,  "units": "g/dL"},
    {"name": "MCHC [Mass/volume] by Automated count",                         "count":  2639, "patient_count": 1171, "percentage": 100.0, "min_value": 33.0,  "max_value": 36.0,   "avg_value": 34.54,  "units": "g/dL"},
    {"name": "MCH [Entitic mass] by Automated count",                         "count":  2639, "patient_count": 1171, "percentage": 100.0, "min_value": 27.0,  "max_value": 33.0,   "avg_value": 29.98,  "units": "pg"},
    {"name": "Respiratory rate",                                              "count": 12552, "patient_count": 1171, "percentage": 100.0, "min_value": 12.0,  "max_value": 16.0,   "avg_value": 14.02,  "units": "/min"},
    {"name": "Body Height",                                                   "count": 12552, "patient_count": 1171, "percentage": 100.0, "min_value": 45.1,  "max_value": 198.7,  "avg_value": 153.85, "units": "cm"},
    {"name": "Erythrocytes [#/volume] in Blood by Automated count",           "count":  2558, "patient_count": 1171, "percentage": 100.0, "min_value": 3.9,   "max_value": 5.5,    "avg_value": 4.7,    "units": "10*6/uL"},
    {"name": "Heart rate",                                                    "count": 12552, "patient_count": 1171, "percentage": 100.0, "min_value": 60.0,  "max_value": 100.0,  "avg_value": 79.68,  "units": "/min"},
    {"name": "Erythrocyte distribution width [Entitic volume] by Automated count", "count": 2558, "patient_count": 1171, "percentage": 100.0, "min_value": 39.0, "max_value": 46.0, "avg_value": 42.49, "units": "fL"},
    {"name": "Body Mass Index",                                               "count": 11451, "patient_count": 1134, "percentage": 96.84, "min_value": 13.4,  "max_value": 48.5,   "avg_value": 26.18,  "units": "kg/m2"},
    {"name": "QALY",                                                          "count": 10121, "patient_count": 1056, "percentage": 90.18, "min_value": -0.1,  "max_value": 104.5,  "avg_value": 33.98,  "units": "a"},
    {"name": "QOLS",                                                          "count": 10121, "patient_count": 1056, "percentage": 90.18, "min_value": 0.0,   "max_value": 1.0,    "avg_value": 0.9,    "units": "{score}"},
    {"name": "DALY",                                                          "count": 10121, "patient_count": 1056, "percentage": 90.18, "min_value": 0.0,   "max_value": 57.4,   "avg_value": 2.36,   "units": "a"},
    {"name": "High Density Lipoprotein Cholesterol",                          "count":  5264, "patient_count":  728, "percentage": 62.17, "min_value": 20.2,  "max_value": 80.0,   "avg_value": 61.37,  "units": "mg/dL"},
    {"name": "Low Density Lipoprotein Cholesterol",                           "count":  5264, "patient_count":  728, "percentage": 62.17, "min_value": 53.2,  "max_value": 198.3,  "avg_value": 103.29, "units": "mg/dL"},
    {"name": "Total Cholesterol",                                             "count":  5264, "patient_count":  728, "percentage": 62.17, "min_value": 150.0, "max_value": 304.0,  "avg_value": 190.48, "units": "mg/dL"}
  ]
}
```

---

## 5. Procedures - `GET /statistics/procedures`

### SQL Queries

```sql
-- Total procedure records
SELECT COUNT(procedure_code) FROM procedures;

-- Unique procedure codes
SELECT COUNT(DISTINCT procedure_code) FROM procedures;

-- Top 20 procedures by frequency
SELECT description AS label, COUNT(procedure_code) AS count
FROM procedures
GROUP BY description
ORDER BY COUNT(procedure_code) DESC
LIMIT 20;

-- Per-patient procedure stats
SELECT
  ROUND(CAST(AVG(cnt) AS NUMERIC), 2) AS avg,
  MIN(cnt) AS min,
  MAX(cnt) AS max
FROM (
  SELECT patient_id, COUNT(procedure_code) AS cnt
  FROM procedures
  GROUP BY patient_id
) AS per_patient;
```

### Endpoint Response

```json
{
  "total_procedures": 34981,
  "unique_procedures": 137,
  "per_patient": {"avg": 30.03, "min": 1, "max": 1273},
  "top_procedures": [
    {"name": "Medication Reconciliation (procedure)",                              "value": 5632.0, "tooltip": "Medication Reconciliation (procedure): 5632 (16.1%)"},
    {"name": "Renal dialysis (procedure)",                                        "value": 3389.0, "tooltip": "Renal dialysis (procedure): 3389 (9.69%)"},
    {"name": "Auscultation of the fetal heart",                                   "value": 2705.0, "tooltip": "Auscultation of the fetal heart: 2705 (7.73%)"},
    {"name": "Evaluation of uterine fundal height",                               "value": 2705.0, "tooltip": "Evaluation of uterine fundal height: 2705 (7.73%)"},
    {"name": "Subcutaneous immunotherapy",                                        "value": 1497.0, "tooltip": "Subcutaneous immunotherapy: 1497 (4.28%)"},
    {"name": "Intramuscular injection",                                           "value": 1324.0, "tooltip": "Intramuscular injection: 1324 (3.78%)"},
    {"name": "Electrical cardioversion",                                          "value":  981.0, "tooltip": "Electrical cardioversion: 981 (2.8%)"},
    {"name": "Combined chemotherapy and radiation therapy (procedure)",           "value":  655.0, "tooltip": "Combined chemotherapy and radiation therapy (procedure): 655 (1.87%)"},
    {"name": "Hemoglobin / Hematocrit / Platelet count",                          "value":  602.0, "tooltip": "Hemoglobin / Hematocrit / Platelet count: 602 (1.72%)"},
    {"name": "Colonoscopy",                                                       "value":  527.0, "tooltip": "Colonoscopy: 527 (1.51%)"},
    {"name": "Standard pregnancy test",                                           "value":  474.0, "tooltip": "Standard pregnancy test: 474 (1.36%)"},
    {"name": "Ultrasound scan for fetal viability",                               "value":  474.0, "tooltip": "Ultrasound scan for fetal viability: 474 (1.36%)"},
    {"name": "Depression screening",                                              "value":  468.0, "tooltip": "Depression screening: 468 (1.34%)"},
    {"name": "Hearing examination (procedure)",                                   "value":  328.0, "tooltip": "Hearing examination (procedure): 328 (0.94%)"},
    {"name": "High resolution computed tomography of chest without contrast (procedure)", "value": 328.0},
    {"name": "Throat culture (procedure)",                                        "value":  316.0},
    {"name": "Physical examination of mother",                                    "value":  307.0},
    {"name": "Urine protein test",                                                "value":  307.0},
    {"name": "Urine screening test for diabetes",                                 "value":  307.0},
    {"name": "Gonorrhea infection test",                                          "value":  307.0}
  ]
}
```

---

## 6. Immunizations - `GET /statistics/immunizations`

### SQL Queries

```sql
-- Total immunization records
SELECT COUNT(immunization_code) FROM immunizations;

-- Unique immunization codes
SELECT COUNT(DISTINCT immunization_code) FROM immunizations;

-- Top 15 immunizations by frequency
SELECT description AS label, COUNT(immunization_code) AS count
FROM immunizations
GROUP BY description
ORDER BY COUNT(immunization_code) DESC
LIMIT 15;

-- Per-patient immunization stats
SELECT
  ROUND(CAST(AVG(cnt) AS NUMERIC), 2) AS avg,
  MIN(cnt) AS min,
  MAX(cnt) AS max
FROM (
  SELECT patient_id, COUNT(immunization_code) AS cnt
  FROM immunizations
  GROUP BY patient_id
) AS per_patient;
```

### Endpoint Response

```json
{
  "total_immunizations": 15478,
  "unique_immunizations": 18,
  "per_patient": {"avg": 13.24, "min": 1, "max": 36},
  "top_immunizations": [
    {"name": "Influenza  seasonal  injectable  preservative free", "value": 9385.0, "tooltip": "Influenza  seasonal  injectable  preservative free: 9385 (60.63%)"},
    {"name": "Td (adult) preservative free",                       "value":  830.0, "tooltip": "Td (adult) preservative free: 830 (5.36%)"},
    {"name": "Pneumococcal conjugate PCV 13",                      "value":  661.0, "tooltip": "Pneumococcal conjugate PCV 13: 661 (4.27%)"},
    {"name": "DTaP",                                               "value":  572.0, "tooltip": "DTaP: 572 (3.7%)"},
    {"name": "IPV",                                                "value":  481.0, "tooltip": "IPV: 481 (3.11%)"},
    {"name": "meningococcal MCV4P",                                "value":  432.0, "tooltip": "meningococcal MCV4P: 432 (2.79%)"},
    {"name": "HPV  quadrivalent",                                  "value":  424.0, "tooltip": "HPV  quadrivalent: 424 (2.74%)"},
    {"name": "Hib (PRP-OMP)",                                      "value":  354.0, "tooltip": "Hib (PRP-OMP): 354 (2.29%)"},
    {"name": "Hep B  adolescent or pediatric",                     "value":  352.0, "tooltip": "Hep B  adolescent or pediatric: 352 (2.27%)"},
    {"name": "Hep A  adult",                                       "value":  281.0, "tooltip": "Hep A  adult: 281 (1.82%)"},
    {"name": "zoster",                                             "value":  280.0, "tooltip": "zoster: 280 (1.81%)"},
    {"name": "Hep B  adult",                                       "value":  263.0, "tooltip": "Hep B  adult: 263 (1.7%)"},
    {"name": "MMR",                                                "value":  233.0, "tooltip": "MMR: 233 (1.51%)"},
    {"name": "Hep A  ped/adol  2 dose",                            "value":  230.0, "tooltip": "Hep A  ped/adol  2 dose: 230 (1.49%)"},
    {"name": "varicella",                                          "value":  228.0, "tooltip": "varicella: 228 (1.47%)"}
  ]
}
```

---

## 7. Medications - `GET /statistics/medications`

### SQL Queries

```sql
-- Total medication records
SELECT COUNT(medication_code) FROM medications;

-- Unique medication codes
SELECT COUNT(DISTINCT medication_code) FROM medications;

-- Top 20 medications by frequency
SELECT description AS label, COUNT(medication_code) AS count
FROM medications
GROUP BY description
ORDER BY COUNT(medication_code) DESC
LIMIT 20;

-- Medication duration stats (min, max, avg, median)
SELECT
  ROUND(CAST(MIN(duration_days) AS NUMERIC), 2) AS min_duration,
  ROUND(CAST(MAX(duration_days) AS NUMERIC), 2) AS max_duration,
  ROUND(CAST(AVG(duration_days) AS NUMERIC), 2) AS avg_duration,
  ROUND(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_days) AS NUMERIC), 2) AS median_duration
FROM medications;

-- Active vs Ended
SELECT
  CASE WHEN end_date IS NULL THEN 'Active' ELSE 'Ended' END AS label,
  COUNT(medication_code) AS count
FROM medications
GROUP BY label;

-- Per-patient medication stats
SELECT
  ROUND(CAST(AVG(cnt) AS NUMERIC), 2) AS avg,
  MIN(cnt) AS min,
  MAX(cnt) AS max
FROM (
  SELECT patient_id, COUNT(medication_code) AS cnt
  FROM medications
  GROUP BY patient_id
) AS per_patient;
```

### Endpoint Response

```json
{
  "total_medications": 42989,
  "unique_medications": 131,
  "per_patient": {"avg": 38.83, "min": 1, "max": 3313},
  "duration_stats": {
    "min_duration": -6.0,
    "max_duration": 24090.0,
    "avg_duration": 213.66,
    "median_duration": 147.0
  },
  "active_vs_ended": [
    {"name": "Active", "value": 1895.0,  "tooltip": "Active: 1895 (4.41%)"},
    {"name": "Ended",  "value": 41094.0, "tooltip": "Ended: 41094 (95.59%)"}
  ],
  "top_medications": [
    {"name": "Hydrochlorothiazide 25 MG Oral Tablet",                                                                                  "value": 3954.0},
    {"name": "insulin human  isophane 70 UNT/ML / Regular Insulin  Human 30 UNT/ML Injectable Suspension [Humulin]",                  "value": 3880.0},
    {"name": "1 ML Epoetin Alfa 4000 UNT/ML Injection [Epogen]",                                                                      "value": 3388.0},
    {"name": "Atenolol 50 MG / Chlorthalidone 25 MG Oral Tablet",                                                                     "value": 3347.0},
    {"name": "24 HR Metformin hydrochloride 500 MG Extended Release Oral Tablet",                                                     "value": 2895.0},
    {"name": "amLODIPine 5 MG / Hydrochlorothiazide 12.5 MG / Olmesartan medoxomil 20 MG Oral Tablet",                               "value": 2867.0},
    {"name": "Simvastatin 10 MG Oral Tablet",                                                                                         "value": 2273.0},
    {"name": "120 ACTUAT Fluticasone propionate 0.044 MG/ACTUAT Metered Dose Inhaler",                                                "value": 2072.0},
    {"name": "NDA020503 200 ACTUAT Albuterol 0.09 MG/ACTUAT Metered Dose Inhaler",                                                    "value": 2072.0},
    {"name": "Hydrochlorothiazide 12.5 MG",                                                                                           "value": 1598.0},
    {"name": "Digoxin 0.125 MG Oral Tablet",                                                                                          "value": 1278.0},
    {"name": "Warfarin Sodium 5 MG Oral Tablet",                                                                                      "value": 1278.0},
    {"name": "Nitroglycerin 0.4 MG/ACTUAT Mucosal Spray",                                                                            "value": 1264.0},
    {"name": "Verapamil Hydrochloride 40 MG",                                                                                         "value": 1259.0},
    {"name": "Simvastatin 20 MG Oral Tablet",                                                                                         "value":  948.0},
    {"name": "Amlodipine 5 MG Oral Tablet",                                                                                           "value":  921.0},
    {"name": "Clopidogrel 75 MG Oral Tablet",                                                                                         "value":  904.0},
    {"name": "Acetaminophen 325 MG Oral Tablet",                                                                                      "value":  644.0},
    {"name": "Cisplatin 50 MG Injection",                                                                                             "value":  572.0},
    {"name": "PACLitaxel 100 MG Injection",                                                                                           "value":  541.0}
  ]
}
```

---

## 8. Allergies - `GET /statistics/allergies`

### SQL Queries

```sql
-- Total allergy records
SELECT COUNT(allergy_code) FROM allergies;

-- Unique allergy codes
SELECT COUNT(DISTINCT allergy_code) FROM allergies;

-- Active vs Resolved
SELECT
  CASE WHEN end_date IS NULL THEN 'Active' ELSE 'Resolved' END AS label,
  COUNT(allergy_code) AS count
FROM allergies
GROUP BY label;

-- Top 15 allergies by frequency
SELECT description AS label, COUNT(allergy_code) AS count
FROM allergies
GROUP BY description
ORDER BY COUNT(allergy_code) DESC
LIMIT 15;

-- Per-patient allergy stats
SELECT
  ROUND(CAST(AVG(cnt) AS NUMERIC), 2) AS avg,
  MIN(cnt) AS min,
  MAX(cnt) AS max
FROM (
  SELECT patient_id, COUNT(allergy_code) AS cnt
  FROM allergies
  GROUP BY patient_id
) AS per_patient;
```

### Endpoint Response

```json
{
  "total_allergies": 597,
  "unique_allergies": 15,
  "per_patient": {"avg": 4.23, "min": 1, "max": 10},
  "active_vs_resolved": [
    {"name": "Active",   "value": 533.0, "tooltip": "Active: 533 (89.28%)"},
    {"name": "Resolved", "value":  64.0, "tooltip": "Resolved: 64 (10.72%)"}
  ],
  "top_allergies": [
    {"name": "Allergy to mould",       "value": 81.0, "tooltip": "Allergy to mould: 81 (13.57%)"},
    {"name": "Dander (animal) allergy","value": 77.0, "tooltip": "Dander (animal) allergy: 77 (12.9%)"},
    {"name": "Allergy to tree pollen", "value": 63.0, "tooltip": "Allergy to tree pollen: 63 (10.55%)"},
    {"name": "House dust mite allergy","value": 61.0, "tooltip": "House dust mite allergy: 61 (10.22%)"},
    {"name": "Allergy to grass pollen","value": 60.0, "tooltip": "Allergy to grass pollen: 60 (10.05%)"},
    {"name": "Shellfish allergy",      "value": 41.0, "tooltip": "Shellfish allergy: 41 (6.87%)"},
    {"name": "Allergy to bee venom",   "value": 33.0, "tooltip": "Allergy to bee venom: 33 (5.53%)"},
    {"name": "Allergy to nut",         "value": 31.0, "tooltip": "Allergy to nut: 31 (5.19%)"},
    {"name": "Allergy to fish",        "value": 30.0, "tooltip": "Allergy to fish: 30 (5.03%)"},
    {"name": "Allergy to peanuts",     "value": 25.0, "tooltip": "Allergy to peanuts: 25 (4.19%)"},
    {"name": "Allergy to wheat",       "value": 25.0, "tooltip": "Allergy to wheat: 25 (4.19%)"},
    {"name": "Latex allergy",          "value": 24.0, "tooltip": "Latex allergy: 24 (4.02%)"},
    {"name": "Allergy to eggs",        "value": 20.0, "tooltip": "Allergy to eggs: 20 (3.35%)"},
    {"name": "Allergy to dairy product","value":18.0, "tooltip": "Allergy to dairy product: 18 (3.02%)"},
    {"name": "Allergy to soya",        "value":  8.0, "tooltip": "Allergy to soya: 8 (1.34%)"}
  ]
}
```

---

## 9. Providers - `GET /statistics/providers`

### SQL Queries

```sql
-- Total providers
SELECT COUNT(provider_id) FROM providers;

-- Unique specialities
SELECT COUNT(DISTINCT speciality) FROM providers;

-- Gender distribution
SELECT gender AS label, COUNT(provider_id) AS count
FROM providers
GROUP BY gender
ORDER BY COUNT(provider_id) DESC;

-- Top 15 specialities
SELECT speciality AS label, COUNT(provider_id) AS count
FROM providers
GROUP BY speciality
ORDER BY COUNT(provider_id) DESC
LIMIT 15;

-- Top 10 cities by provider count
SELECT city AS label, COUNT(provider_id) AS count
FROM providers
GROUP BY city
ORDER BY COUNT(provider_id) DESC
LIMIT 10;

-- Provider utilization stats
SELECT
  MIN(utilization) AS min,
  MAX(utilization) AS max,
  ROUND(CAST(AVG(utilization) AS NUMERIC), 2) AS avg,
  ROUND(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY utilization) AS NUMERIC), 2) AS median
FROM providers;
```

### Endpoint Response

```json
{
  "total_providers": 5855,
  "unique_specialities": 69,
  "utilization": {"min": 0, "max": 4828, "avg": 24.27, "median": 0.0},
  "gender": [
    {"name": "F", "value": 3062.0, "tooltip": "F: 3062 (52.3%)"},
    {"name": "M", "value": 2793.0, "tooltip": "M: 2793 (47.7%)"}
  ],
  "top_specialities": [
    {"name": "GENERAL PRACTICE",                  "value": 1120.0, "tooltip": "GENERAL PRACTICE: 1120 (19.13%)"},
    {"name": "INTERNAL MEDICINE",                 "value":  608.0, "tooltip": "INTERNAL MEDICINE: 608 (10.38%)"},
    {"name": "NURSE PRACTITIONER",                "value":  511.0, "tooltip": "NURSE PRACTITIONER: 511 (8.73%)"},
    {"name": "CLINICAL SOCIAL WORKER",            "value":  367.0, "tooltip": "CLINICAL SOCIAL WORKER: 367 (6.27%)"},
    {"name": "PHYSICIAN ASSISTANT",               "value":  311.0, "tooltip": "PHYSICIAN ASSISTANT: 311 (5.31%)"},
    {"name": "PHYSICAL THERAPY",                  "value":  308.0, "tooltip": "PHYSICAL THERAPY: 308 (5.26%)"},
    {"name": "FAMILY PRACTICE",                   "value":  279.0, "tooltip": "FAMILY PRACTICE: 279 (4.77%)"},
    {"name": "CLINICAL PSYCHOLOGIST",             "value":  204.0, "tooltip": "CLINICAL PSYCHOLOGIST: 204 (3.48%)"},
    {"name": "DIAGNOSTIC RADIOLOGY",              "value":  171.0, "tooltip": "DIAGNOSTIC RADIOLOGY: 171 (2.92%)"},
    {"name": "CHIROPRACTIC",                      "value":  148.0, "tooltip": "CHIROPRACTIC: 148 (2.53%)"},
    {"name": "OPTOMETRY",                         "value":  139.0, "tooltip": "OPTOMETRY: 139 (2.37%)"},
    {"name": "PSYCHIATRY",                        "value":  125.0, "tooltip": "PSYCHIATRY: 125 (2.13%)"},
    {"name": "CARDIOVASCULAR DISEASE (CARDIOLOGY)","value": 100.0, "tooltip": "CARDIOVASCULAR DISEASE (CARDIOLOGY): 100 (1.71%)"},
    {"name": "OBSTETRICS/GYNECOLOGY",             "value":   93.0, "tooltip": "OBSTETRICS/GYNECOLOGY: 93 (1.59%)"},
    {"name": "GASTROENTEROLOGY",                  "value":   88.0, "tooltip": "GASTROENTEROLOGY: 88 (1.5%)"}
  ],
  "top_cities": [
    {"name": "SOMERVILLE", "value": 453.0, "tooltip": "SOMERVILLE: 453 (7.74%)"},
    {"name": "PEABODY",    "value": 382.0, "tooltip": "PEABODY: 382 (6.52%)"},
    {"name": "HAVERHILL",  "value": 342.0, "tooltip": "HAVERHILL: 342 (5.84%)"},
    {"name": "CAMBRIDGE",  "value": 274.0, "tooltip": "CAMBRIDGE: 274 (4.68%)"},
    {"name": "SOMERSET",   "value": 152.0, "tooltip": "SOMERSET: 152 (2.6%)"},
    {"name": "WORCESTER",  "value": 147.0, "tooltip": "WORCESTER: 147 (2.51%)"},
    {"name": "FAIRHAVEN",  "value": 132.0, "tooltip": "FAIRHAVEN: 132 (2.25%)"},
    {"name": "HYANNIS",    "value": 115.0, "tooltip": "HYANNIS: 115 (1.96%)"},
    {"name": "BOSTON",     "value": 111.0, "tooltip": "BOSTON: 111 (1.9%)"},
    {"name": "MELROSE",    "value": 102.0, "tooltip": "MELROSE: 102 (1.74%)"}
  ]
}
```

---

## 10. Organizations - `GET /statistics/organizations`

### SQL Queries

```sql
-- Total organizations
SELECT COUNT(organization_id) FROM organizations;

-- Top 10 cities by organization count
SELECT city AS label, COUNT(organization_id) AS count
FROM organizations
GROUP BY city
ORDER BY COUNT(organization_id) DESC
LIMIT 10;

-- Organization utilization stats
SELECT
  MIN(utilization) AS min,
  MAX(utilization) AS max,
  ROUND(CAST(AVG(utilization) AS NUMERIC), 2) AS avg,
  ROUND(CAST(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY utilization) AS NUMERIC), 2) AS median
FROM organizations;
```

### Endpoint Response

```json
{
  "total_organizations": 1119,
  "utilization": {"min": 1, "max": 4828, "avg": 127.0, "median": 43.0},
  "top_cities": [
    {"name": "BROOKLINE",      "value": 32.0, "tooltip": "BROOKLINE: 32 (2.86%)"},
    {"name": "CAMBRIDGE",      "value": 29.0, "tooltip": "CAMBRIDGE: 29 (2.59%)"},
    {"name": "BOSTON",         "value": 25.0, "tooltip": "BOSTON: 25 (2.23%)"},
    {"name": "MILTON",         "value": 18.0, "tooltip": "MILTON: 18 (1.61%)"},
    {"name": "SOMERVILLE",     "value": 17.0, "tooltip": "SOMERVILLE: 17 (1.52%)"},
    {"name": "SPRINGFIELD",    "value": 15.0, "tooltip": "SPRINGFIELD: 15 (1.34%)"},
    {"name": "WORCESTER",      "value": 14.0, "tooltip": "WORCESTER: 14 (1.25%)"},
    {"name": "QUINCY",         "value": 13.0, "tooltip": "QUINCY: 13 (1.16%)"},
    {"name": "LOWELL",         "value": 13.0, "tooltip": "LOWELL: 13 (1.16%)"},
    {"name": "WEST SPRINGFIELD","value": 13.0, "tooltip": "WEST SPRINGFIELD: 13 (1.16%)"}
  ]
}
```
