import { Theme } from "@/utils/theme";

export const GenderBadgeStyles = (theme: Theme) => ({
  empty: {
    color: theme.colors.text.disabled,
  },
  male: {
    display: "inline-flex",
    alignItems: "center",
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.75rem",
    color: theme.colors.gender.male,
    backgroundColor: theme.colors.gender.maleBg,
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },
  female: {
    display: "inline-flex",
    alignItems: "center",
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.75rem",
    color: theme.colors.gender.female,
    backgroundColor: theme.colors.gender.femaleBg,
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },
});
