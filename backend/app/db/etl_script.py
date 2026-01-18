import os
import pandas as pd
from pathlib import Path

from db import engine as db_engine

dataset_path = Path(__file__).parent.parent.parent.parent / "dataset"

def load_csv(path):
    df = pd.read_csv(path)
    return df


def clear_existing_cleaned_csv(cleaned_name: str):
    if os.path.exists(dataset_path / cleaned_name):
        os.remove(dataset_path / cleaned_name)


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
        "STATE": "state",
        "LAT": "latitude",
        "LON": "longitude",
    }

    patients_df = df[list(keep_cols.keys())].rename(columns=keep_cols)
    patients_df["marital"] = patients_df["marital"].fillna("unmarried")

    ref_date = pd.Timestamp.now()
    patients_df["birthdate"] = pd.to_datetime(patients_df["birthdate"])
    patients_df["deathdate"] = pd.to_datetime(patients_df["deathdate"])
    patients_df["age"] = (patients_df["deathdate"].fillna(ref_date) - patients_df["birthdate"]).dt.days // 365

    if patients_df["gender"].isna().sum():
        patients_df["gender"] = patients_df["gender"].fillna(patients_df["gender"].mode()[0])

    if patients_df["race"].isna().sum():
        patients_df["race"] = patients_df["race"].fillna(patients_df["race"].mode()[0])

    clear_existing_cleaned_csv("cleaned_patients.csv")
    patients_df.to_csv(dataset_path / "cleaned_patients.csv", index=False)

    patients_df.to_sql(
        name="patient",
        con=db_engine,
        if_exists="append",
        index=False,
    )

load_patients("a")


