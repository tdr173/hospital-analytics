/**
 * Service base URLs. Each backend microservice is exposed at its own host
 * via Traefik (host-based routing). In dev outside docker-compose, set
 * NEXT_PUBLIC_*_URL to http://localhost:8000 to point everything at a
 * single monolith.
 */
const env = (k: string, fallback: string): string =>
  (typeof process !== "undefined" && process.env?.[k]) || fallback;

export const AUTH_BASE      = env("NEXT_PUBLIC_AUTH_URL",      "http://auth.localhost");
export const USERS_BASE     = env("NEXT_PUBLIC_USERS_URL",     "http://users.localhost");
export const CLINICAL_BASE  = env("NEXT_PUBLIC_CLINICAL_URL",  "http://clinical.localhost");
export const ANALYTICS_BASE = env("NEXT_PUBLIC_ANALYTICS_URL", "http://analytics.localhost");
export const ML_BASE        = env("NEXT_PUBLIC_ML_URL",        "http://ml.localhost");
export const QUEUE_BASE     = env("NEXT_PUBLIC_QUEUE_URL",     "http://queue.localhost");

/**
 * Map a path beginning with a known prefix to the correct service base URL.
 * Falls back to CLINICAL_BASE for anything unrecognized.
 *
 * Path prefixes:
 *   /auth/*        → auth
 *   /users/*       → users
 *   /patients/*    → clinical-core
 *   /providers/*   → clinical-core
 *   /encounters/*  → clinical-core
 *   /statistics/*  → analytics
 *   /dashboard/*   → analytics
 *   /clusters/*    → ml-batch
 *   /sequences/*   → ml-batch
 *   /jobs/*        → queue-service
 */
export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  if (p.startsWith("/auth"))       return `${AUTH_BASE}${p}`;
  if (p.startsWith("/users"))      return `${USERS_BASE}${p}`;
  if (p.startsWith("/patients"))   return `${CLINICAL_BASE}${p}`;
  if (p.startsWith("/providers"))  return `${CLINICAL_BASE}${p}`;
  if (p.startsWith("/encounters")) return `${CLINICAL_BASE}${p}`;
  if (p.startsWith("/statistics")) return `${ANALYTICS_BASE}${p}`;
  if (p.startsWith("/dashboard"))  return `${ANALYTICS_BASE}${p}`;
  if (p.startsWith("/clusters"))   return `${ML_BASE}${p}`;
  if (p.startsWith("/sequences"))  return `${ML_BASE}${p}`;
  if (p.startsWith("/jobs"))       return `${QUEUE_BASE}${p}`;
  return `${CLINICAL_BASE}${p}`;
}

/**
 * Backwards-compatible shim. Returns a string that, when concatenated with
 * a leading-slash path, produces the correct service URL.
 *
 * Implemented as a Proxy over a function so that:
 *   `${API_BASE}/patients` → CLINICAL_BASE/patients
 *   `${API_BASE}/clusters` → ML_BASE/clusters
 *
 * This works because template-literal interpolation calls toString(), and
 * we override toString to inspect the surrounding context via a marker
 * pattern. To avoid that complexity we instead require call sites to use
 * `apiUrl("/path")`. The legacy `API_BASE` re-export below points at
 * CLINICAL_BASE so old code that wasn't updated still resolves *something*.
 */
export const API_BASE = CLINICAL_BASE;
