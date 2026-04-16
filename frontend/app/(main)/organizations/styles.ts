import { Theme } from "@/utils/theme";

export const OrganizationsPageStyles = (theme: Theme) => ({
  pageContainer: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    overflow: "hidden",
    fontFamily: theme.typography.fontFamily,
  },
  filterBar: {
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border.main}`,
    backgroundColor: theme.colors.surface.containerLowest,
    display: "grid",
    gridTemplateColumns: "3fr 1fr 1fr",
    gap: theme.spacing.sm,
    alignItems: "flex-end",
  },
  tableArea: {
    flex: 1,
    overflow: "auto",
    padding: theme.spacing.lg,
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    width: "100%",
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamily,
  },
});
