"use client";

import { useState } from "react";
import TextField, { TextFieldProps } from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";

interface StyledInputProps
  extends Omit<TextFieldProps, "variant" | "label" | "type"> {
  label: string;
  type?: "text" | "password" | "email" | "number";
  error?: boolean;
  helperText?: string;
  disabled?: boolean;
}

export default function StyledInput({
  label,
  type = "text",
  error = false,
  helperText,
  disabled = false,
  sx,
  ...props
}: StyledInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  const isPassword = type === "password";
  const inputType = isPassword && showPassword ? "text" : type;

  return (
    <TextField
      fullWidth
      variant="standard"
      label={label}
      type={inputType}
      error={error}
      helperText={helperText}
      disabled={disabled}
      slotProps={{
        input: {
          disableUnderline: true,
          endAdornment: isPassword ? (
            <InputAdornment position="end">
              <IconButton
                onClick={() => setShowPassword(!showPassword)}
                edge="end"
                size="small"
                sx={{ color: "#6b7280" }}
              >
                {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
              </IconButton>
            </InputAdornment>
          ) : undefined,
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
            marginBottom: "6px",
          },
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
  );
}
