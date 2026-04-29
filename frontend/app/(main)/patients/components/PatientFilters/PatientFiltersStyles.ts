import { Theme } from "@/utils/theme";

export const PatientFiltersStyles = (theme: Theme) => ({
  bar: {
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border.main}`,
    backgroundColor: theme.colors.surface.containerLowest,
    display: "grid",
    gridTemplateColumns: "1.6fr 1fr 1fr 1fr 1fr 1fr 1fr",
    gap: theme.spacing.sm,
    alignItems: "flex-end",
  },

  barWithAdd: {
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border.main}`,
    backgroundColor: theme.colors.surface.containerLowest,
    display: "grid",
    gridTemplateColumns: "1.6fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr",
    gap: theme.spacing.sm,
    alignItems: "flex-end",
  },
});
