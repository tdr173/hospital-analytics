"use client";

import { useEffect, useState } from "react";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import StyledDatePicker from "@/components/generic_components/StyledDatePicker/StyledDatePicker";
import {
  PatientDetail,
  PatientListItem,
  PatientResources,
} from "@/models/generic/patients";
import { PatientCreatePayload } from "@/store/slices/patients/thunks";

type PatientLike = PatientDetail | PatientListItem | null | undefined;

interface PatientFormModalProps {
  open: boolean;
  initial?: PatientLike;
  resources: PatientResources | null;
  submitting?: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onSubmit: (payload: PatientCreatePayload) => void;
}

function deriveAge(birthdate: string): number {
  if (!birthdate) return 0;
  const dob = new Date(birthdate);
  if (Number.isNaN(dob.getTime())) return 0;
  const diffMs = Date.now() - dob.getTime();
  return Math.max(1, Math.floor(diffMs / (1000 * 60 * 60 * 24 * 365.25)));
}

export default function PatientFormModal({
  open,
  initial,
  resources,
  submitting,
  errorMessage,
  onClose,
  onSubmit,
}: PatientFormModalProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [birthdate, setBirthdate] = useState("");
  const [gender, setGender] = useState("");
  const [race, setRace] = useState("");
  const [ethnicity, setEthnicity] = useState("");
  const [marital, setMarital] = useState("");
  const [city, setCity] = useState("");
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) return;

    let raceValue = initial?.race ?? "";
    // Try to find matching race in resources (case-insensitive)
    if (raceValue && resources?.races) {
      const matchedRace = resources.races.find(
        (r) => r.value.toString().toLowerCase() === raceValue.toLowerCase()
      );
      raceValue = matchedRace?.value.toString() ?? raceValue;
    }

    let maritalValue = initial?.marital ?? "";
    // Try to find matching marital in resources (case-insensitive)
    if (maritalValue && resources?.maritalStatuses) {
      const matchedMarital = resources.maritalStatuses.find(
        (m) => m.value.toString().toLowerCase() === maritalValue.toLowerCase()
      );
      maritalValue = matchedMarital?.value.toString() ?? maritalValue;
    }

    let genderValue = initial?.gender ?? "";
    // Try to find matching gender in resources (case-insensitive)
    if (genderValue && resources?.genders) {
      const matchedGender = resources.genders.find(
        (g) => g.value.toString().toLowerCase() === genderValue.toLowerCase()
      );
      genderValue = matchedGender?.value.toString() ?? genderValue;
    }

    setFirstName(initial?.firstName ?? "");
    setLastName(initial?.lastName ?? "");
    setBirthdate(initial?.birthdate ?? "");
    setGender(genderValue);
    setRace(raceValue);
    setEthnicity(initial?.ethnicity ?? "");
    setMarital(maritalValue);
    setCity(initial?.city ?? "");
    setTouched(false);
  }, [open, initial, resources]);

  const errors = {
    firstName: !firstName.trim() ? "Required" : undefined,
    lastName: !lastName.trim() ? "Required" : undefined,
    birthdate: !birthdate ? "Required" : undefined,
    gender: !gender ? "Required" : undefined,
    race: !race ? "Required" : undefined,
    ethnicity: !ethnicity.trim() ? "Required" : undefined,
    marital: !marital ? "Required" : undefined,
    city: !city.trim() ? "Required" : undefined,
  };
  const hasError = Object.values(errors).some(Boolean);
  const isResourcesLoaded = resources && resources.races && resources.races.length > 0;

  const handleSubmit = () => {
    setTouched(true);
    // Re-evaluate errors after setting touched
    const newErrors = {
      firstName: !firstName.trim() ? "Required" : undefined,
      lastName: !lastName.trim() ? "Required" : undefined,
      birthdate: !birthdate ? "Required" : undefined,
      gender: !gender ? "Required" : undefined,
      race: !race ? "Required" : undefined,
      ethnicity: !ethnicity.trim() ? "Required" : undefined,
      marital: !marital ? "Required" : undefined,
      city: !city.trim() ? "Required" : undefined,
    };
    if (Object.values(newErrors).some(Boolean)) return;
    onSubmit({
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      age: deriveAge(birthdate),
      birthdate: birthdate || null,
      gender,
      race,
      ethnicity: ethnicity.trim(),
      marital,
      city: city.trim(),
    });
  };

  return (
    <FormModal
      open={open}
      title={initial ? "Edit patient" : "Add patient"}
      submitLabel={initial ? "Save changes" : "Create patient"}
      submitting={submitting || !isResourcesLoaded}
      onClose={onClose}
      onSubmit={handleSubmit}
      errorMessage={errorMessage || (!isResourcesLoaded ? "Loading form data..." : null)}
    >
      <StyledInput
        label="First name"
        required
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
        error={touched && !!errors.firstName}
        helperText={touched ? errors.firstName : undefined}
        height={"40px"}
      />
      <StyledInput
        label="Last name"
        required
        value={lastName}
        onChange={(e) => setLastName(e.target.value)}
        error={touched && !!errors.lastName}
        helperText={touched ? errors.lastName : undefined}
        height={"40px"}
      />
      <StyledDatePicker
        label="Birthdate"
        required
        value={birthdate}
        onChange={setBirthdate}
        error={touched && !!errors.birthdate}
        helperText={touched ? errors.birthdate : undefined}
        fullWidth
        height={"40px"}
      />
      <StyledDropdown
        label="Gender"
        required
        value={gender}
        onChange={(v) => setGender(String(v))}
        options={resources?.genders ?? []}
        placeholder="Select"
        error={touched && !!errors.gender}
        helperText={touched ? errors.gender : undefined}
        height={"40px"}
      />
      <StyledDropdown
        label="Race"
        required
        value={race}
        onChange={(v) => setRace(String(v))}
        options={resources?.races ?? []}
        placeholder="Select"
        error={touched && !!errors.race}
        helperText={touched ? errors.race : undefined}
        height={"40px"}
      />
      <StyledInput
        label="Ethnicity"
        required
        value={ethnicity}
        onChange={(e) => setEthnicity(e.target.value)}
        error={touched && !!errors.ethnicity}
        helperText={touched ? errors.ethnicity : undefined}
        height={"40px"}
      />
      <StyledDropdown
        label="Marital status"
        required
        value={marital}
        onChange={(v) => setMarital(String(v))}
        options={resources?.maritalStatuses ?? []}
        placeholder="Select"
        error={touched && !!errors.marital}
        helperText={touched ? errors.marital : undefined}
        height={"40px"}
      />
      <StyledInput
        label="City"
        required
        value={city}
        onChange={(e) => setCity(e.target.value)}
        error={touched && !!errors.city}
        helperText={touched ? errors.city : undefined}
        height={"40px"}
      />
    </FormModal>
  );
}
