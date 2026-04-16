import { Theme } from "@/utils/theme";

const sequencesTabStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  countBar: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    padding: `${theme.spacing.xs} 0`,
  },
  list: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  paginationBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing.md,
    padding: `${theme.spacing.sm} 0`,
  },
  position: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamily,
    minWidth: "120px",
    textAlign: "center" as const,
  },
  navButton: {
    color: theme.colors.primary.main,
    "&.Mui-disabled": {
      color: theme.colors.text.disabled,
    },
    "&:hover": {
      backgroundColor: "rgba(0, 103, 128, 0.08)",
    },
  },
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: theme.spacing.xxl,
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.md,
  },
});

export default sequencesTabStyles;
