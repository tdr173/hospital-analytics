import type { UserRole } from "@/store/slices/auth/thunks";

export interface RouteRoles {
  prefix: string;
  allowed: UserRole[];
}

export const ROUTE_ROLES: RouteRoles[] = [
  { prefix: "/home", allowed: ["MANAGER", "DOCTOR", "PATIENT"] },
  { prefix: "/statistics", allowed: ["MANAGER"] },
  { prefix: "/clusters", allowed: ["MANAGER"] },
  { prefix: "/sequences", allowed: ["MANAGER"] },
  { prefix: "/patients", allowed: ["MANAGER", "DOCTOR"] },
  { prefix: "/encounters", allowed: ["MANAGER", "DOCTOR", "PATIENT"] },
  { prefix: "/providers", allowed: ["MANAGER", "DOCTOR"] },
  { prefix: "/ask", allowed: ["MANAGER", "DOCTOR"] },
  { prefix: "/register-user", allowed: ["MANAGER"] },
  { prefix: "/users", allowed: ["MANAGER"] },
];

export function isRouteAllowedForRole(
  pathname: string,
  role: UserRole,
): boolean {
  const match = ROUTE_ROLES.find((r) => pathname.startsWith(r.prefix));
  if (!match) return true;
  return match.allowed.includes(role);
}
