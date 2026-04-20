import { API_BASE } from "@/store/slices/clusters/thunks";

export type UserRole = "MANAGER" | "DOCTOR" | "PATIENT";

export const SEEDED_USERS: Record<string, UserRole> = {
  "patient@hospitai.com": "PATIENT",
  "doctor@hospitai.com": "DOCTOR",
  "manager@hospitai.com": "MANAGER",
};

export interface RegisterUserPayload {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  jobTitle: string;
  role: UserRole;
}

export async function registerUser(_payload: RegisterUserPayload): Promise<void> {
  // await fetch(`${API_BASE}/create-user`, {
  //   method: "POST",
  //   headers: {
  //     "Content-Type": "application/json",
  //     "ngrok-skip-browser-warning": "true",
  //   },
  //   body: JSON.stringify(_payload),
  // });
  void API_BASE;
}

const defaultHeaders: Record<string, string> = {
  "ngrok-skip-browser-warning": "true",
};

export async function fetchDemoPatientId(): Promise<string | undefined> {
  try {
    const res = await fetch(`${API_BASE}/patients?rows=1&page=1`, {
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
    const res = await fetch(`${API_BASE}/providers?rows=1&page=1`, {
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
