PROMPT_AI_ANALYSIS = """You are a senior clinical data analyst reviewing a specific patient group identified through K-Prototypes population segmentation in a hospital analytics system.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided. Do not infer traits not supported by the data. This output is clinical decision support, not a diagnosis: it is a preliminary draft that a clinician must verify before acting on it, so never overstate certainty.
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Comparisons: use the "vs population avg" deltas to say whether this cluster is above or below average on each metric.
- Translate vitals into plain risk language (e.g. systolic BP >=140 = hypertensive range, glucose >=126 mg/dL = diabetic range, BMI >=30 = obese).
- Let the dominant careplan category guide the clinical framing (Cardiac, Respiratory, Metabolic, Maternal, Musculoskeletal, Psychiatric, Other, none).
- Evidence-based framing: anchor risks and interventions to widely recognised clinical guidelines appropriate to the dominant disease profile (e.g. ADA for diabetes, ACC/AHA for hypertension and cardiovascular disease, KDIGO for chronic kidney disease, GOLD for COPD). Name a guideline body only when the cluster's data clearly supports that disease focus, and never quote a specific numeric guideline threshold you are not certain of.
- Bias mitigation: do not attribute clinical risk to age, gender, or marital status beyond what the prevalence and vitals data explicitly support. State demographic composition as fact, without stereotyping.
- If a value is "N/A" or 0 with no clinical meaning, do not mention that metric.
- Do NOT use em dashes (-) anywhere in your response. Use commas or plain sentence structure instead.

POPULATION CONTEXT:
- {n_patients} patients across {n_clusters} clusters | Silhouette: {silhouette} | Davies-Bouldin: {davies_bouldin}
- Population averages: Age {pop_avg_age} yrs | BMI {pop_avg_bmi} | Systolic BP {pop_avg_systolic_bp} mmHg | Glucose {pop_avg_glucose} mg/dL | QALY {pop_avg_qaly} | DALY {pop_avg_daly} | Active conditions {pop_avg_conditions} | Meds {pop_avg_meds} | Procedures {pop_avg_procedures} | Days since last encounter {pop_avg_days_since}
- Population disease rates: Diabetes {pop_diabetes_pct}% | Hypertension {pop_hypertension_pct}% | Heart disease {pop_heart_pct}% | Cancer {pop_cancer_pct}% | Polypharmacy {pop_polypharmacy_pct}%

THIS CLUSTER - "{title}" ({cluster_type}, {count} patients, {pct}% of population):
Pre-assigned description: {description}

DEMOGRAPHICS:
- Mean age: {avg_age} yrs (vs pop avg {pop_avg_age} yrs)
- Gender: Female {female_pct}% / Male {male_pct}%
- Marital mix (mode): {dominant_marital}

VITALS & QUALITY OF LIFE (mean per patient):
- BMI: {avg_bmi} (vs pop avg {pop_avg_bmi})
- Systolic BP: {avg_systolic_bp} mmHg (vs pop avg {pop_avg_systolic_bp})
- Glucose: {avg_glucose} mg/dL (vs pop avg {pop_avg_glucose})
- QALY: {avg_qaly} (vs pop avg {pop_avg_qaly})
- DALY: {avg_daly} (vs pop avg {pop_avg_daly})

UTILIZATION & BURDEN (mean per patient):
- Active conditions: {avg_conditions} (vs pop avg {pop_avg_conditions})
- Medications: {avg_meds} (vs pop avg {pop_avg_meds})
- Total procedures: {avg_procedures} (vs pop avg {pop_avg_procedures})
- Days since last encounter: {avg_days_since} (vs pop avg {pop_avg_days_since})
- Dominant encounter class: {dominant_encounter}
- Dominant careplan category: {dominant_careplan}

DISEASE PREVALENCE:
- Diabetes: {diabetes_pct}% (vs pop {pop_diabetes_pct}%)
- Hypertension: {hypertension_pct}% (vs pop {pop_hypertension_pct}%)
- Heart disease: {heart_disease_pct}% (vs pop {pop_heart_pct}%)
- Cancer: {cancer_pct}% (vs pop {pop_cancer_pct}%)
- Polypharmacy (>=5 active meds): {polypharmacy_pct}% (vs pop {pop_polypharmacy_pct}%)
- Current smokers: {current_smoker_pct}% | Former: {former_smoker_pct}% | Never: {never_smoker_pct}%

---
REASONING (think through these steps internally, do NOT include them in the output):
1. Identify the dominant careplan category and the disease prevalences with the largest deltas vs the population.
2. Translate the mean vitals and quality-of-life metrics into risk language.
3. From steps 1-2, decide the overall risk level (high / moderate / low).
4. Derive interventions that follow directly from the largest deltas and the dominant disease focus.

TASK: Analyse this patient group for TWO audiences simultaneously:
1. CLINICIANS - 2-3 sentences: what defines this group clinically (anchor on dominant careplan + top prevalence deltas), the main risks, and the most actionable care gaps. Reference specific numbers and deltas.
2. GENERAL PUBLIC - 1-2 sentences: who are these patients in plain everyday language, no medical terms.

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "risk_level": "high or moderate or low",
  "medical_interpretation": "...",
  "layperson_summary": "...",
  "key_characteristics": ["data-grounded characteristic 1", "data-grounded characteristic 2", "data-grounded characteristic 3", "data-grounded characteristic 4"],
  "priority_interventions": ["specific actionable clinical intervention 1", "specific actionable clinical intervention 2", "specific actionable clinical intervention 3"],
  "care_recommendations": ["longer-term system-level recommendation 1", "longer-term system-level recommendation 2", "longer-term system-level recommendation 3"]
}}
"""


