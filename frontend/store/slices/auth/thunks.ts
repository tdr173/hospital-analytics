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

export const DEMO_PATIENT_ID = "8ceaad7c-9545-e79c-17b2-47c7d3c17b87";
export const DEMO_PROVIDER_ID = "1dc97cc3-c9d9-341b-9b32-a34b4c4b79ff";

export async function fetchDemoPatientId(): Promise<string | undefined> {
  return DEMO_PATIENT_ID;
}

export async function fetchDemoProviderId(): Promise<string | undefined> {
  return DEMO_PROVIDER_ID;
}
