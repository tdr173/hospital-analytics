import { Theme } from "@/utils/theme";

export const AuthLayoutStyles = (theme: Theme) => ({
  root: {
    display: "flex",
    flexDirection: "column" as const,
    minHeight: "100vh",
    backgroundColor: theme.colors.surface.base,
    position: "relative" as const,
  },
  logoContainer: {
    height: "70px",
    width: theme.layout.sidebarWidth,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "0 14px",
    gap: "4px",
    position: "absolute" as const,
  },
  logoText: {
    fontSize: "24px",
    fontWeight: 700,
    color: "#191c1e",
    lineHeight: 1.2,
    fontFamily: '"Inter", sans-serif',
    letterSpacing: "-0.02em",
  },
  body: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
});
