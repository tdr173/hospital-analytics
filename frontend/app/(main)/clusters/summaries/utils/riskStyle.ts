export interface RiskStyle {
  bg: string;
  color: string;
  dot: string;
  label: string;
}

export const RISK_STYLE: Record<string, RiskStyle> = {
  high: { bg: "#fee2e2", color: "#991b1b", dot: "#ef4444", label: "High Risk" },
  moderate: { bg: "#fef9c3", color: "#854d0e", dot: "#eab308", label: "Moderate Risk" },
  low: { bg: "#dcfce7", color: "#166534", dot: "#22c55e", label: "Low Risk" },
};
