"use client";

import { useState } from "react";
import React from "react";
import TextField, { TextFieldProps } from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import ClearIcon from "@mui/icons-material/Clear";
import useClasses from "@/utils/useClasses";
import { StyledInputStyles } from "./StyledInputStyles";

interface StyledInputProps extends Omit<
  TextFieldProps,
  "variant" | "label" | "type" | "required"
> {
  label: string;
  type?: "text" | "password" | "email" | "number";
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  startIcon?: React.ReactNode;
  clearIcon?: boolean;
  height?: string | number;
  onClear?: () => void;
}

export default function StyledInput({
  label,
  type = "text",
  error = false,
  helperText,
  disabled = false,
  required = false,
  startIcon,
  clearIcon,
  onClear,
  height = 40,
  sx,
  ...props
}: StyledInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  const isPassword = type === "password";
  const inputType = isPassword && showPassword ? "text" : type;

  const classes = useClasses(StyledInputStyles, { name: "StyledInput" });
  const displayLabel = required ? `${label} *` : label;

  const endAdornment = isPassword ? (
    <InputAdornment position="end">
      <IconButton
        onClick={() => setShowPassword(!showPassword)}
        edge="end"
        size="small"
        sx={{ color: "#6b7280" }}
      >
        {showPassword ? (
          <VisibilityOff fontSize="small" />
        ) : (
          <Visibility fontSize="small" />
        )}
      </IconButton>
    </InputAdornment>
  ) : clearIcon && props.value ? (
    <InputAdornment position="end">
      <IconButton
        onClick={onClear}
        size="small"
        sx={{
          padding: "2px",
          color: "#6b7280",
          "&:hover": { color: "#191c1e" },
        }}
      >
        <ClearIcon sx={{ fontSize: "0.95rem" }} />
      </IconButton>
    </InputAdornment>
  ) : undefined;

  return (
    <div className={classes.wrapper}>
      <span className={classes.label} style={{ marginBottom: "6px" }}>
        {displayLabel}
      </span>
      <TextField
        fullWidth
        variant="standard"
        type={inputType}
        error={error}
        helperText={helperText}
        disabled={disabled}
        slotProps={{
          input: {
            disableUnderline: true,
            startAdornment: startIcon ? (
              <InputAdornment position="start" sx={{ mr: "8px" }}>
                {startIcon}
              </InputAdornment>
            ) : undefined,
            endAdornment,
          },
        }}
        sx={{
          "& .MuiInput-root": {
            fontFamily: '"Inter", sans-serif',
            fontSize: "0.875rem",
            color: "#191c1e",
            backgroundColor: "#f2f4f6",
            borderRadius: "6px",
            padding: "10px 14px",
            ...(height !== undefined && {
              height,
              boxSizing: "border-box" as const,
            }),
            transition: "box-shadow 0.15s ease",
            "&:hover": {
              backgroundColor: "#edf0f2",
            },
            "&.Mui-focused": {
              boxShadow: "0 0 0 2px rgba(0, 103, 128, 0.25)",
              backgroundColor: "#ffffff",
            },
            "&.Mui-error": {
              boxShadow: "0 0 0 2px rgba(239, 68, 68, 0.25)",
            },
            "&.Mui-disabled": {
              backgroundColor: "#e0e3e5",
              color: "#9ca3af",
              cursor: "not-allowed",
            },
          },
          "& .MuiFormHelperText-root": {
            fontFamily: '"Inter", sans-serif',
            fontSize: "0.75rem",
            marginTop: "4px",
            marginLeft: 0,
          },
          ...sx,
        }}
        {...props}
      />
    </div>
  );
}
