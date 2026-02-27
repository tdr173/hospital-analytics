import os
import pandas as pd
from pathlib import Path

from db import engine as db_engine

dataset_path = Path(__file__).parent.parent.parent.parent / "dataset"

def load_csv(path):
    df = pd.read_csv(path)
    return df


def clear_existing_cleaned_csv(cleaned_name: str):
    if os.path.exists(dataset_path / "cleaned "/ cleaned_name):
        os.remove(dataset_path / "cleaned" / cleaned_name)


def load_patients(engine):
    df = pd.read_csv(dataset_path / "patients.csv")

    keep_cols = {
        "Id": "patient_id",
        "BIRTHDATE": "birthdate",
        "DEATHDATE": "deathdate",
        "FIRST": "first_name",
        "LAST": "last_name",
        "MARITAL": "marital",
        "GENDER": "gender",
        "RACE": "race",
        "ETHNICITY": "ethnicity",
        "CITY": "city",
        "LAT": "latitude",
        "LON": "longitude",
    }

    patients_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    patients_df["marital"] = patients_df["marital"].fillna("S ")

    ref_date = pd.Timestamp.now()
    patients_df["birthdate"] = pd.to_datetime(patients_df["birthdate"])
    patients_df["deathdate"] = pd.to_datetime(patients_df["deathdate"])
    patients_df["age"] = (patients_df["deathdate"].fillna(ref_date) - patients_df["birthdate"]).dt.days // 365

    categorical_cols = ["gender", "race", "ethnicity"]
    for col in categorical_cols:
        if patients_df[col].isnull().any():
            patients_df[col] = patients_df[col].fillna(patients_df[col].mode()[0])

    numerical_cols = ["latitude", "longitude"]
    for col in numerical_cols:
        if patients_df[col].isnull().any():
            patients_df[col] = patients_df[col].fillna(patients_df[col].mode()[0])

    clear_existing_cleaned_csv("cleaned_patients.csv")
    patients_df.to_csv(dataset_path / "cleaned" / "cleaned_patients.csv", index=False)

    patients_df.to_sql(
        name="patient",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(patients_df)} patients.")


def load_organizations(engine):
    df = pd.read_csv(dataset_path / "organizations.csv")

    keep_cols = {
        "Id": "organization_id",
        "NAME": "name",
        "CITY": "city",
        "LAT": "latitude",
        "LON": "longitude",
        "PHONE": "phone",
        "UTILIZATION": "utilization",
    }

    organizations_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    categorical_cols = ["city"]
    for col in categorical_cols:
        if organizations_df[col].isnull().any():
            organizations_df[col] = organizations_df[col].fillna(organizations_df[col].mode()[0])

    numerical_cols = ["latitude", "longitude", "utilization"]
    for col in numerical_cols:
        if organizations_df[col].isnull().any():
            organizations_df[col] = organizations_df[col].fillna(organizations_df[col].median())

    clear_existing_cleaned_csv("cleaned_organizations.csv")
    organizations_df.to_csv(dataset_path / "cleaned" / "cleaned_organizations.csv", index=False)

    organizations_df.to_sql(
        name="organization",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(organizations_df)} organizations.")


def load_providers(engine):
    df = pd.read_csv(dataset_path / "providers.csv")

    keep_cols = {
        "Id": "provider_id",
        "ORGANIZATION": "organization_id",
        "NAME": "name",
        "GENDER": "gender",
        "SPECIALITY": "speciality",
        "CITY": "city",
        "LAT": "latitude",
        "LON": "longitude",
        "UTILIZATION": "utilization",
    }

    providers_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    providers_df["first_name"] = providers_df["name"].str.split(" ").str[0]
    providers_df["last_name"] = providers_df["name"].str.split(" ").str[0]
    providers_df = providers_df.drop(columns=["name"])

    categorical_cols = ["gender", "speciality"]
    for col in categorical_cols:
        if providers_df[col].isnull().any():
            providers_df[col] = providers_df[col].fillna(providers_df[col].mode()[0])

    numerical_cols = ["latitude", "longitude", "utilization"]
    for col in numerical_cols:
        if providers_df[col].isnull().any():
            providers_df[col] = providers_df[col].fillna(providers_df[col].median())

    clear_existing_cleaned_csv("cleaned_providers.csv")
    providers_df.to_csv(dataset_path / "cleaned" / "cleaned_providers.csv", index=False)

    providers_df.to_sql(
        name="provider",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(providers_df)} providers.")


def load_encounters(engine):
    df = pd.read_csv(dataset_path / "encounters.csv")

    keep_cols = {
        "Id": "encounter_id",
        "PATIENT": "patient_id",
        "ORGANIZATION": "organization_id",
        "PROVIDER": "provider_id",
        "START": "start_date",
        "STOP": "end_date",
        "ENCOUNTERCLASS": "encounter_class",
        "DESCRIPTION": "description",
        "REASONDESCRIPTION": "reason_description",
    }

    encounters_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    encounters_df["start_date"] = pd.to_datetime(encounters_df["start_date"])
    encounters_df["end_date"] = pd.to_datetime(encounters_df["end_date"])
    encounters_df["duration"] = (encounters_df["end_date"] - encounters_df["start_date"]).dt.total_seconds() / 60

    categorical_cols = ["encounter_class", "description", "reason_description"]
    for col in categorical_cols:
        encounters_df[col] = encounters_df[col].fillna("no_reason_specified")

    if encounters_df["duration"].isnull().any():
        encounters_df["duration"] = encounters_df["duration"].fillna(encounters_df["duration"].median())

    clear_existing_cleaned_csv("cleaned_encounters.csv")
    encounters_df.to_csv(dataset_path / "cleaned" / "cleaned_encounters.csv", index=False)

    encounters_df.to_sql(
        name="encounter",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(encounters_df)} encounters.")


