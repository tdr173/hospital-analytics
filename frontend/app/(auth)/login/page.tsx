"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDispatch } from "react-redux";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import Link from "next/link";
import * as yup from "yup";
import useClasses from "@/utils/useClasses";
import { LoginPageStyles } from "./styles";
import { AppDispatch } from "@/store";
import { login } from "@/store/slices/auth/auth-slice";
import { loginUser, type UserRole } from "@/store/slices/auth/thunks";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

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
  const dispatch = useAppDispatch();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {},
  );
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const classes = useClasses(LoginPageStyles, { name: "LoginPage" });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSubmitError("");

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

    setSubmitting(true);
    const result = await loginUser(email.trim().toLowerCase(), password);
    setSubmitting(false);

    if (!result.ok) {
      setSubmitError(result.error.message);
      return;
    }

    const { data } = result;
    dispatch(
      login({
        email: data.email,
        role: data.role as UserRole,
        patientId: data.patientId ?? undefined,
        providerId: data.providerId ?? undefined,
        accessToken: data.accessToken,
        mustChangePassword: data.mustChangePassword,
      }),
    );

    if (data.mustChangePassword) {
      router.push("/forgot-password");
      return;
    }
    router.push("/home");
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
        {submitError ? (
          <div
            role="alert"
            style={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "0.85rem",
              color: "#b91c1c",
              backgroundColor: "#fef2f2",
              border: "1px solid #fee2e2",
              padding: "10px 12px",
              borderRadius: "8px",
            }}
          >
            {submitError}
          </div>
        ) : null}

        <StyledInput
          label="Email Address"
          type="email"
          required
          placeholder="doctor@hospitai.com"
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
          {submitting ? "Signing in…" : "Sign in"}
        </StyledButton>
      </form>

      <p className={classes.footer}></p>
    </div>
  );
}
