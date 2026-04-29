"use client";

import TextField from "@mui/material/TextField";
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
  const displayLabel = required ? `${label} *` : label;

  return (
    <TextField
      type="date"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      error={error}
      helperText={helperText}
      fullWidth={fullWidth}
      variant="standard"
      slotProps={{
        htmlInput: { min, max },
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
        input: {
          disableUnderline: true,
        },
      }}
      label={displayLabel}
      sx={{
        width: width ?? (fullWidth ? "100%" : undefined),
        "& .MuiInputLabel-root + .MuiInput-root": {
          marginTop: 0,
        },
        "& .MuiInput-root": {
          fontFamily: theme.typography.fontFamily,
          fontSize: theme.typography.fontSize.sm,
          color: theme.colors.text.primary,
          backgroundColor: error
            ? theme.colors.surface.containerLow
            : theme.colors.surface.containerLow,
          borderRadius: theme.borderRadius.md,
          padding: "10px 14px",
          ...(height !== undefined && { height, boxSizing: "border-box" as const }),
          transition: "box-shadow 0.15s ease, background-color 0.15s ease",
          "&:hover": {
            backgroundColor: theme.colors.surface.containerHighest,
          },
          "&.Mui-focused": {
            boxShadow: `0 0 0 2px rgba(0, 103, 128, 0.25)`,
            backgroundColor: theme.colors.surface.containerLowest,
          },
          "&.Mui-error": {
            boxShadow: `0 0 0 2px rgba(239, 68, 68, 0.25)`,
          },
          "&.Mui-disabled": {
            backgroundColor: theme.colors.grey[200],
            color: theme.colors.text.disabled,
            cursor: "not-allowed",
          },
        },
        "& .MuiInput-input": {
          padding: 0,
          // Tint the native calendar icon to match the theme
          "&::-webkit-calendar-picker-indicator": {
            filter:
              "invert(25%) sepia(60%) saturate(400%) hue-rotate(165deg) brightness(90%)",
            cursor: "pointer",
            opacity: 0.7,
          },
        },
        "& .MuiFormHelperText-root": {
          fontFamily: theme.typography.fontFamily,
          fontSize: "0.75rem",
          marginTop: "4px",
          marginLeft: 0,
        },
      }}
    />
  );
}
