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
