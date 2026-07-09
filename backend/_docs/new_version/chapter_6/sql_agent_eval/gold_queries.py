QUERIES = [
    # -- Demographics --
    {
        "question": "How many patients are in the database?",
        "sql": "SELECT COUNT(*) AS n FROM patient",
    },
    {
        "question": "How many male patients and how many female patients are there?",
        "sql": "SELECT gender, COUNT(*) AS n FROM patient GROUP BY gender ORDER BY gender",
    },
    {
        "question": "What is the average age of the patients?",
        "sql": "SELECT ROUND(AVG(age)::numeric, 1) AS avg_age FROM patient",
    },
    {
        "question": "How many patients are older than 70?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE age > 70",
    },
    {
        "question": "How many patients have died?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE deathdate IS NOT NULL",
    },
    {
        "question": "Which city has the most patients?",
        "sql": "SELECT city, COUNT(*) AS n FROM patient GROUP BY city ORDER BY n DESC LIMIT 1",
    },
    {
        "question": "How many patients are divorced?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE marital = 'D'",
    },
    {
        "question": "How many patients identify as black race?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE race = 'black'",
    },
    {
        "question": "What is the age of the oldest patient in the database?",
        "sql": "SELECT MAX(age) AS max_age FROM patient",
    },
    {
        "question": "How many patients are under 18 years old?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE age < 18",
    },
    # -- Conditions --
    {
        "question": "How many distinct patients have a condition described as Gingivitis (disorder)?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM condition WHERE description = 'Gingivitis (disorder)'",
    },
    {
        "question": "What is the most common condition recorded in the database?",
        "sql": "SELECT description, COUNT(*) AS n FROM condition GROUP BY description ORDER BY n DESC LIMIT 1",
    },
    {
        "question": "How many distinct patients have Normal pregnancy recorded as a condition?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM condition WHERE description = 'Normal pregnancy (finding)'",
    },
    {
        "question": "How many distinct patients have more than 20 condition records each?",
        "sql": "SELECT COUNT(*) AS n FROM (SELECT patient_id FROM condition GROUP BY patient_id HAVING COUNT(*) > 20) t",
    },
    # -- Medications --
    {
        "question": "How many distinct patients are prescribed lisinopril 10 MG Oral Tablet?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM medication WHERE description = 'lisinopril 10 MG Oral Tablet'",
    },
    {
        "question": "What is the most frequently prescribed medication?",
        "sql": "SELECT description, COUNT(*) AS n FROM medication GROUP BY description ORDER BY n DESC LIMIT 1",
    },
    {
        "question": "How many medication records reference a Metformin extended release tablet?",
        "sql": "SELECT COUNT(*) AS n FROM medication WHERE description LIKE '%Metformin%'",
    },
    {
        "question": "How many distinct patients take both lisinopril 10 MG Oral Tablet and Hydrochlorothiazide 25 MG Oral Tablet?",
        "sql": (
            "SELECT COUNT(*) AS n FROM ("
            "SELECT patient_id FROM medication WHERE description = 'lisinopril 10 MG Oral Tablet' "
            "INTERSECT "
            "SELECT patient_id FROM medication WHERE description = 'Hydrochlorothiazide 25 MG Oral Tablet'"
            ") t"
        ),
    },
    # -- Procedures --
    {
        "question": "How many distinct patients underwent renal dialysis?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM procedure WHERE description = 'Renal dialysis (procedure)'",
    },
    {
        "question": "What is the most common procedure performed?",
        "sql": "SELECT description, COUNT(*) AS n FROM procedure GROUP BY description ORDER BY n DESC LIMIT 1",
    },
    # -- Immunizations --
    {
        "question": "How many distinct patients received the trivalent influenza vaccine?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM immunization WHERE description = 'Influenza  split virus  trivalent  PF'",
    },
    {
        "question": "How many distinct patients received a 30 mcg mRNA COVID-19 vaccine dose?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM immunization WHERE description = 'COVID-19  mRNA  LNP-S  PF  30 mcg/0.3 mL dose'",
    },
    {
        "question": "What is the most administered immunization?",
        "sql": "SELECT description, COUNT(*) AS n FROM immunization GROUP BY description ORDER BY n DESC LIMIT 1",
    },
    # -- Allergies --
    {
        "question": "How many distinct patients are allergic to aspirin?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM allergy WHERE description = 'Aspirin'",
    },
    {
        "question": "What is the most common recorded allergy?",
        "sql": "SELECT description, COUNT(*) AS n FROM allergy GROUP BY description ORDER BY n DESC LIMIT 1",
    },
    {
        "question": "How many patients have no recorded allergies at all?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE patient_id NOT IN (SELECT DISTINCT patient_id FROM allergy)",
    },
    # -- Care plans --
    {
        "question": "How many care plans have been recorded in total?",
        "sql": "SELECT COUNT(*) AS n FROM careplan",
    },
    {
        "question": "What is the average duration in days of care plans that have already ended?",
        "sql": "SELECT ROUND(AVG(duration_days)::numeric, 1) AS avg_days FROM careplan WHERE end_date IS NOT NULL",
    },
    # -- Observations --
    {
        "question": "What is the average systolic blood pressure recorded across all observations?",
        "sql": "SELECT ROUND(AVG(value_numeric)::numeric, 1) AS avg_sbp FROM observation WHERE description = 'Systolic Blood Pressure'",
    },
    {
        "question": "What is the highest heart rate ever recorded in the observations?",
        "sql": "SELECT MAX(value_numeric) AS max_hr FROM observation WHERE description = 'Heart rate'",
    },
    {
        "question": "How many distinct patients have at least one BMI observation showing obesity (30 or above)?",
        "sql": "SELECT COUNT(DISTINCT patient_id) AS n FROM observation WHERE description = 'Body mass index (BMI) [Ratio]' AND value_numeric >= 30",
    },
    # -- Encounters --
    {
        "question": "How many encounters are classified as emergency?",
        "sql": "SELECT COUNT(*) AS n FROM encounter WHERE encounter_class = 'emergency'",
    },
    {
        "question": "What is the average duration, in hours, of inpatient encounters?",
        "sql": "SELECT ROUND((AVG(duration) / 60.0)::numeric, 2) AS avg_hours FROM encounter WHERE encounter_class = 'inpatient'",
    },
    {
        "question": "How many encounters took place in 2020?",
        "sql": "SELECT COUNT(*) AS n FROM encounter WHERE EXTRACT(YEAR FROM start_date) = 2020",
    },
    {
        "question": "Which patient has the highest number of encounters, and how many?",
        "sql": (
            "SELECT p.first_name, p.last_name, t.n FROM ("
            "SELECT patient_id, COUNT(*) AS n FROM encounter GROUP BY patient_id ORDER BY n DESC LIMIT 1"
            ") t JOIN patient p ON p.patient_id = t.patient_id"
        ),
    },
    # -- Providers / organizations --
    {
        "question": "How many providers work at the hospital?",
        "sql": "SELECT COUNT(*) AS n FROM provider",
    },
    {
        "question": "What is the name of the hospital organization in the database?",
        "sql": "SELECT name FROM organization LIMIT 1",
    },
    {
        "question": "How many male providers and how many female providers are there?",
        "sql": "SELECT gender, COUNT(*) AS n FROM provider GROUP BY gender ORDER BY gender",
    },
    {
        "question": "Which provider has the most encounters recorded?",
        "sql": "SELECT first_name, last_name, encounters FROM provider ORDER BY encounters DESC LIMIT 1",
    },
    # -- Clusters --
    {
        "question": "How many patient clusters were identified by the clustering pipeline, including the outlier group?",
        "sql": "SELECT COUNT(DISTINCT cluster_label) AS n FROM cluster",
    },
    {
        "question": "What is the title of cluster number 2?",
        "sql": "SELECT title FROM cluster WHERE cluster_label = 2",
    },
    {
        "question": "How many patients belong to the Complex High Need outlier cluster?",
        "sql": (
            "SELECT COUNT(*) AS n FROM cluster_patient cp JOIN cluster c ON c.cluster_label = cp.cluster_label "
            "WHERE c.title = 'Complex High Need'"
        ),
    },
    {
        "question": "Which cluster has the most patients assigned to it?",
        "sql": (
            "SELECT c.title, t.n FROM ("
            "SELECT cluster_label, COUNT(*) AS n FROM cluster_patient GROUP BY cluster_label ORDER BY n DESC LIMIT 1"
            ") t JOIN cluster c ON c.cluster_label = t.cluster_label"
        ),
    },
    {
        "question": "What percentage of patients are outliers, not part of any main cluster?",
        "sql": (
            "SELECT ROUND(100.0 * SUM(CASE WHEN is_outlier THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct "
            "FROM cluster_patient"
        ),
    },
    # -- Sequence mining --
    {
        "question": "What is the most frequent global care sequence pattern that was mined?",
        "sql": "SELECT pattern_str, support_count FROM prefix_span_pattern WHERE cluster_label IS NULL ORDER BY support_count DESC LIMIT 1",
    },
    {
        "question": "How many sequence patterns were mined specifically for cluster 0?",
        "sql": "SELECT COUNT(*) AS n FROM prefix_span_pattern WHERE cluster_label = 0",
    },
    # -- Cross-table / harder queries --
    {
        "question": "How many patients over the age of 65 have been prescribed lisinopril 10 MG Oral Tablet?",
        "sql": (
            "SELECT COUNT(DISTINCT p.patient_id) AS n FROM patient p JOIN medication m ON m.patient_id = p.patient_id "
            "WHERE p.age > 65 AND m.description = 'lisinopril 10 MG Oral Tablet'"
        ),
    },
    {
        "question": "How many distinct patients have both a Viral sinusitis condition and take Acetaminophen 325 MG Oral Tablet?",
        "sql": (
            "SELECT COUNT(*) AS n FROM ("
            "SELECT patient_id FROM condition WHERE description = 'Viral sinusitis (disorder)' "
            "INTERSECT "
            "SELECT patient_id FROM medication WHERE description = 'Acetaminophen 325 MG Oral Tablet [Tylenol]'"
            ") t"
        ),
    },
    {
        "question": "How many male patients living in Houston are there?",
        "sql": "SELECT COUNT(*) AS n FROM patient WHERE city = 'Houston' AND gender = 'M'",
    },
    {
        "question": "What is the average number of medication records per patient?",
        "sql": "SELECT ROUND((SELECT COUNT(*)::numeric FROM medication) / (SELECT COUNT(DISTINCT patient_id)::numeric FROM medication), 2) AS avg_meds",
    },
]

assert len(QUERIES) == 50, len(QUERIES)
