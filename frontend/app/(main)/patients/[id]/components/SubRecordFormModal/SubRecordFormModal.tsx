"use client";

import { useEffect, useMemo, useState } from "react";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledDropdown from "@/components/generic_components/StyledDropdown/StyledDropdown";
import StyledDatePicker from "@/components/generic_components/StyledDatePicker/StyledDatePicker";
import { EncounterItem } from "@/models/generic/patients";
import { SubRecordKind } from "@/store/slices/encounters/thunks";
import { formatDate } from "@/utils/functions";

const KIND_TITLES: Record<SubRecordKind, string> = {
  observation: "observation",
  condition: "condition",
  medication: "medication",
  procedure: "procedure",
  immunization: "vaccination",
  careplan: "care plan",
  allergy: "allergy",
};

const HAS_END_DATE = new Set<SubRecordKind>([
  "condition",
  "medication",
  "procedure",
  "careplan",
  "allergy",
]);
const HAS_REASON = new Set<SubRecordKind>(["medication", "procedure", "careplan"]);
const HAS_VALUE = new Set<SubRecordKind>(["observation"]);
const SINGLE_DATE = new Set<SubRecordKind>(["observation", "immunization"]);

interface InitialValues {
  encounterId?: string | null;
  startDate?: string | null;
  endDate?: string | null;
  date?: string | null;
  code?: string;
  description?: string;
  reasonDescription?: string | null;
  value?: string;
  valueNumeric?: number | null;
  units?: string | null;
}

interface SubRecordFormModalProps {
  open: boolean;
  kind: SubRecordKind;
  encounters: EncounterItem[];
  initial?: InitialValues | null;
  submitting?: boolean;
  errorMessage?: string | null;
  onClose: () => void;
  onSubmit: (encounterId: string, payload: Record<string, unknown>) => void;
}

function toDateInput(iso: string | null | undefined): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}

export default function SubRecordFormModal({
  open,
  kind,
  encounters,
  initial,
  submitting,
  errorMessage,
  onClose,
  onSubmit,
}: SubRecordFormModalProps) {
  const [encounterId, setEncounterId] = useState<string>("");
  const [code, setCode] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [value, setValue] = useState("");
  const [valueNumeric, setValueNumeric] = useState("");
  const [units, setUnits] = useState("");
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (!open) return;
    setEncounterId(initial?.encounterId ?? "");
    setCode(initial?.code ?? "");
    setDescription(initial?.description ?? "");
    setStartDate(toDateInput(initial?.startDate ?? initial?.date));
    setEndDate(toDateInput(initial?.endDate));
    setReason(initial?.reasonDescription ?? "");
    setValue(initial?.value ?? "");
    setValueNumeric(initial?.valueNumeric != null ? String(initial.valueNumeric) : "");
    setUnits(initial?.units ?? "");
    setTouched(false);
  }, [open, initial]);

  const encounterOptions = useMemo(
    () =>
      encounters.map((e) => ({
        value: e.encounterId,
        label: `${formatDate(e.startDate)} — ${e.description}`,
      })),
    [encounters],
  );

  const errors = {
    encounterId: !encounterId ? "Required" : undefined,
    code: !code.trim() ? "Required" : undefined,
    description: !description.trim() ? "Required" : undefined,
    startDate: !startDate ? "Required" : undefined,
    value: HAS_VALUE.has(kind) && !value.trim() ? "Required" : undefined,
  };
  const hasError = Object.values(errors).some(Boolean);
  const isEditing = !!initial?.encounterId;

  const handleSubmit = () => {
    setTouched(true);
    if (hasError) return;
    const payload: Record<string, unknown> = { description: description.trim() };

    if (HAS_VALUE.has(kind)) {
      payload.observationCode = code.trim();
      payload.value = value.trim();
      payload.valueNumeric = valueNumeric ? Number(valueNumeric) : null;
      payload.units = units.trim() || null;
      payload.date = new Date(startDate).toISOString();
    } else if (kind === "immunization") {
      payload.immunizationCode = code.trim();
      payload.date = new Date(startDate).toISOString();
    } else {
      const codeKey = `${kind}Code`;
      payload[codeKey] = code.trim();
      payload.startDate = new Date(startDate).toISOString();
      if (HAS_END_DATE.has(kind)) {
        payload.endDate = endDate ? new Date(endDate).toISOString() : null;
      }
      if (HAS_REASON.has(kind)) {
        payload.reasonDescription = reason.trim() || null;
      }
    }

    onSubmit(encounterId, payload);
  };

  return (
    <FormModal
      open={open}
      title={`${isEditing ? "Edit" : "Add"} ${KIND_TITLES[kind]}`}
      submitLabel={isEditing ? "Save changes" : "Create"}
      submitting={submitting}
      onClose={onClose}
      onSubmit={handleSubmit}
      errorMessage={errorMessage}
    >
      <StyledDropdown
        label="Visit"
        required
        value={encounterId}
        onChange={(v) => setEncounterId(String(v))}
        options={encounterOptions}
        placeholder={encounters.length ? "Select a visit" : "No visits available"}
        disabled={isEditing}
        error={touched && !!errors.encounterId}
        helperText={touched ? errors.encounterId : undefined}
      />
      <StyledInput
        label="Code"
        required
        value={code}
        onChange={(e) => setCode(e.target.value)}
        error={touched && !!errors.code}
        helperText={touched ? errors.code : undefined}
      />
      <StyledInput
        label="Description"
        required
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        error={touched && !!errors.description}
        helperText={touched ? errors.description : undefined}
      />
      <StyledDatePicker
        label={SINGLE_DATE.has(kind) ? "Date" : "Start date"}
        required
        value={startDate}
        onChange={setStartDate}
        error={touched && !!errors.startDate}
        helperText={touched ? errors.startDate : undefined}
        fullWidth
      />
      {HAS_END_DATE.has(kind) && (
        <StyledDatePicker
          label="End date"
          value={endDate}
          onChange={setEndDate}
          fullWidth
        />
      )}
      {HAS_REASON.has(kind) && (
        <StyledInput
          label="Reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      )}
      {HAS_VALUE.has(kind) && (
        <>
          <StyledInput
            label="Value"
            required
            value={value}
            onChange={(e) => setValue(e.target.value)}
            error={touched && !!errors.value}
            helperText={touched ? errors.value : undefined}
          />
          <StyledInput
            label="Numeric value"
            type="number"
            value={valueNumeric}
            onChange={(e) => setValueNumeric(e.target.value)}
          />
          <StyledInput
            label="Units"
            value={units}
            onChange={(e) => setUnits(e.target.value)}
          />
        </>
      )}
    </FormModal>
  );
}
