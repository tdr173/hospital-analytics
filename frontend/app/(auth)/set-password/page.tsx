"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import VpnKeyOutlinedIcon from "@mui/icons-material/VpnKeyOutlined";
import Link from "next/link";
import * as yup from "yup";
import useClasses from "@/utils/useClasses";
import { apiUrl } from "@/utils/apiBases";
import { SetPasswordPageStyles } from "./styles";

const passwordSchema = yup.object({
  newPassword: yup
    .string()
    .required("This field is required.")
    .min(8, "Password must be at least 8 characters long."),
  confirmPassword: yup
    .string()
    .required("Please confirm your password.")
    .oneOf([yup.ref("newPassword")], "Passwords do not match."),
});

function SetPasswordInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errors, setErrors] = useState<{
    newPassword?: string;
    confirmPassword?: string;
  }>({});
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const classes = useClasses(SetPasswordPageStyles, { name: "SetPasswordPage" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSubmitError("");

    if (!token) {
      setSubmitError(
        "This link is missing a token. Request a new password-reset link from /forgot-password.",
      );
      return;
    }

    try {
      await passwordSchema.validate(
        { newPassword, confirmPassword },
        { abortEarly: false },
      );
    } catch (err: any) {
      const fieldErrors: typeof errors = {};
      err.inner.forEach((e: any) => {
        if (e.path && !fieldErrors[e.path as keyof typeof fieldErrors]) {
          fieldErrors[e.path as keyof typeof fieldErrors] = e.message;
        }
      });
      setErrors(fieldErrors);
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(apiUrl("/auth/set-password"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({ token, new_password: newPassword }),
      });
      if (!res.ok) {
        let detail = "Could not set password. The link may have expired.";
        try {
          const body = await res.json();
          if (typeof body?.detail === "string") detail = body.detail;
        } catch {
          /* ignore */
        }
        setSubmitError(detail);
        return;
      }
      setDone(true);
    } catch {
      setSubmitError(
        "Network error. Check your connection and try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={classes.card}>
      <div className={classes.iconRow}>
        <div className={classes.iconBox}>
          <VpnKeyOutlinedIcon sx={{ color: "#0891B2", fontSize: "28px" }} />
        </div>
      </div>

      <h1 className={classes.title}>Set your password</h1>
      <p className={classes.subtitle}>
        Choose a new password to finish setting up or recovering your account.
        This link is valid for 10 minutes.
      </p>

      {done ? (
        <div className={classes.successContainer}>
          <p className={classes.successText}>
            Password updated. You can now sign in.
          </p>
          <StyledButton
            variant="secondary"
            type="button"
            onClick={() => router.push("/login")}
            sx={{
              width: "100%",
              padding: "12px",
              fontSize: "0.875rem",
              backgroundColor: "#0891B2",
              color: "#ffffff",
              border: "none",
              "&:hover": { backgroundColor: "#0e7490" },
            }}
          >
            Go to login
          </StyledButton>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className={classes.form}>
          {submitError ? (
            <div className={classes.errorBanner}>{submitError}</div>
          ) : null}

          <StyledInput
            label="New Password"
            type="password"
            required
            placeholder="At least 8 characters"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            error={!!errors.newPassword}
            helperText={errors.newPassword}
          />
          <StyledInput
            label="Confirm Password"
            type="password"
            required
            placeholder="Re-enter your new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            error={!!errors.confirmPassword}
            helperText={errors.confirmPassword}
          />

          <StyledButton
            variant="secondary"
            type="submit"
            disabled={submitting}
            sx={{
              width: "100%",
              padding: "12px",
              fontSize: "0.875rem",
              backgroundColor: "#0891B2",
              color: "#ffffff",
              border: "none",
              "&:hover": { backgroundColor: "#0e7490" },
              "&:disabled": { backgroundColor: "#a3d4e0" },
            }}
          >
            {submitting ? "Saving…" : "Set password"}
          </StyledButton>

          <Link href="/login" className={classes.backLink}>
            Back to login
          </Link>
        </form>
      )}
    </div>
  );
}

export default function SetPasswordPage() {
  // useSearchParams must be inside a Suspense boundary in Next.js App Router.
  return (
    <Suspense fallback={null}>
      <SetPasswordInner />
    </Suspense>
  );
}
