import { Theme } from "@/utils/theme";

const headerStyles = (theme: Theme) => ({
  headerContainer: {
    backgroundColor: theme.colors.surface.containerLowest,
    height: "70px",
    width: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0px 24px",
    boxShadow: theme.shadows.sm,
    borderBottom: `1px solid #E8EAED`,
  },
  pageTitle: {
    fontSize: "1.1rem",
    fontWeight: 600,
    color: theme.colors.text.primary,
    fontFamily: theme.typography.fontFamilyHeading,
    lineHeight: 1,
    letterSpacing: "-0.01em",
  },
});

export default headerStyles;