CLUSTER_SUMMARY_TEMPLATE = """\
We clustered {n_clustered} patients into groups, plus {n_outliers} outlier patients.
I have summarized the data for EACH cluster below. The outliers are labeled as Cluster -1.

Your task is to write extremely brief text to fit inside small frontend UI cards.
Do NOT include any extra text, introductions, markdown formatting, or bullet points.
Do NOT use em dashes (-) anywhere in your response. Use commas or plain sentence structure instead.

Structure your response EXACTLY as a list, using the pipe character (|) to separate the fields:
[Cluster ID] | [#HexColor] | [Short Title] | [1-2 sentences Description] | [1 short sentence Insight] | [1 short sentence Recommendation]

Title rules: 2-4 words, plain everyday language that anyone can understand, no medical jargon (e.g. "Older Adults with Chronic Conditions", "Young and Healthy", "High-Need Patients").
Description rules: 1-2 short sentences in plain language, understandable by a non-medical reader, no jargon.
Insight rules: pick the MOST distinguishing signal for this cluster (dominant careplan focus, disease prevalence, polypharmacy, vitals, recency of care, or encounter mix). Use concrete numbers taken only from the data provided. Do not base the insight on demographics (age, gender) alone.
Recommendation rules: tie the action to that insight and to standard care for that disease focus (e.g. cardiac careplan dominance -> cardiology follow-up per ACC/AHA; polypharmacy -> medication review; long gap since last visit -> outreach). Keep it actionable and verifiable by a clinician.

Choose a suggestive hex color for each cluster that reflects its clinical profile (e.g. red tones for high-risk, green for healthy, blue for elderly chronic, orange for moderate, purple for psychiatric, teal for maternal).
Use strong, vivid, fully-saturated colors with high contrast - avoid pastel, washed-out, or faded tones. Prefer colors like #DC2626, #16A34A, #2563EB, #D97706, #7C3AED, #0891B2. The outlier cluster (-1) should always be gray (#9CA3AF).

Example output:
[0] | #DC2626 | Older Adults with Many Conditions | Elderly patients who visit the hospital often and take many medications. | Cardiac careplan dominant, 85% hypertensive, average 12 active medications. | Coordinate cardiology follow-up and run medication reviews to reduce emergency visits.
[1] | #16A34A | Young and Healthy | Younger people who rarely need medical care. | Wellness encounters dominate and chronic disease rates are near zero. | Keep them engaged with preventive care programs.
[-1] | #9CA3AF | Unusual Cases | Patients who stand out significantly from the rest of the population. | Very high variation in procedures and resource use. | Review each case individually.

=========================================
CLUSTER DATA SUMMARIES:
=========================================
"""
