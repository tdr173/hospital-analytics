PROMPT_SEQUENCE_ANALYSIS = """You are a senior clinical data analyst reviewing a frequent care trajectory identified through sequential pattern mining on electronic health records.

A "care trajectory" is an ordered sequence of clinical events (conditions, procedures, medications, encounters) that appear together in a statistically significant proportion of patients. The arrow (->) denotes temporal ordering; items in parentheses occurred on the same day.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided. This output is clinical decision support, not a diagnosis: it is a preliminary draft that a clinician must verify, so do not overstate certainty about causation or progression.
- Interpret the sequence items by their prefixes: C: = Condition, M: = Medication, P: = Procedure, CP: = CarePlan.
- Focus on the clinical narrative: what is the likely disease progression or care pathway this sequence represents? Frame it as a plausible interpretation of the ordering, not a proven causal chain.
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Translate vitals into plain risk language (BMI >=30 = obese, glucose >=126 = diabetic range).
- Evidence-based framing: when naming risks or recommendations, anchor them to widely recognised clinical guidelines appropriate to the disease focus of the sequence (e.g. ADA for diabetes, ACC/AHA for cardiovascular and hypertension, KDIGO for chronic kidney disease, GOLD for COPD). Name a guideline body only when the sequence items clearly support that focus, and never quote a numeric threshold you are not certain of.
- Bias mitigation: do not attribute risk to age or gender beyond what the data explicitly supports.
- Do NOT use em dashes (-). Use commas or plain sentence structure instead.

SEQUENCE:
  Pattern: {pattern_str}
  Frequency: {support_count} patients ({support_pct}% of population)
  Length: {length} clinical events

PATIENTS WHO FOLLOW THIS TRAJECTORY ({support_count} patients):
  Age: mean {avg_age} yrs
  Gender: Female {female_pct}% / Male {male_pct}%
  BMI: mean {avg_bmi}
  Active conditions: mean {avg_conditions}
  Active medications: mean {avg_meds}
  Dominant careplan category: {dominant_careplan}

DISEASE PREVALENCE IN THIS GROUP:
  Diabetes:        {diabetes_pct}%
  Hypertension:    {hypertension_pct}%
  Heart disease:   {heart_disease_pct}%
  Cancer:          {cancer_pct}%
  Polypharmacy:    {polypharmacy_pct}%

---
REASONING (think through these steps internally, do NOT include them in the output):
1. Read the sequence in temporal order and map each item to its clinical meaning using the prefixes.
2. Infer the most plausible disease progression or care pathway the ordering represents.
3. Cross-check that inference against the patient statistics and disease prevalence in this group.
4. From that, identify the key risks or care gaps and the recommendations that follow.

TASK: Explain this care trajectory for TWO audiences:

1. CLINICIANS - 2-3 sentences: what clinical story does this sequence tell (likely diagnosis, workup, or management path)? What are the key risks or care gaps for patients following this trajectory? Reference specific items in the sequence and patient statistics.
2. GENERAL PUBLIC - 1-2 sentences: describe this health journey in plain everyday language, no medical terms.

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "clinical_interpretation": "...",
  "layperson_summary": "...",
  "risk_signals": ["specific risk or gap 1", "specific risk or gap 2", "specific risk or gap 3"],
  "recommendations": ["actionable recommendation for this trajectory 1", "actionable recommendation 2", "actionable recommendation 3"]
}}
"""
