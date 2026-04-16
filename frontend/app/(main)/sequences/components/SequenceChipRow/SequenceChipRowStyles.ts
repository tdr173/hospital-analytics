import { Theme } from "@/utils/theme";

export const SequenceChipRowStyles = (theme: Theme) => ({
  row: {
    display: "flex",
    flexWrap: "wrap" as const,
    alignItems: "center",
    gap: "6px",
    rowGap: "8px",
  },
  step: {
    display: "inline-flex",
    alignItems: "center",
    flexWrap: "wrap" as const,
    gap: "4px",
  },
  chip: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "4px 10px",
    borderRadius: theme.borderRadius.sm,
    fontSize: "0.75rem",
    fontWeight: theme.typography.fontWeight.semibold,
    fontFamily: theme.typography.fontFamily,
    border: "1px solid transparent",
    lineHeight: 1.3,
  },
  chipPrefix: {
    fontWeight: theme.typography.fontWeight.bold,
    fontSize: "0.7rem",
    letterSpacing: "0.04em",
    textTransform: "uppercase" as const,
    opacity: 0.85,
  },
  chipValue: {
    fontWeight: theme.typography.fontWeight.semibold,
  },
  arrow: {
    color: theme.colors.text.secondary,
    fontSize: "0.9rem",
    fontWeight: theme.typography.fontWeight.bold,
    userSelect: "none" as const,
  },
});
