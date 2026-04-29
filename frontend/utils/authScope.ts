import type { AuthUser } from "@/store/slices/auth/auth-slice";

const STORAGE_KEY = "hospitai.auth";

export function readAuthUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function appendScope(q: URLSearchParams): URLSearchParams {
  const user = readAuthUser();
  if (!user) return q;
  q.set("role", user.role);
  if (user.patientId) q.set("patientId", user.patientId);
  if (user.providerId) q.set("providerId", user.providerId);
  return q;
}

export function scopeSuffix(): string {
  const q = new URLSearchParams();
  appendScope(q);
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function appendScopeToUrl(url: string): string {
  const user = readAuthUser();
  if (!user) return url;
  const hasQuery = url.includes("?");
  const parts: string[] = [`role=${user.role}`];
  if (user.patientId) parts.push(`patientId=${encodeURIComponent(user.patientId)}`);
  if (user.providerId) parts.push(`providerId=${encodeURIComponent(user.providerId)}`);
  return `${url}${hasQuery ? "&" : "?"}${parts.join("&")}`;
}
