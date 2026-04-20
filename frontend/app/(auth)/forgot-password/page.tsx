"use client";

import { useState } from "react";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import LockResetIcon from "@mui/icons-material/LockReset";
import Link from "next/link";
import * as yup from "yup";
import useClasses from "@/utils/useClasses";
import { ForgotPasswordPageStyles } from "./styles";

const emailSchema = yup
  .string()
  .required("This field is required.")
  .email("Please introduce a valid email.");

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
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

    setSent(true);
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
        a link to reset your password.
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

          <Link href="/login" className={classes.backLink}>
            Back to login
          </Link>
        </form>
      )}
    </div>
  );
}
