/**
 * Global fetch interceptor: injects `Authorization: Bearer <jwt>` on every
 * request that targets one of our microservice hosts.
 *
 * The token is read from the same `hospitai.auth` localStorage entry that
 * auth-slice persists. Done as a one-time monkey-patch on the global fetch
 * so existing thunks (which use raw `fetch`) get the header for free.
 *
 * The patch is idempotent (guarded by a flag on window) and a no-op on
 * the server (SSR path) where `window` is undefined.
 *
 * If the user already set an `Authorization` header on the request, we
 * leave it untouched - the explicit value wins.
 */
import {
  AUTH_BASE,
  USERS_BASE,
  CLINICAL_BASE,
  ANALYTICS_BASE,
  ML_BASE,
  QUEUE_BASE,
} from "./apiBases";

const STORAGE_KEY = "hospitai.auth";
const FLAG = "__hospitai_fetch_patched__";

function readAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { accessToken?: string };
    return parsed?.accessToken ?? null;
  } catch {
    return null;
  }
}

function urlMatchesService(url: string): boolean {
  // Same-origin (no protocol prefix) requests target the page host (e.g. SSR
  // or relative URLs). We treat those as "ours" too. Otherwise check the
  // configured service hosts.
  if (!/^https?:\/\//i.test(url)) return true;
  const bases = [
    AUTH_BASE,
    USERS_BASE,
    CLINICAL_BASE,
    ANALYTICS_BASE,
    ML_BASE,
    QUEUE_BASE,
  ];
  return bases.some((b) => b && url.startsWith(b));
}

function inputToUrl(input: RequestInfo | URL): string {
  if (typeof input === "string") return input;
  if (input instanceof URL) return input.toString();
  return input.url;
}

function hasExplicitAuth(init: RequestInit | undefined): boolean {
  if (!init?.headers) return false;
  if (init.headers instanceof Headers) {
    return init.headers.has("Authorization") || init.headers.has("authorization");
  }
  if (Array.isArray(init.headers)) {
    return init.headers.some(([k]) => k.toLowerCase() === "authorization");
  }
  return Object.keys(init.headers).some((k) => k.toLowerCase() === "authorization");
}

function injectAuthHeader(
  init: RequestInit | undefined,
  token: string,
): RequestInit {
  const next: RequestInit = { ...(init ?? {}) };
  const existing = init?.headers;
  if (existing instanceof Headers) {
    const h = new Headers(existing);
    h.set("Authorization", `Bearer ${token}`);
    next.headers = h;
  } else if (Array.isArray(existing)) {
    next.headers = [...existing, ["Authorization", `Bearer ${token}`]];
  } else {
    next.headers = { ...(existing ?? {}), Authorization: `Bearer ${token}` };
  }
  return next;
}

export function installFetchInterceptor(): void {
  if (typeof window === "undefined") return;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const w = window as any;
  if (w[FLAG]) return;
  w[FLAG] = true;

  const originalFetch = window.fetch.bind(window);
  window.fetch = function patchedFetch(
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> {
    const url = inputToUrl(input);
    if (!urlMatchesService(url) || hasExplicitAuth(init)) {
      return originalFetch(input, init);
    }
    const token = readAccessToken();
    if (!token) return originalFetch(input, init);
    return originalFetch(input, injectAuthHeader(init, token));
  };
}
