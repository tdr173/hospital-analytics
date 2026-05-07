import { Theme } from "@/utils/theme";

const sequencesTabStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
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
    flex: 1,
    height: "100%",
    width: "100%",
    minHeight: "200px",
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
    fontSize: theme.typography.fontSize.sm,
  },
});

export default sequencesTabStyles;
