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
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) return;
    setFirstName(initial?.firstName ?? "");
    setLastName(initial?.lastName ?? "");
    setBirthdate(initial?.birthdate ?? "");
    setGender(initial?.gender ?? "");
    setRace(initial?.race ?? "");
    setEthnicity(initial?.ethnicity ?? "");
    setMarital(initial?.marital ?? "");
    setCity(initial?.city ?? "");
    const det = initial as PatientDetail | undefined;
    setLatitude(det?.latitude != null ? String(det.latitude) : "");
    setLongitude(det?.longitude != null ? String(det.longitude) : "");
    setTouched(false);
  }, [open, initial]);

  const errors = {
    firstName: !firstName.trim() ? "Required" : undefined,
    lastName: !lastName.trim() ? "Required" : undefined,
    birthdate: !birthdate ? "Required" : undefined,
  };
  const hasError = Object.values(errors).some(Boolean);

  const handleSubmit = () => {
    setTouched(true);
    if (hasError) return;
    onSubmit({
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      age: deriveAge(birthdate),
      birthdate: birthdate || null,
      gender: gender || null,
      race: race || null,
      ethnicity: ethnicity || null,
      marital: marital || null,
      city: city.trim() || null,
      latitude: latitude ? Number(latitude) : null,
      longitude: longitude ? Number(longitude) : null,
    });
  };

  return (
    <FormModal
      open={open}
      title={initial ? "Edit patient" : "Add patient"}
      submitLabel={initial ? "Save changes" : "Create patient"}
      submitting={submitting}
      onClose={onClose}
      onSubmit={handleSubmit}
      errorMessage={errorMessage}
    >
      <StyledInput
        label="First name"
        required
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
        error={touched && !!errors.firstName}
        helperText={touched ? errors.firstName : undefined}
      />
      <StyledInput
        label="Last name"
        required
        value={lastName}
        onChange={(e) => setLastName(e.target.value)}
        error={touched && !!errors.lastName}
        helperText={touched ? errors.lastName : undefined}
      />
      <StyledDatePicker
        label="Birthdate"
        required
        value={birthdate}
        onChange={setBirthdate}
        error={touched && !!errors.birthdate}
        helperText={touched ? errors.birthdate : undefined}
        fullWidth
      />
      <StyledDropdown
        label="Gender"
        value={gender}
        onChange={(v) => setGender(String(v))}
        options={resources?.genders ?? []}
        placeholder="Select"
      />
      <StyledDropdown
        label="Race"
        value={race}
        onChange={(v) => setRace(String(v))}
        options={resources?.races ?? []}
        placeholder="Select"
      />
      <StyledInput
        label="Ethnicity"
        value={ethnicity}
        onChange={(e) => setEthnicity(e.target.value)}
      />
      <StyledDropdown
        label="Marital status"
        value={marital}
        onChange={(v) => setMarital(String(v))}
        options={resources?.maritalStatuses ?? []}
        placeholder="Select"
      />
      <StyledInput
        label="City"
        value={city}
        onChange={(e) => setCity(e.target.value)}
      />
      <StyledInput
        label="Latitude"
        type="number"
        value={latitude}
        onChange={(e) => setLatitude(e.target.value)}
      />
      <StyledInput
        label="Longitude"
        type="number"
        value={longitude}
        onChange={(e) => setLongitude(e.target.value)}
      />
    </FormModal>
  );
}
