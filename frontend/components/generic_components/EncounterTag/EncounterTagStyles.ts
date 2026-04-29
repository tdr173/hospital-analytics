import { Theme } from "@/utils/theme";

const tag = (bg: string, color: string) => ({
  backgroundColor: bg,
  color,
});

export const EncounterTagStyles = (_theme: Theme) => ({
  base: {
    display: "inline-block",
    fontSize: "0.68rem",
    fontWeight: 700,
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    borderRadius: "4px",
    padding: "2px 8px",
    whiteSpace: "nowrap" as const,
  },
  ambulatory: tag("#dbeafe", "#1d4ed8"),
  emergency: tag("#fee2e2", "#b91c1c"),
  home: tag("#d1fae5", "#065f46"),
  hospice: tag("#f3e8ff", "#6b21a8"),
  inpatient: tag("#ede9fe", "#5b21b6"),
  outpatient: tag("#e0f2fe", "#0369a1"),
  snf: tag("#fef9c3", "#854d0e"),
  urgentcare: tag("#ffedd5", "#c2410c"),
  virtual: tag("#f0fdf4", "#166534"),
  wellness: tag("#d1fae5", "#065f46"),
  other: tag("#f1f5f9", "#475569"),
});