def load_allergies(engine):
    df = pd.read_csv(dataset_path / "allergies.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "allergy_code",
        "DESCRIPTION": "description",
    }

    allergies_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    allergies_df["start_date"] = pd.to_datetime(allergies_df["start_date"])
    allergies_df["end_date"] = pd.to_datetime(allergies_df["end_date"])

    if allergies_df["description"].isnull().any():
        allergies_df["description"] = allergies_df["description"].fillna("unknown_allergy")

    clear_existing_cleaned_csv("cleaned_allergies.csv")
    allergies_df.to_csv(dataset_path / "cleaned" / "cleaned_allergies.csv", index=False)

    allergies_df.to_sql(
        name="allergy",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(allergies_df)} allergy records.")


def load_procedures(engine):
    df = pd.read_csv(dataset_path / "procedures.csv")

    keep_cols = {
        "DATE": "date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "procedure_code",
        "DESCRIPTION": "description",
        "REASONDESCRIPTION": "reason_description",
    }

    procedures_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    procedures_df["date"] = pd.to_datetime(procedures_df["date"])

    categorical_cols = ["description", "reason_description"]
    for col in categorical_cols:
        procedures_df[col] = procedures_df[col].fillna("routine_procedure")

    clear_existing_cleaned_csv("cleaned_procedures.csv")
    procedures_df.to_csv(dataset_path / "cleaned" / "cleaned_procedures.csv", index=False)

    procedures_df.to_sql(
        name="procedure",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(procedures_df)} procedures.")


def load_medications(engine):
    df = pd.read_csv(dataset_path / "medications.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "medication_code",
        "DESCRIPTION": "description",
        "REASONDESCRIPTION": "reason_description",
    }

    medications_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    medications_df["start_date"] = pd.to_datetime(medications_df["start_date"])
    medications_df["end_date"] = pd.to_datetime(medications_df["end_date"])
    medications_df["duration_days"] = (medications_df["end_date"] - medications_df["start_date"]).dt.days

    categorical_cols = ["description", "reason_description"]
    for col in categorical_cols:
        medications_df[col] = medications_df[col].fillna("no_reason_specified")

    clear_existing_cleaned_csv("cleaned_medications.csv")
    medications_df.to_csv(dataset_path / "cleaned" / "cleaned_medications.csv", index=False)

    medications_df.to_sql(
        name="medication",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(medications_df)} medications.")


def load_immunizations(engine):
    df = pd.read_csv(dataset_path / "immunizations.csv")

    keep_cols = {
        "DATE": "date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "immunization_code",
        "DESCRIPTION": "description",
    }

    immunizations_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    immunizations_df["date"] = pd.to_datetime(immunizations_df["date"])

    if immunizations_df["description"].isnull().any():
        immunizations_df["description"] = immunizations_df["description"].fillna("unknown_vaccine")

    clear_existing_cleaned_csv("cleaned_immunizations.csv")
    immunizations_df.to_csv(dataset_path / "cleaned" / "cleaned_immunizations.csv", index=False)

    immunizations_df.to_sql(
        name="immunization",
        con=engine,
        if_exists="replace",
        index=False,
    )
    print(f"Loaded {len(immunizations_df)} immunizations.")


def load_conditions(engine):
    df = pd.read_csv(dataset_path / "conditions.csv")

    keep_cols = {
        "START": "start_date",
        "STOP": "end_date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "condition_code",
        "DESCRIPTION": "description",
    }

    conditions_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    conditions_df["start_date"] = pd.to_datetime(conditions_df["start_date"])
    conditions_df["end_date"] = pd.to_datetime(conditions_df["end_date"], errors='coerce')

    conditions_df["description"] = conditions_df["description"].fillna("unknown_condition")

    clear_existing_cleaned_csv("cleaned_conditions.csv")
    conditions_df.to_csv(dataset_path / "cleaned" / "cleaned_conditions.csv", index=False)
    conditions_df.to_sql(name="condition", con=engine, if_exists="replace", index=False)
    print(f"Loaded {len(conditions_df)} conditions.")


def load_observations(engine):
    df = pd.read_csv(dataset_path / "observations.csv")

    keep_cols = {
        "DATE": "date",
        "PATIENT": "patient_id",
        "ENCOUNTER": "encounter_id",
        "CODE": "observation_code",
        "DESCRIPTION": "description",
        "VALUE": "value",
        "UNITS": "units",
    }

    obs_df = df[list(keep_cols.keys())].rename(columns=keep_cols)

    obs_df["value_numeric"] = pd.to_numeric(obs_df["value"], errors='coerce')

    clear_existing_cleaned_csv("cleaned_observations.csv")
    obs_df.to_csv(dataset_path / "cleaned" / "cleaned_observations.csv", index=False)

    obs_df.to_sql(name="observation", con=engine, if_exists="replace", index=False)
    print(f"Loaded {len(obs_df)} observations.")


def run_etl(engine):
    load_patients(engine)
    load_organizations(engine)
    load_providers(engine)
    load_encounters(engine)
    load_allergies(engine)
    load_procedures(engine)
    load_medications(engine)
    load_immunizations(engine)
    load_conditions(engine)
    load_observations(engine)


# run_etl(db_engine)