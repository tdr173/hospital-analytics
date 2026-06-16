from prompts.dashboard import PERSONAL_SUMMARY_SYSTEM, PRACTICE_SUMMARY_SYSTEM
from service.lllm_sql_agent_service.llm_models import ask_ai


def personal_summary(patient_data: dict) -> str:
    return ask_ai(PERSONAL_SUMMARY_SYSTEM.format(patient_data=patient_data))


def practice_summary(practice_data: dict) -> str:
    period = practice_data.get("period", "the last month")
    return ask_ai(
        PRACTICE_SUMMARY_SYSTEM.format(practice_data=practice_data, period=period)
    )
