"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import Link from "next/link";
import * as yup from "yup";

const loginSchema = yup.object({
  email: yup
    .string()
    .required("This field is required.")
    .email("Please introduce a valid email."),
  password: yup
    .string()
    .required("This field is required.")
    .min(8, "Password must be at least 8 characters long."),
});

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {},
  );

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    try {
      await loginSchema.validate({ email, password }, { abortEarly: false });
    } catch (err: any) {
      const fieldErrors: { email?: string; password?: string } = {};
      err.inner.forEach((e: any) => {
        if (e.path && !fieldErrors[e.path as keyof typeof fieldErrors]) {
          fieldErrors[e.path as keyof typeof fieldErrors] = e.message;
        }
      });
      setErrors(fieldErrors);
      return;
    }

    router.push("/statistics/patients");
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
          <LockOutlinedIcon sx={{ color: "#0891B2", fontSize: "28px" }} />
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
        Welcome back
      </h1>
      <p
        style={{
          fontFamily: '"Inter", sans-serif',
          fontSize: "0.875rem",
          color: "#6b7280",
          textAlign: "center",
          marginBottom: "32px",
        }}
      >
        Sign in to your HospitAI account
      </p>

      <form
        onSubmit={handleLogin}
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
          error={!!errors.email}
          helperText={errors.email}
        />
        <StyledInput
          label="Password"
          type="password"
          required
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={!!errors.password}
          helperText={errors.password}
        />

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Link
            href="/forgot-password"
            style={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.8rem",
              color: "#0891B2",
              fontWeight: 600,
              textDecoration: "none",
            }}
          >
            Forgot password?
          </Link>
        </div>

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
          Sign in
        </StyledButton>
      </form>

      <p
        style={{
          fontFamily: '"Inter", sans-serif',
          fontSize: "0.875rem",
          color: "#6b7280",
          textAlign: "center",
          marginTop: "24px",
        }}
      ></p>
    </div>
  );
}
