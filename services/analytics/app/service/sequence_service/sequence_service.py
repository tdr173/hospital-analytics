from typing import Optional

from repository import SequenceRepository
from service._helpers import parse_ai_json
from service.lllm_sql_agent_service.llm_models import ask_ai


PROMPT_SEQUENCE_ANALYSIS = """You are a senior clinical data analyst reviewing a frequent care trajectory identified through sequential pattern mining on electronic health records.

A "care trajectory" is an ordered sequence of clinical events (conditions, procedures, medications, encounters) that appear together in a statistically significant proportion of patients. The arrow (->) denotes temporal ordering; items in parentheses occurred on the same day.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided.
- Interpret the sequence items by their prefixes: C: = Condition, M: = Medication, P: = Procedure, CP: = CarePlan.
- Focus on the clinical narrative: what is the likely disease progression or care pathway this sequence represents?
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Translate vitals into plain risk language (BMI >=30 = obese, glucose >=126 = diabetic range).
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


class SequenceService:
    def __init__(self, repo: SequenceRepository):
        self.repo = repo

    def get_resources(self):
        return self.repo.get_resources()

    def get_sequences(
        self,
        search: Optional[str] = None,
        min_length: int = 1,
        sort_by: str = "support",
        sort_type: str = "desc",
        page: int = 1,
        rows: int = 8,
    ):
        return self.repo.get_sequences(
            search=search,
            min_length=min_length,
            sort_by=sort_by,
            sort_type=sort_type,
            page=page,
            rows=rows,
        )

    def get_patient_continuations(
        self,
        patient_id: str,
        last_n: int = 3,
        page: int = 1,
        page_size: int = 20,
    ):
        return self.repo.get_patient_continuations(
            patient_id=patient_id,
            last_n=last_n,
            page=page,
            page_size=page_size,
        )

    def get_ai_analysis(self, pattern_id: int) -> dict:
        cached = self.repo.get_pattern_ai_analysis(pattern_id)
        if cached:
            return cached

        # Row-lock the pattern to serialize concurrent requests for the same id.
        locked = self.repo.lock_pattern_ai_analysis(pattern_id)
        if locked:
            return locked

        ctx = self.repo.get_pattern_ai_context(pattern_id)
        prompt = PROMPT_SEQUENCE_ANALYSIS.format(
            **ctx["pattern"],
            **ctx["patient_stats"],
        )

        analysis = parse_ai_json(ask_ai(prompt))
        self.repo.save_pattern_ai_analysis(pattern_id, analysis)
        return analysis
