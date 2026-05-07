import { Theme } from "@/utils/theme";

const ContinuationsTabStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    paddingBottom: theme.spacing.xs,
    flexWrap: "wrap" as const,
  },
  toolbarLabel: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    fontWeight: theme.typography.fontWeight.semibold,
  },
  nSelect: {
    minWidth: "70px",
    fontFamily: theme.typography.fontFamily,
    "& .MuiSelect-select": {
      padding: "6px 12px",
      fontSize: theme.typography.fontSize.sm,
    },
    "& .MuiOutlinedInput-notchedOutline": {
      borderColor: theme.colors.border.dark,
    },
  },
  toolbarHint: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
  },
  list: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minHeight: "200px",
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
    fontSize: theme.typography.fontSize.sm,
    textAlign: "center" as const,
    padding: theme.spacing.lg,
  },
});

export default ContinuationsTabStyles;
