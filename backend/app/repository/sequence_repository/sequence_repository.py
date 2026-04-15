import json
import re
from sqlalchemy import func, case, cast, Numeric
from sqlalchemy.orm import Session
from domain import (
    PrefixSpanPatternModel,
    PrefixSpanPatientPatternModel,
    ClusterPatientModel,
)
from service.lllm_sql_agent_service.llm_models import ask_ai


PROMPT_SEQUENCE_ANALYSIS = """You are a senior clinical data analyst reviewing a frequent care trajectory identified through sequential pattern mining on electronic health records.

A "care trajectory" is an ordered sequence of clinical events (conditions, procedures, medications, encounters) that appear together in a statistically significant proportion of patients. The arrow (->) denotes temporal ordering; items in parentheses occurred on the same day.

IMPORTANT RULES:
- Base every claim strictly on the numbers provided.
- Interpret the sequence items by their prefixes: C: = Condition, P: = Procedure, M: = Medication, E: = Encounter type.
- Focus on the clinical narrative: what is the likely disease progression or care pathway this sequence represents?
- Gender: describe as "balanced" if 40-60%, "more female/male" if 60-70%, "predominantly female/male" only if >70%.
- Translate vitals into plain risk language (BMI >=30 = obese, glucose >=126 = diabetic range).
- Do NOT use em dashes (—). Use commas or plain sentence structure instead.

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


class SequenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_sequence_ai_analysis(self, pattern_id: int) -> dict:
        pattern = self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.id == pattern_id
        ).first()
        if not pattern:
            raise ValueError(f"Pattern {pattern_id} not found")

        if pattern.ai_analysis:
            return pattern.ai_analysis

        # Aggregate features over all patients who follow this trajectory,
        # joining the pre-computed cluster_patient.features JSONB.
        def avg_feat(feature, decimals=1):
            return func.round(
                func.avg(cast(ClusterPatientModel.features[feature].astext, Numeric)),
                decimals,
            )

        def flag_pct(feature, value):
            return func.round(
                100.0 * func.sum(case(
                    (ClusterPatientModel.features[feature].astext == value, 1),
                    else_=0,
                )) / func.nullif(func.count(), 0),
                1,
            )

        stats = (
            self.db.query(
                func.count().label("patient_count"),
                avg_feat("age").label("avg_age"),
                avg_feat("avg_bmi", 1).label("avg_bmi"),
                avg_feat("total_medications").label("avg_meds"),
                avg_feat("active_conditions_count").label("avg_conditions"),
                flag_pct("gender", "F").label("female_pct"),
                flag_pct("gender", "M").label("male_pct"),
                flag_pct("has_diabetes", "Yes").label("diabetes_pct"),
                flag_pct("has_hypertension", "Yes").label("hypertension_pct"),
                flag_pct("has_heart_disease", "Yes").label("heart_disease_pct"),
                flag_pct("has_cancer", "Yes").label("cancer_pct"),
                flag_pct("is_polypharmacy", "Yes").label("polypharmacy_pct"),
                func.mode().within_group(
                    ClusterPatientModel.features["dominant_careplan"].astext
                ).label("dominant_careplan"),
            )
            .select_from(ClusterPatientModel)
            .join(
                PrefixSpanPatientPatternModel,
                PrefixSpanPatientPatternModel.patient_id == ClusterPatientModel.patient_id,
            )
            .filter(
                PrefixSpanPatientPatternModel.pattern_id == pattern_id,
                ClusterPatientModel.is_outlier == False,
            )
            .first()
        )

        s = stats._asdict() if stats else {}

        def v(key):
            val = s.get(key)
            return val if val is not None else "N/A"

        prompt = PROMPT_SEQUENCE_ANALYSIS.format(
            pattern_str=pattern.pattern_str,
            support_count=pattern.support_count,
            support_pct=pattern.support_pct,
            length=pattern.length,
            avg_age=v("avg_age"),
            avg_bmi=v("avg_bmi"),
            avg_meds=v("avg_meds"),
            avg_conditions=v("avg_conditions"),
            female_pct=v("female_pct"),
            male_pct=v("male_pct"),
            diabetes_pct=v("diabetes_pct"),
            hypertension_pct=v("hypertension_pct"),
            heart_disease_pct=v("heart_disease_pct"),
            cancer_pct=v("cancer_pct"),
            polypharmacy_pct=v("polypharmacy_pct"),
            dominant_careplan=v("dominant_careplan"),
        )

        raw = ask_ai(prompt)
        analysis = _parse_ai_json(raw)

        self.db.query(PrefixSpanPatternModel).filter(
            PrefixSpanPatternModel.id == pattern_id
        ).update({"ai_analysis": analysis}, synchronize_session="fetch")
        self.db.commit()

        return analysis


def _parse_ai_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", text, flags=re.DOTALL)
    return json.loads(text.strip())
