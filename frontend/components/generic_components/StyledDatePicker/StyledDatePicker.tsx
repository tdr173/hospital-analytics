"use client";

import { useRef, useState, useEffect } from "react";
import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import theme from "@/utils/theme";

interface StyledDatePickerProps {
  label: string;
  value: string; // "YYYY-MM-DD"
  onChange: (value: string) => void;
  min?: string; // "YYYY-MM-DD"
  max?: string; // "YYYY-MM-DD"
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  required?: boolean;
  fullWidth?: boolean;
  width?: string | number;
  height?: string | number;
}

function toDisplay(yyyymmdd: string): string {
  if (!yyyymmdd) return "";
  const [y, m, d] = yyyymmdd.split("-");
  if (!y || !m || !d) return "";
  return `${d}/${m}/${y}`;
}

function toInternal(ddmmyyyy: string): string | null {
  const match = ddmmyyyy.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!match) return null;
  const [, d, m, y] = match;
  const date = new Date(`${y}-${m}-${d}`);
  if (isNaN(date.getTime())) return null;
  return `${y}-${m}-${d}`;
}

export default function StyledDatePicker({
  label,
  value,
  onChange,
  min,
  max,
  disabled = false,
  error = false,
  helperText,
  required = false,
  fullWidth = false,
  width,
  height = 40,
}: StyledDatePickerProps) {
  const [display, setDisplay] = useState(toDisplay(value));
  const nativeRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setDisplay(toDisplay(value));
  }, [value]);

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const prev = display;
    const raw = e.target.value;

    // Allow backspace/delete to work naturally
    if (raw.length < prev.length) {
      setDisplay(raw);
      return;
    }

    const digits = raw.replace(/\D/g, "");
    let formatted = digits;
    if (digits.length > 2) formatted = digits.slice(0, 2) + "/" + digits.slice(2);
    if (digits.length > 4) formatted = formatted.slice(0, 5) + "/" + digits.slice(4, 8);

    setDisplay(formatted);

    if (formatted.length === 10) {
      const internal = toInternal(formatted);
      if (internal) onChange(internal);
    }
  };

  const handleBlur = () => {
    // Reset to last valid value if incomplete
    setDisplay(toDisplay(value));
  };

  const handleNativeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value; // YYYY-MM-DD
    if (val) {
      onChange(val);
      setDisplay(toDisplay(val));
    }
  };

  const openPicker = () => {
    const el = nativeRef.current;
    if (!el) return;
    try {
      el.showPicker();
    } catch {
      el.click();
    }
  };

  const displayLabel = required ? `${label} *` : label;

  return (
    <div style={{ position: "relative", width: width ?? (fullWidth ? "100%" : undefined) }}>
      <TextField
        type="text"
        value={display}
        onChange={handleTextChange}
        onBlur={handleBlur}
        placeholder="dd/mm/yyyy"
        disabled={disabled}
        error={error}
        helperText={helperText}
        fullWidth
        variant="standard"
        slotProps={{
          input: {
            disableUnderline: true,
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={openPicker}
                  disabled={disabled}
                  size="small"
                  sx={{ padding: "2px", color: theme.colors.text.secondary }}
                  tabIndex={-1}
                >
                  <CalendarTodayIcon sx={{ fontSize: "1rem" }} />
                </IconButton>
              </InputAdornment>
            ),
          },
          inputLabel: {
            shrink: true,
            sx: {
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.75rem",
              fontWeight: 700,
              color: "#6b7280",
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              position: "relative",
              transform: "none",
              marginBottom: "2px",
            },
          },
        }}
        label={displayLabel}
        sx={{
          "& .MuiInputLabel-root + .MuiInput-root": { marginTop: 0 },
          "& .MuiInput-root": {
            fontFamily: theme.typography.fontFamily,
            fontSize: theme.typography.fontSize.sm,
            color: theme.colors.text.primary,
            backgroundColor: theme.colors.surface.containerLow,
            borderRadius: theme.borderRadius.md,
            padding: "10px 14px",
            ...(height !== undefined && { height, boxSizing: "border-box" as const }),
            transition: "box-shadow 0.15s ease, background-color 0.15s ease",
            "&:hover": { backgroundColor: theme.colors.surface.containerHighest },
            "&.Mui-focused": {
              boxShadow: `0 0 0 2px rgba(0, 103, 128, 0.25)`,
              backgroundColor: theme.colors.surface.containerLowest,
            },
            "&.Mui-error": { boxShadow: `0 0 0 2px rgba(239, 68, 68, 0.25)` },
            "&.Mui-disabled": {
              backgroundColor: theme.colors.grey[200],
              color: theme.colors.text.disabled,
              cursor: "not-allowed",
            },
          },
          "& .MuiInput-input": { padding: 0 },
          "& .MuiFormHelperText-root": {
            fontFamily: theme.typography.fontFamily,
            fontSize: "0.75rem",
            marginTop: "4px",
            marginLeft: 0,
          },
        }}
      />
      <input
        ref={nativeRef}
        type="date"
        value={value}
        min={min}
        max={max}
        onChange={handleNativeChange}
        tabIndex={-1}
        style={{ position: "absolute", opacity: 0, width: 0, height: 0, pointerEvents: "none" }}
      />
    </div>
  );
}
