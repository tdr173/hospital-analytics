export const PersonalLlmSummaryCardStyles = {
  card: {
    backgroundColor: "#ffffff",
    border: "1px solid #E5E7EB",
    borderRadius: "12px",
    padding: "20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  header: {
    fontSize: "1rem",
    fontWeight: 600,
    color: "#0F172A",
    marginBottom: "12px",
  },
  body: {
    color: "#334155",
    fontSize: "0.9rem",
    lineHeight: 1.55,
  },
  markdown: {
    whiteSpace: "pre-wrap" as const,
    fontFamily: "inherit",
    margin: 0,
  },
  error: {
    color: "#B91C1C",
  },
};
