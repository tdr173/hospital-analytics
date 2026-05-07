from sqlalchemy import func, case

from domain.models.patient_model import PatientModel
from domain.models.provider_model import ProviderModel


def _name_col(model, label: str):
    first = func.regexp_replace(model.first_name, '[0-9]', '', 'g')
    last = func.regexp_replace(model.last_name, '[0-9]', '', 'g')
    return case(
        (model.first_name == model.last_name, first),
        else_=first + ' ' + last,
    ).label(label)


def patient_name_col(label: str = "patient_name"):
    return _name_col(PatientModel, label)


def provider_name_col(label: str = "provider_name"):
    return _name_col(ProviderModel, label)
