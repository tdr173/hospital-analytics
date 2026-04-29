"use client";

import Select, { SelectChangeEvent } from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import Checkbox from "@mui/material/Checkbox";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import theme from "@/utils/theme";
import { DropdownOption } from "@/components/generic_components/StyledDropdown/StyledDropdown";
import useClasses from "@/utils/useClasses";
import { StyledMultiDropdownStyles } from "./StyledMultiDropdownStyles";
import TruncatedText from "@/components/generic_components/TruncatedText/TruncatedText";

interface StyledMultiDropdownProps {
  label: string;
  value: (string | number)[];
  onChange: (value: (string | number)[]) => void;
  options: DropdownOption[];
  placeholder?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  required?: boolean;
  fullWidth?: boolean;
  width?: string | number;
  height?: string | number;
  onClear?: () => void;
  showSelectAll?: boolean;
}

const selectSx = {
  fontFamily: theme.typography.fontFamily,
  fontSize: theme.typography.fontSize.sm,
  color: theme.colors.text.primary,
  backgroundColor: theme.colors.surface.containerLow,
  borderRadius: theme.borderRadius.md,
  transition: "box-shadow 0.15s ease, background-color 0.15s ease",
  "& .MuiSelect-select": {
    padding: "8px 14px",
    paddingRight: "36px !important",
    minHeight: "unset !important",
    overflow: "hidden",
    minWidth: 0, // CRITICAL
  },
  "& .MuiOutlinedInput-notchedOutline": { border: "none" },
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
    "& .MuiOutlinedInput-notchedOutline": { border: "none" },
  },
  "& .MuiSelect-icon": {
    color: theme.colors.text.secondary,
    right: "6px",
    top: "50%",
    transform: "translateY(-50%)",
    position: "absolute",
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
    padding: "6px 14px",
    gap: "6px",
    "&:hover": {
      backgroundColor: theme.colors.surface.containerLow,
    },
    "&.Mui-selected": {
      backgroundColor: "transparent",
      "&:hover": { backgroundColor: theme.colors.surface.containerLow },
    },
  },
};

const SELECT_ALL = "__select_all__";

export default function StyledMultiDropdown({
  label,
  value,
  onChange,
  options,
  placeholder = "Select...",
  disabled = false,
  error = false,
  helperText,
  required = false,
  fullWidth = false,
  width,
  height = 40,
  onClear,
  showSelectAll = true,
}: StyledMultiDropdownProps) {
  const classes = useClasses(StyledMultiDropdownStyles, {
    name: "StyledMultiDropdown",
  });

  const allValues = options.map((o) => o.value);
  const allSelected =
    allValues.length > 0 && allValues.every((v) => value.includes(v));
  const someSelected = value.length > 0 && !allSelected;

  const handleChange = (e: SelectChangeEvent<(string | number)[]>) => {
    const raw = e.target.value;
    const val = typeof raw === "string" ? raw.split(",") : raw;
    if (val.includes(SELECT_ALL)) {
      onChange(allSelected ? [] : allValues);
    } else {
      onChange(val);
    }
  };

  const renderValue = (selected: (string | number)[]) => {
    if (selected.length === 0) {
      return (
        <div
          className={classes.placeholderText}
          style={{ width: "100%", overflow: "hidden" }}
        >
          <TruncatedText text={placeholder} />
        </div>
      );
    }
    if (allSelected) {
      return (
        <div style={{ width: "100%", overflow: "hidden" }}>
          <TruncatedText text="All" />
        </div>
      );
    }
    if (selected.length === 1) {
      const opt = options.find((o) => o.value === selected[0]);
      const displayLabel = opt?.label ?? String(selected[0]);
      return (
        <div style={{ width: "100%", overflow: "hidden" }}>
          <TruncatedText text={displayLabel} />
        </div>
      );
    }
    return (
      <span
        className={classes.countText}
        style={{ width: "100%", overflow: "hidden", display: "block" }}
      >
        <TruncatedText text={`+${selected.length}`} />
      </span>
    );
  };

  return (
    <div
      className={classes.wrapper}
      style={{ width: width ?? (fullWidth ? "100%" : undefined) }}
    >
      <span className={classes.label} style={{ marginBottom: "6px" }}>
        {required ? `${label} *` : label}
      </span>

      <Select
        multiple
        value={value}
        onChange={handleChange}
        displayEmpty
        disabled={disabled}
        error={error}
        fullWidth={fullWidth || !!width}
        variant="outlined"
        renderValue={renderValue}
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
              overflow: "hidden",
              minWidth: 0, // CRITICAL
            },
          }),
        }}
        MenuProps={{ PaperProps: { sx: menuPaperSx } }}
        IconComponent={() =>
          value.length > 0 && onClear && !disabled ? (
            <IconButton
              size="small"
              onMouseDown={(e) => {
                e.stopPropagation();
                e.preventDefault();
                onClear();
              }}
              sx={{
                position: "absolute",
                right: "4px",
                padding: "3px",
                color: theme.colors.text.secondary,
              }}
            >
              <CloseIcon sx={{ fontSize: "1rem" }} />
            </IconButton>
          ) : (
            <ExpandMoreIcon
              sx={{
                fontSize: "1.25rem",
                color: theme.colors.text.secondary,
                position: "absolute",
                right: "8px",
                pointerEvents: "none",
              }}
            />
          )
        }
      >
        {showSelectAll && (
          <MenuItem
            value={SELECT_ALL}
            sx={{
              borderBottom: `1px solid`,
              borderColor: "divider",
              fontWeight: 600,
            }}
          >
            <Checkbox
              checked={allSelected}
              indeterminate={someSelected}
              size="small"
              sx={{
                padding: 0,
                color: theme.colors.grey[400],
                "&.Mui-checked, &.MuiCheckbox-indeterminate": {
                  color: theme.colors.primary.main,
                },
              }}
            />
            Select All
          </MenuItem>
        )}
        {options.map((opt) => (
          <MenuItem key={opt.value} value={opt.value}>
            <Checkbox
              checked={value.includes(opt.value)}
              size="small"
              sx={{
                padding: 0,
                color: theme.colors.grey[400],
                "&.Mui-checked": { color: theme.colors.primary.main },
              }}
            />
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
