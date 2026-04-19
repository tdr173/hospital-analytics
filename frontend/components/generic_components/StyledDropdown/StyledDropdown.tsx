"use client";

import Select, { SelectChangeEvent } from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import theme from "@/utils/theme";
import useClasses from "@/utils/useClasses";
import { StyledDropdownStyles } from "./StyledDropdownStyles";

export interface DropdownOption {
  value: string | number;
  label: string;
}

interface StyledDropdownProps {
  label: string;
  value: string | number | "";
  onChange: (value: string | number | "") => void;
  options: DropdownOption[];
  placeholder?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  required?: boolean;
  fullWidth?: boolean;
  width?: string | number;
  height?: string | number;
}

const selectSx = {
  fontFamily: theme.typography.fontFamily,
  fontSize: theme.typography.fontSize.sm,
  color: theme.colors.text.primary,
  backgroundColor: theme.colors.surface.containerLow,
  borderRadius: theme.borderRadius.md,
  transition: "box-shadow 0.15s ease, background-color 0.15s ease",
  "& .MuiSelect-select": {
    padding: "10px 14px",
    paddingRight: "36px !important",
  },
  "& .MuiOutlinedInput-notchedOutline": {
    border: "none",
  },
  "&:hover": {
    backgroundColor: theme.colors.surface.containerHighest,
    "& .MuiOutlinedInput-notchedOutline": { border: "none" },
  },
  "&.Mui-focused": {
    boxShadow: `0 0 0 2px rgba(0, 103, 128, 0.25)`,
    backgroundColor: theme.colors.surface.containerLowest,
    "& .MuiOutlinedInput-notchedOutline": { border: "none" },
  },
  "&.Mui-error": {
    boxShadow: `0 0 0 2px rgba(239, 68, 68, 0.25)`,
    "& .MuiOutlinedInput-notchedOutline": { border: "none" },
  },
  "&.Mui-disabled": {
    backgroundColor: theme.colors.grey[200],
    color: theme.colors.text.disabled,
    "& .MuiOutlinedInput-notchedOutline": { border: "none" },
  },
  "& .MuiSelect-icon": {
    color: theme.colors.text.secondary,
    right: "10px",
  },
};

const menuPaperSx = {
  borderRadius: theme.borderRadius.md,
  boxShadow: theme.shadows.md,
  border: `1px solid ${theme.colors.border.main}`,
  marginTop: "4px",
  "& .MuiMenuItem-root": {
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    padding: "9px 14px",
    "&:hover": {
      backgroundColor: theme.colors.surface.containerLow,
    },
    "&.Mui-selected": {
      backgroundColor: theme.colors.secondary.light,
      color: theme.colors.primary.main,
      fontWeight: theme.typography.fontWeight.semibold,
      "&:hover": {
        backgroundColor: theme.colors.secondary.light,
      },
    },
  },
};

export default function StyledDropdown({
  label,
  value,
  onChange,
  options,
  placeholder,
  disabled = false,
  error = false,
  helperText,
  required = false,
  fullWidth = false,
  width,
  height,
}: StyledDropdownProps) {
  const classes = useClasses(StyledDropdownStyles, { name: "StyledDropdown" });

  const handleChange = (e: SelectChangeEvent<string | number | "">) => {
    onChange(e.target.value as string | number | "");
  };

  return (
    <div
      className={classes.wrapper}
      style={{ width: width ?? (fullWidth ? "100%" : undefined) }}
    >
      <span className={classes.label}>{required ? `${label} *` : label}</span>

      <Select
        value={value}
        onChange={handleChange}
        displayEmpty
        disabled={disabled}
        error={error}
        fullWidth={fullWidth || !!width}
        variant="outlined"
        sx={{
          ...selectSx,
          ...(height !== undefined && {
            height,
            "& .MuiSelect-select": {
              paddingTop: 0,
              paddingBottom: 0,
              paddingLeft: "14px",
              paddingRight: "36px !important",
              display: "flex",
              alignItems: "center",
              height: "100%",
              boxSizing: "border-box",
            },
          }),
        }}
        MenuProps={{ PaperProps: { sx: menuPaperSx } }}
      >
        {placeholder && (
          <MenuItem
            value=""
            disabled
            sx={{ color: theme.colors.text.secondary }}
          >
            {placeholder}
          </MenuItem>
        )}
        {options.map((opt) => (
          <MenuItem key={opt.value} value={opt.value}>
            {opt.label}
          </MenuItem>
        ))}
      </Select>

      {helperText && (
        <span
          className={classes.helperText}
          style={{
            color: error
              ? theme.colors.status.error
              : theme.colors.text.secondary,
          }}
        >
          {helperText}
        </span>
      )}
    </div>
  );
}
