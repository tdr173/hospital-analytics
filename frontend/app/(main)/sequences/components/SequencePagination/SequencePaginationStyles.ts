import { Theme } from "@/utils/theme";

export const SequencePaginationStyles = (theme: Theme) => ({
  bar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: theme.spacing.md,
    padding: `${theme.spacing.md} 0`,
  },
  info: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
  controls: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
  },
  button: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: `${theme.spacing.xs} ${theme.spacing.md}`,
    backgroundColor: theme.colors.surface.containerLowest,
    color: theme.colors.text.primary,
    border: `1px solid ${theme.colors.border.main}`,
    borderRadius: theme.borderRadius.md,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.semibold,
    fontFamily: theme.typography.fontFamily,
    cursor: "pointer",
    transition: "background 0.15s",
    "&:hover:not(:disabled)": {
      backgroundColor: theme.colors.surface.containerLow,
    },
    "&:disabled": {
      opacity: 0.5,
      cursor: "not-allowed",
    },
  },
  pageLabel: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    padding: `0 ${theme.spacing.sm}`,
  },
});
