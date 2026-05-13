import { Theme } from "@/utils/theme";

export const ClusterMultiSelectStyles = (theme: Theme) => ({
  select: {
    height: "40px",
    minWidth: "200px",
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    fontSize: theme.typography.fontSize.sm,
    fontFamily: theme.typography.fontFamily,
    color: theme.colors.text.primary,
    "& .MuiOutlinedInput-notchedOutline": {
      borderColor: theme.colors.border.light,
    },
    "&:hover .MuiOutlinedInput-notchedOutline": {
      borderColor: theme.colors.border.main,
    },
    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
      borderColor: theme.colors.primary.main,
      borderWidth: "1px",
    },
    "& .MuiSelect-select": {
      padding: "0 12px",
      display: "flex",
      alignItems: "center",
    },
  },
  placeholder: {
    color: theme.colors.text.disabled,
    fontSize: theme.typography.fontSize.sm,
  },
  menuItem: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: theme.typography.fontSize.sm,
    fontFamily: theme.typography.fontFamily,
    padding: "6px 12px",
  },
  colorDot: {
    width: "10px",
    height: "10px",
    borderRadius: "50%",
    flexShrink: 0,
  },
  chipRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    flexWrap: "wrap" as const,
    overflow: "hidden",
  },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "2px 8px",
    borderRadius: "999px",
    fontSize: "0.7rem",
    fontWeight: 600,
    lineHeight: 1.4,
    maxWidth: "120px",
    overflow: "hidden",
    whiteSpace: "nowrap" as const,
    textOverflow: "ellipsis",
  },
});
