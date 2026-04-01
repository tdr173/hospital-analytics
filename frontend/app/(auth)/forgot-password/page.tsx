"use client";

import { useState } from "react";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import LockResetIcon from "@mui/icons-material/LockReset";
import Link from "next/link";
import * as yup from "yup";

const emailSchema = yup
  .string()
  .required("This field is required.")
  .email("Please introduce a valid email.");

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    try {
      await emailSchema.validate(email);
    } catch (err: any) {
      setError(err.message);
      return;
    }

    setSent(true);
  };

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "400px",
        padding: "40px",
        backgroundColor: "#ffffff",
        borderRadius: "12px",
        boxShadow: "0px 12px 32px rgba(25, 28, 30, 0.06)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          marginBottom: "24px",
        }}
      >
        <div
          style={{
            width: "56px",
            height: "56px",
            borderRadius: "14px",
            backgroundColor: "#f2f4f6",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <LockResetIcon sx={{ color: "#0891B2", fontSize: "28px" }} />
        </div>
      </div>

      <h1
        style={{
          fontFamily: '"Manrope", sans-serif',
          fontSize: "1.5rem",
          fontWeight: 700,
          color: "#191c1e",
          textAlign: "center",
          marginBottom: "8px",
        }}
      >
        Reset your password
      </h1>
      <p
        style={{
          fontFamily: '"Inter", sans-serif',
          fontSize: "0.875rem",
          color: "#6b7280",
          textAlign: "center",
          marginBottom: "32px",
          lineHeight: 1.5,
        }}
      >
        Enter the email address associated with your account and we&apos;ll send
        a link to reset your password.
      </p>

      {sent ? (
        <div style={{ textAlign: "center" }}>
          <p
            style={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.875rem",
              color: "#0891B2",
              marginBottom: "24px",
            }}
          >
            If an account exists for <strong>{email}</strong>, you will receive
            a password reset link shortly.
          </p>
          <Link
            href="/login"
            style={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.875rem",
              color: "#0891B2",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Back to login
          </Link>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          noValidate
          style={{ display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <StyledInput
            label="Email Address"
            type="email"
            required
            placeholder="clinician@hospital.org"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={!!error}
            helperText={error}
          />

          <StyledButton
            variant="secondary"
            type="submit"
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
            }}
          >
            Send reset link
          </StyledButton>

          <Link
            href="/login"
            style={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.875rem",
              color: "#6b7280",
              textDecoration: "none",
              textAlign: "center",
            }}
          >
            Back to login
          </Link>
        </form>
      )}
    </div>
  );
}
