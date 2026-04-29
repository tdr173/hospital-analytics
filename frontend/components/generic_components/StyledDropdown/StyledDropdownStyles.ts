import { Theme } from "@/utils/theme";

export const StyledDropdownStyles = (theme: Theme) => ({
  wrapper: {
    display: "flex",
    flexDirection: "column" as const,
  },
  label: {
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.75rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
    margin: 0,
    marginBottom: "6px",
    display: "block",
  },
  helperText: {
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.75rem",
    margin: 0,
    marginTop: "4px",
  },
});
