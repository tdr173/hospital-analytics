const MONTH_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

export function formatDay(iso: string): string {
  const [, month, day] = iso.split("-");
  const monthIdx = Number(month) - 1;
  const dayNum = Number(day);
  if (Number.isNaN(monthIdx) || Number.isNaN(dayNum)) return iso;
  const monthLabel = MONTH_SHORT[monthIdx] ?? "";
  return `${String(dayNum).padStart(2, "0")} ${monthLabel}`;
}

export function formatMonth(iso: string): string {
  const [year, month] = iso.split("-");
  const monthIdx = Number(month) - 1;
  if (Number.isNaN(monthIdx)) return iso;
  const monthLabel = MONTH_SHORT[monthIdx] ?? "";
  return `${monthLabel} ${year}`;
}

export function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}...` : text;
}

export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
