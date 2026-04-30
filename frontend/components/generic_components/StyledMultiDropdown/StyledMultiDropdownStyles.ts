import { Theme } from "@/utils/theme";

export const StyledMultiDropdownStyles = (theme: Theme) => ({
  wrapper: {
    display: "flex",
    flexDirection: "column" as const,
    minWidth: 0,
  },
  label: {
    fontFamily: '"Inter", sans-serif',
    fontSize: "0.75rem",
    fontWeight: 700,
    color: "#6b7280",
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
    position: "relative",
    transform: "none",
    marginBottom: "6px",
    margin: 0,
    display: "block",
  },
  placeholderText: {
    color: theme.colors.text.secondary,
  },
  countText: {
    color: theme.colors.text.secondary,
  },
  helperText: {
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.75rem",
    margin: 0,
    marginTop: "4px",
  },
});
