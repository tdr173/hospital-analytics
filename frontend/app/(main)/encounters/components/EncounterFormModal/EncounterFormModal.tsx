"use client";

import { useEffect, useState } from "react";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import StyledDatePicker from "@/components/generic_components/StyledDatePicker/StyledDatePicker";

const ENCOUNTER_CLASSES = [
  { value: "wellness", label: "Wellness" },
  { value: "ambulatory", label: "Ambulatory" },
  { value: "outpatient", label: "Outpatient" },
  { value: "urgentcare", label: "Urgent Care" },
  { value: "emergency", label: "Emergency" },
  { value: "inpatient", label: "Inpatient" },
];

export interface EncounterFormValue {
  patientId?: string;
  startDate: string;
  endDate: string;
  encounterClass: string;
  description: string;
  reasonDescription: string | null;
}

interface InitialValues {
  startDate?: string;
  endDate?: string;
  encounterClass?: string;
  description?: string;
  reasonDescription?: string | null;
}

interface EncounterFormModalProps {
  open: boolean;
  showPatientId?: boolean;
  initial?: InitialValues | null;
  submitting?: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onSubmit: (value: EncounterFormValue) => void;
}

function toLocalInputValue(iso: string | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function EncounterFormModal({
  open,
  showPatientId = false,
  initial,
  submitting,
  errorMessage,
  onClose,
  onSubmit,
}: EncounterFormModalProps) {
  const [patientId, setPatientId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [encounterClass, setEncounterClass] = useState("ambulatory");
  const [description, setDescription] = useState("");
  const [reason, setReason] = useState("");
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) return;
    setPatientId("");
    setStartDate(toLocalInputValue(initial?.startDate));
    setEndDate(toLocalInputValue(initial?.endDate));
    setEncounterClass(initial?.encounterClass ?? "ambulatory");
    setDescription(initial?.description ?? "");
    setReason(initial?.reasonDescription ?? "");
    setTouched(false);
  }, [open, initial]);

  const errors = {
    patientId:
      showPatientId && !patientId.trim() ? "This field is required" : undefined,
    startDate: !startDate ? "This field is required" : undefined,
    endDate: !endDate ? "This field is required" : undefined,
    description: !description.trim() ? "This field is required" : undefined,
  };
  const hasError = Object.values(errors).some(Boolean);

  const handleSubmit = () => {
    setTouched(true);
    if (hasError) return;
    onSubmit({
      ...(showPatientId ? { patientId: patientId.trim() } : {}),
      startDate: new Date(startDate).toISOString(),
      endDate: new Date(endDate).toISOString(),
      encounterClass,
      description: description.trim(),
      reasonDescription: reason.trim() || null,
    });
  };

  return (
    <FormModal
      open={open}
      title={initial ? "Edit visit" : "Add visit"}
      submitLabel={initial ? "Save changes" : "Create visit"}
      submitting={submitting}
      onClose={onClose}
      onSubmit={handleSubmit}
      errorMessage={errorMessage}
    >
      {showPatientId && (
        <StyledInput
          label="Patient ID"
          required
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
          error={touched && !!errors.patientId}
          helperText={touched ? errors.patientId : undefined}
          placeholder="Enter patient ID"
        />
      )}
      {showPatientId && (
        <StyledDropdown
          label="Type"
          required
          value={encounterClass}
          onChange={(v) => setEncounterClass(String(v))}
          options={ENCOUNTER_CLASSES}
          onClear={() => setEncounterClass("")}
        />
      )}
      <StyledDatePicker
        label="Start (date)"
        required
        value={startDate.slice(0, 10)}
        onChange={(v) => setStartDate(`${v}T${startDate.slice(11) || "09:00"}`)}
        error={touched && !!errors.startDate}
        helperText={touched ? errors.startDate : undefined}
        fullWidth
      />
      <StyledInput
        label="Start (time)"
        type="text"
        required
        value={startDate.slice(11) || ""}
        onChange={(e) =>
          setStartDate(`${startDate.slice(0, 10) || ""}T${e.target.value}`)
        }
        placeholder="HH:MM"
      />
      <StyledDatePicker
        label="End (date)"
        required
        value={endDate.slice(0, 10)}
        onChange={(v) => setEndDate(`${v}T${endDate.slice(11) || "10:00"}`)}
        error={touched && !!errors.endDate}
        helperText={touched ? errors.endDate : undefined}
        fullWidth
      />
      <StyledInput
        label="End (time)"
        type="text"
        value={endDate.slice(11) || ""}
        onChange={(e) =>
          setEndDate(`${endDate.slice(0, 10) || ""}T${e.target.value}`)
        }
        placeholder="HH:MM"
      />
      <StyledInput
        label="Description"
        required
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        error={touched && !!errors.description}
        helperText={touched ? errors.description : undefined}
      />
      <StyledInput
        label="Reason"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
      />
      {!showPatientId && (
        <StyledDropdown
          label="Type"
          required
          value={encounterClass}
          onChange={(v) => setEncounterClass(String(v))}
          options={ENCOUNTER_CLASSES}
          onClear={() => setEncounterClass("")}
        />
      )}

      <div />
    </FormModal>
  );
}
