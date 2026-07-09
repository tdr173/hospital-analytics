import { Theme } from "@/utils/theme";

export const SequenceFiltersStyles = (theme: Theme) => ({
  bar: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    display: "grid",
    gridTemplateColumns: "1fr auto auto auto",
    gap: theme.spacing.md,
    alignItems: "end",
    // as a flex item of the scroll container, min-width:auto would let the bar
    // grow to its content's min size (so the fields widen when a clear icon
    // appears). Pinning it to 0 keeps the bar at container width and forces the
    // minmax(0, ...fr) tracks to absorb the change instead.
    width: "100%",
    minWidth: 0,
    maxWidth: "100%",
    boxSizing: "border-box" as const,
    "@media (max-width: 900px)": {
      gridTemplateColumns: "1fr",
    },
  },
  fieldGroup: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "4px",
    // allow grid columns to shrink so fields fill (and never exceed) their
    // share of the bar instead of growing to their content width
    minWidth: 0,
  },
  fieldLabel: {
    fontSize: "0.65rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  sortDirectionButton: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    height: "42px",
    padding: `0 ${theme.spacing.md}`,
    backgroundColor: theme.colors.surface.containerLow,
    color: theme.colors.text.primary,
    border: `1px solid ${theme.colors.border.light}`,
    borderRadius: theme.borderRadius.md,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.semibold,
    fontFamily: theme.typography.fontFamily,
    cursor: "pointer",
    transition: "background 0.15s, color 0.15s",
    "&:hover": {
      backgroundColor: theme.colors.surface.containerHighest,
    },
  },
  resultCount: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    padding: `0 ${theme.spacing.lg}`,
  },
});
