import { API_BASE } from "@/store/slices/clusters/thunks";

export type UserRole = "MANAGER" | "DOCTOR" | "PATIENT";

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
