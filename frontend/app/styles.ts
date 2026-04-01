import { Theme } from "@/utils/theme";

export const NotFoundStyles = (_theme: Theme) => ({
  container: {
    padding: "48px 24px",
    textAlign: "center" as const,
    height: "100vh",
    display: "flex",
    flexDirection: "column" as const,
    justifyContent: "center",
    alignItems: "center",
  },
});
