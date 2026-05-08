import { apiUrl } from "@/utils/apiBases";

export type UserRole = "MANAGER" | "DOCTOR" | "PATIENT";

export const SEEDED_USERS: Record<string, UserRole> = {
  "patient@hospitai.com": "PATIENT",
  "doctor@hospitai.com": "DOCTOR",
  "manager@hospitai.com": "MANAGER",
};

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  role: UserRole;
  mustChangePassword: boolean;
  patientId?: string | null;
  providerId?: string | null;
  email: string;
}

export interface LoginError {
  status: number;
  message: string;
}

/**
 * Real login against /auth/login. Returns a discriminated result so the
 * caller can render BE error messages (401 wrong creds, 422 validation)
 * without a try/catch dance.
 */
export async function loginUser(
  email: string,
  password: string,
): Promise<
  | { ok: true; data: LoginResponse }
  | { ok: false; error: LoginError }
> {
  let res: Response;
  try {
    res = await fetch(apiUrl("/auth/login"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
      },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return {
      ok: false,
      error: {
        status: 0,
        message: "Network error. Check your connection and try again.",
      },
    };
  }

  if (res.ok) {
    const data = (await res.json()) as LoginResponse;
    return { ok: true, data };
  }

  let detail: string | undefined;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") {
      detail = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      const fieldErr = body.detail[0];
      detail = `${fieldErr.loc?.[1] ?? "field"}: ${fieldErr.msg}`;
    }
  } catch {
    /* ignore */
  }
  const fallback =
    res.status === 401
      ? "Email or password is incorrect."
      : `Login failed (HTTP ${res.status}).`;
  return {
    ok: false,
    error: { status: res.status, message: detail ?? fallback },
  };
}

export interface RegisterUserPayload {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  jobTitle: string;
  role: UserRole;
}

export async function registerUser(_payload: RegisterUserPayload): Promise<void> {
  // await fetch(apiUrl(`/create-user`), {
  //   method: "POST",
  //   headers: {
  //     "Content-Type": "application/json",
  //     "ngrok-skip-browser-warning": "true",
  //   },
  //   body: JSON.stringify(_payload),
  // });
  void _payload;
}

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export async function fetchDemoPatientId(): Promise<string | undefined> {
  try {
    const res = await fetch(apiUrl(`/patients?rows=1&page=1`), {
      headers: defaultHeaders,
    });
    if (!res.ok) return undefined;
    const data = await res.json();
    const first = data?.items?.[0] ?? data?.[0];
    return first?.patient_id ?? first?.patientId;
  } catch {
    return undefined;
  }
}

export async function fetchDemoProviderId(): Promise<string | undefined> {
  try {
    const res = await fetch(apiUrl(`/providers?rows=1&page=1`), {
      headers: defaultHeaders,
    });
    if (!res.ok) return undefined;
    const data = await res.json();
    const first = data?.items?.[0] ?? data?.[0];
    return first?.provider_id ?? first?.providerId;
  } catch {
    return undefined;
  }
}
