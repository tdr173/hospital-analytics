import { toast } from "react-toastify";
import { appendScopeToUrl } from "@/utils/authScope";

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
  "Content-Type": "application/json",
};

async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return res.statusText;
  }
}

async function send<TRes>(
  method: "POST" | "PATCH" | "DELETE",
  url: string,
  body: unknown | undefined,
  label: string,
): Promise<TRes> {
  const scoped = appendScopeToUrl(url);
  const res = await fetch(scoped, {
    method,
    headers: defaultHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await readError(res);
    toast.error(`${label}: ${detail}`, { toastId: `${method}-${label}` });
    throw new Error(`${res.status}`);
  }
  if (res.status === 204) return undefined as TRes;
  return res.json() as Promise<TRes>;
}

export function apiPost<TRes>(url: string, body: unknown, label: string) {
  return send<TRes>("POST", url, body, label);
}

export function apiPatch<TRes>(url: string, body: unknown, label: string) {
  return send<TRes>("PATCH", url, body, label);
}

export function apiDelete(url: string, label: string) {
  return send<void>("DELETE", url, undefined, label);
}
