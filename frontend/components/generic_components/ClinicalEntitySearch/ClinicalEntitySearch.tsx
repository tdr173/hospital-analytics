"use client";

import { useState, useEffect, useRef } from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";
import { apiUrl } from "@/utils/apiBases";

interface Option {
  id: string;
  label: string;
}

interface Props {
  entityType: "patient" | "provider";
  value: string | null;
  onChange: (id: string | null) => void;
  error?: boolean;
  helperText?: string;
}

export default function ClinicalEntitySearch({ entityType, value, onChange, error, helperText }: Props) {
  const [inputValue, setInputValue] = useState("");
  const [options, setOptions] = useState<Option[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const selectedOption = options.find((o) => o.id === value) ?? null;

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!inputValue.trim()) {
      setOptions([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const path = entityType === "patient"
          ? `/patients?search=${encodeURIComponent(inputValue)}&rows=10&page=1`
          : `/providers?search=${encodeURIComponent(inputValue)}&rows=10&page=1`;
        const res = await fetch(apiUrl(path), {
          headers: { "ngrok-skip-browser-warning": "true" },
        });
        if (!res.ok) return;
        const data = await res.json();
        const items: Option[] = (data?.items ?? []).map((item: any) => {
          if (entityType === "patient") {
            return {
              id: item.patientId ?? item.patient_id,
              label: `${item.firstName ?? item.first_name} ${item.lastName ?? item.last_name}`,
            };
          }
          return {
            id: item.providerId ?? item.provider_id,
            label: `${item.firstName ?? item.first_name} ${item.lastName ?? item.last_name}${item.speciality ? ` — ${item.speciality}` : ""}`,
          };
        });
        setOptions(items);
      } catch {
        // silently ignore search errors
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [inputValue, entityType]);

  return (
    <Autocomplete
      options={options}
      value={selectedOption}
      inputValue={inputValue}
      onInputChange={(_, val) => setInputValue(val)}
      onChange={(_, opt) => onChange(opt?.id ?? null)}
      loading={loading}
      filterOptions={(x) => x}
      getOptionLabel={(opt) => opt.label}
      isOptionEqualToValue={(opt, val) => opt.id === val.id}
      renderInput={(params) => (
        <TextField
          {...params}
          label={entityType === "patient" ? "Patient" : "Provider"}
          required
          error={error}
          helperText={helperText}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={16} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
          size="small"
        />
      )}
    />
  );
}
