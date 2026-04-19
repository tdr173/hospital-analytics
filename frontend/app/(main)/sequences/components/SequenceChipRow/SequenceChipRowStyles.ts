import { Theme } from "@/utils/theme";

export const SequenceChipRowStyles = (theme: Theme) => ({
  wrapper: {
    overflow: "hidden",
    minWidth: 0,
    width: "100%",
  },
  row: {
    display: "flex",
    flexWrap: "nowrap" as const,
    alignItems: "center",
    gap: "6px",
    overflowX: "auto" as const,
    overflowY: "hidden" as const,
    paddingBottom: "4px",
    scrollbarWidth: "thin" as const,
    scrollbarColor: `${theme.colors.primary.main} transparent`,
    "&::-webkit-scrollbar": { height: "4px" },
    "&::-webkit-scrollbar-track": { background: "transparent" },
    "&::-webkit-scrollbar-thumb": {
      backgroundColor: theme.colors.primary.main,
      borderRadius: "4px",
    },
  },
  step: {
    display: "inline-flex",
    alignItems: "center",
    flexShrink: 0,
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
    flexShrink: 0,
  },
});
