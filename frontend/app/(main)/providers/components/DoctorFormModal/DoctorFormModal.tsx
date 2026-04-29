"use client";

import { useEffect, useState } from "react";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import { ProviderDetail, ProviderResources } from "@/models/generic/providers";
import { ProviderCreatePayload } from "@/store/slices/providers/thunks";

interface DoctorFormModalProps {
  open: boolean;
  initial?: ProviderDetail | null;
  resources: ProviderResources | null;
  submitting?: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onSubmit: (payload: ProviderCreatePayload) => void;
}

export default function DoctorFormModal({
  open,
  initial,
  resources,
  submitting,
  errorMessage,
  onClose,
  onSubmit,
}: DoctorFormModalProps) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [gender, setGender] = useState<string>("");
  const [speciality, setSpeciality] = useState<string>("");
  const [city, setCity] = useState("");
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) return;
    setFirstName(initial?.firstName ?? "");
    setLastName(initial?.lastName ?? "");
    setGender(initial?.gender ?? "");
    setSpeciality(initial?.speciality ?? "");
    setCity(initial?.city ?? "");
    setTouched(false);
  }, [open, initial]);

  const errors = {
    firstName: !firstName.trim() ? "Required" : undefined,
    lastName: !lastName.trim() ? "Required" : undefined,
  };
  const hasError = Object.values(errors).some(Boolean);

  const handleSubmit = () => {
    setTouched(true);
    if (hasError) return;
    onSubmit({
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      gender: gender || null,
      speciality: speciality.trim() || null,
      city: city.trim() || null,
    });
  };

  const specialityOptions = resources?.specialities ?? [];

  return (
    <FormModal
      open={open}
      title={initial ? "Edit doctor" : "Add doctor"}
      submitLabel={initial ? "Save changes" : "Create doctor"}
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
      <StyledDropdown
        label="Gender"
        value={gender}
        onChange={(v) => setGender(String(v))}
        options={[
          { value: "M", label: "Male" },
          { value: "F", label: "Female" },
        ]}
        placeholder="Select"
      />
      <StyledDropdown
        label="Specialty"
        value={speciality}
        onChange={(v) => setSpeciality(String(v))}
        options={specialityOptions.length ? specialityOptions : [{ value: "GENERAL PRACTICE", label: "GENERAL PRACTICE" }]}
        placeholder="Select"
      />
      <StyledInput
        label="City"
        value={city}
        onChange={(e) => setCity(e.target.value)}
      />
    </FormModal>
  );
}
