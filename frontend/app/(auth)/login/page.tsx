"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import Link from "next/link";
import * as yup from "yup";
import useClasses from "@/utils/useClasses";
import { LoginPageStyles } from "./styles";

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
  const classes = useClasses(LoginPageStyles, { name: "LoginPage" });

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
    <div className={classes.card}>
      <div className={classes.iconRow}>
        <div className={classes.iconBox}>
          <LockOutlinedIcon sx={{ color: "#0891B2", fontSize: "28px" }} />
        </div>
      </div>

      <h1 className={classes.title}>
        Welcome back
      </h1>
      <p className={classes.subtitle}>
        Sign in to your HospitAI account
      </p>

      <form
        onSubmit={handleLogin}
        noValidate
        className={classes.form}
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

        <div className={classes.forgotRow}>
          <Link href="/forgot-password" className={classes.forgotLink}>
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

      <p className={classes.footer}></p>
    </div>
  );
}
