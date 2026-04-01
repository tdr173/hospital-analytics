import moment from "moment";

export function hexToHexa(hex: string, alpha: number): string {
  const a = Math.round(alpha * 255)
    .toString(16)
    .padStart(2, "0");
  return `${hex}${a}`;
}

export function clearName(firstName: string | null, lastName: string | null) {
  firstName = firstName ?? "";
  lastName = lastName ?? "";
  return `${firstName.replace(/\d+/g, "")} ${lastName.replace(/\d+/g, "")}`.trim();
}

export function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return "-";
  return moment(dateStr).format("DD.MM.YYYY");
}
