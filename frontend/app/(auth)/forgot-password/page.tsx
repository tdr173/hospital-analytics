"use client";

import { useState } from "react";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import LockResetIcon from "@mui/icons-material/LockReset";
import Link from "next/link";
import * as yup from "yup";
import useClasses from "@/utils/useClasses";
import { apiUrl } from "@/utils/apiBases";
import { ForgotPasswordPageStyles } from "./styles";

const emailSchema = yup
  .string()
  .required("This field is required.")
  .email("Please introduce a valid email.");

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const classes = useClasses(ForgotPasswordPageStyles, { name: "ForgotPasswordPage" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await emailSchema.validate(email);
    } catch (err: any) {
      setError(err.message);
      return;
    }

    setSubmitting(true);
    try {
      // BE always returns 200 here (anti-enumeration). We treat any non-2xx
      // as a generic failure so we don't accidentally reveal account state.
      const res = await fetch(apiUrl("/auth/forgot-password"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        setError("Something went wrong. Please try again.");
        return;
      }
      setSent(true);
    } catch {
      setError("Network error. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={classes.card}>
      <div className={classes.iconRow}>
        <div className={classes.iconBox}>
          <LockResetIcon sx={{ color: "#0891B2", fontSize: "28px" }} />
        </div>
      </div>

      <h1 className={classes.title}>
        Reset your password
      </h1>
      <p className={classes.subtitle}>
        Enter the email address associated with your account and we&apos;ll send
        a link to reset your password. The link is valid for 10 minutes.
      </p>

      {sent ? (
        <div className={classes.sentContainer}>
          <p className={classes.sentText}>
            If an account exists for <strong>{email}</strong>, you will receive
            a password reset link shortly.
          </p>
          <Link href="/login" className={classes.link}>
            Back to login
          </Link>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          noValidate
          className={classes.form}
        >
          <StyledInput
            label="Email Address"
            type="email"
            required
            placeholder="doctor@hospital.org"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={!!error}
            helperText={error}
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
              "&:hover": {
                backgroundColor: "#0e7490",
              },
              "&:disabled": {
                backgroundColor: "#a3d4e0",
              },
            }}
          >
            {submitting ? "Sending…" : "Send reset link"}
          </StyledButton>

          <Link href="/login" className={classes.backLink}>
            Back to login
          </Link>
        </form>
      )}
    </div>
  );
}
