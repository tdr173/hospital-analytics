import { Theme } from "@/utils/theme";

export const ForgotPasswordPageStyles = (_theme: Theme) => ({
  card: {
    width: "100%",
    maxWidth: "400px",
    padding: "40px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    boxShadow: "0px 12px 32px rgba(25, 28, 30, 0.06)",
  },
  iconRow: {
    display: "flex",
    justifyContent: "center",
    marginBottom: "24px",
  },
  iconBox: {
    width: "56px",
    height: "56px",
    borderRadius: "14px",
    backgroundColor: "#f2f4f6",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontFamily: '"Manrope", sans-serif',
    fontSize: "1.5rem",
    fontWeight: 700,
    color: "#191c1e",
    textAlign: "center" as const,
    marginBottom: "8px",
  },
  subtitle: {
    fontFamily: '"Inter", sans-serif',
    fontSize: "0.875rem",
    color: "#6b7280",
    textAlign: "center" as const,
    marginBottom: "32px",
    lineHeight: 1.5,
  },
  form: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "20px",
  },
  sentContainer: {
    textAlign: "center" as const,
  },
  sentText: {
    fontFamily: '"Inter", sans-serif',
    fontSize: "0.875rem",
    color: "#0891B2",
    marginBottom: "24px",
  },
  link: {
    fontFamily: '"Inter", sans-serif',
    fontSize: "0.875rem",
    color: "#0891B2",
    fontWeight: 600,
    textDecoration: "none",
  },
  backLink: {
    fontFamily: '"Inter", sans-serif',
    fontSize: "0.875rem",
    color: "#6b7280",
    textDecoration: "none",
    textAlign: "center" as const,
  },
});
