"use client";

import { useState, useEffect } from "react";
import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import SearchIcon from "@mui/icons-material/Search";
import ClearIcon from "@mui/icons-material/Clear";
import theme from "@/utils/theme";

interface StyledSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  width?: string | number;
}

export default function StyledSearchBar({
  value,
  onChange,
  placeholder = "Search...",
  disabled = false,
  width,
}: StyledSearchBarProps) {
  const [localValue, setLocalValue] = useState(value);

  useEffect(() => {
    setLocalValue(value);
  }, [value]);

  const commit = (v: string) => {
    if (v !== value) onChange(v);
  };

  return (
    <TextField
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      onBlur={() => commit(localValue)}
      onKeyDown={(e) => { if (e.key === "Enter") commit(localValue); }}
      placeholder={placeholder}
      disabled={disabled}
      variant="standard"
      sx={{
        width: width ?? "100%",
        maxWidth: 360,
        "& .MuiInput-root": {
          fontFamily: theme.typography.fontFamily,
          fontSize: theme.typography.fontSize.sm,
          color: theme.colors.text.primary,
          backgroundColor: theme.colors.surface.containerLow,
          borderRadius: theme.borderRadius.md,
          padding: "8px 12px",
          transition: "box-shadow 0.15s ease, background-color 0.15s ease",
          "&:hover": {
            backgroundColor: theme.colors.surface.containerHighest,
          },
          "&.Mui-focused": {
            boxShadow: `0 0 0 2px rgba(0, 103, 128, 0.25)`,
            backgroundColor: theme.colors.surface.containerLowest,
          },
          "&.Mui-disabled": {
            backgroundColor: theme.colors.grey[200],
            color: theme.colors.text.disabled,
          },
          height: "40px",
        },
        "& .MuiInput-input": {
          padding: 0,
          "&::placeholder": {
            color: theme.colors.text.secondary,
            opacity: 1,
          },
        },
      }}
      slotProps={{
        input: {
          disableUnderline: true,
          startAdornment: (
            <InputAdornment position="start" sx={{ mr: "8px" }}>
              <SearchIcon
                sx={{
                  fontSize: "1.1rem",
                  color: theme.colors.text.secondary,
                }}
              />
            </InputAdornment>
          ),
          endAdornment: value ? (
            <InputAdornment position="end" sx={{ ml: "4px" }}>
              <IconButton
                size="small"
                onClick={() => onChange("")}
                sx={{
                  padding: "2px",
                  color: theme.colors.text.secondary,
                  "&:hover": { color: theme.colors.text.primary },
                }}
              >
                <ClearIcon sx={{ fontSize: "0.95rem" }} />
              </IconButton>
            </InputAdornment>
          ) : undefined,
        },
      }}
    />
  );
}
