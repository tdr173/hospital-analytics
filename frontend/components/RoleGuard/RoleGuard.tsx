"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "@/store";
import { setScopeIds, login } from "@/store/slices/auth/auth-slice";
import type { UserRole } from "@/store/slices/auth/thunks";
import { isRouteAllowedForRole } from "@/utils/rolePermissions";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function RoleGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const dispatch = useAppDispatch();
  const user = useSelector((s: RootState) => s.auth.user);

  useEffect(() => {
    const roleParam = searchParams.get("role") as UserRole | null;
    const patientParam = searchParams.get("patientId") ?? undefined;
    const providerParam = searchParams.get("providerId") ?? undefined;

    if (!roleParam && !patientParam && !providerParam) return;

    if (roleParam && roleParam !== user?.role) {
      dispatch(
        login({
          email: user?.email ?? `${roleParam.toLowerCase()}@hospitai.com`,
          role: roleParam,
          patientId: patientParam,
          providerId: providerParam,
        }),
      );
    } else if (patientParam || providerParam) {
      dispatch(
        setScopeIds({ patientId: patientParam, providerId: providerParam }),
      );
    }
  }, [searchParams, user, dispatch]);

  useEffect(() => {
    if (!user) return;
    if (!isRouteAllowedForRole(pathname, user.role)) {
      router.replace("/home");
      return;
    }
    if (
      user.role === "PATIENT" &&
      pathname.startsWith("/patients")
    ) {
      router.replace("/home");
      return;
    }
    if (
      user.role === "PATIENT" &&
      pathname.startsWith("/encounters/") &&
      pathname !== "/encounters"
    ) {
      // Backend ownership check handles the data, UI just shows empty if denied.
    }
  }, [pathname, user, router]);

  return <>{children}</>;
}
