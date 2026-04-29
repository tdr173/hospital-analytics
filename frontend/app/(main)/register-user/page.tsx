"use client";

import { useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";
import * as yup from "yup";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import PersonAddOutlinedIcon from "@mui/icons-material/PersonAddOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { RegisterPageStyles } from "./styles";
import { registerUser, UserRole } from "@/store/slices/auth/thunks";
import type { RootState } from "@/store";

const ROLES: UserRole[] = ["MANAGER", "DOCTOR", "PATIENT"];

type FieldKey = "firstName" | "lastName" | "email" | "phone" | "jobTitle" | "role";

interface Variant {
  title: string;
  subtitle: string;
  submitLabel: string;
  showRoleSelector: boolean;
  showJobTitle: boolean;
  fixedRole: UserRole | null;
}

const MANAGER_VARIANT: Variant = {
  title: "Register New User",
  subtitle: "Fill in the details below to create a new account.",
  submitLabel: "Register User",
  showRoleSelector: true,
  showJobTitle: true,
  fixedRole: null,
};

const DOCTOR_VARIANT: Variant = {
  title: "Register Patient",
  subtitle: "Add a new patient to your panel.",
  submitLabel: "Register Patient",
  showRoleSelector: false,
  showJobTitle: false,
  fixedRole: "PATIENT",
};

const PATIENT_VARIANT: Variant = {
  title: "Invite Family Member",
  subtitle: "Invite a loved one to join your care network.",
  submitLabel: "Send Invite",
  showRoleSelector: false,
  showJobTitle: false,
  fixedRole: "PATIENT",
};

function resolveVariant(role?: UserRole): Variant {
  if (role === "DOCTOR") return DOCTOR_VARIANT;
  if (role === "PATIENT") return PATIENT_VARIANT;
  return MANAGER_VARIANT;
}

const BUTTON_SX = {
  width: "100%",
  padding: "12px",
  fontSize: "0.875rem",
  backgroundColor: "#0891B2",
  color: "#ffffff",
  border: "none",
  "&:hover": { backgroundColor: "#0e7490" },
};

export default function RegisterPage() {
  const classes = useClasses(RegisterPageStyles, { name: "RegisterPage" });
  const currentRole = useSelector((s: RootState) => s.auth.user?.role);
  const variant = useMemo(() => resolveVariant(currentRole), [currentRole]);

  const initial = useMemo(
    () => ({
      firstName: "",
      lastName: "",
      email: "",
      phone: "",
      jobTitle: "",
      role: (variant.fixedRole ?? "DOCTOR") as UserRole,
    }),
    [variant.fixedRole],
  );

  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState<Partial<Record<FieldKey, string>>>({});
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  useEffect(() => {
    setValues(initial);
    setErrors({});
    setSubmittedEmail(null);
  }, [initial]);

  const schema = useMemo(() => {
    const base: any = {
      firstName: yup.string().required("This field is required."),
      lastName: yup.string().required("This field is required."),
      email: yup
        .string()
        .required("This field is required.")
        .email("Please introduce a valid email."),
      phone: yup
        .string()
        .required("This field is required.")
        .matches(
          /^\+?[0-9\s\-().]{7,20}$/,
          "Please introduce a valid phone number.",
        ),
      role: yup.string().oneOf(ROLES).required("This field is required."),
    };
    if (variant.showJobTitle) {
      base.jobTitle = yup.string().required("This field is required.");
    }
    return yup.object(base);
  }, [variant]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    try {
      await schema.validate(values, { abortEarly: false });
    } catch (err) {
      if (err instanceof yup.ValidationError) {
        const fieldErrors: Partial<Record<FieldKey, string>> = {};
        err.inner.forEach((ie) => {
          if (ie.path && !fieldErrors[ie.path as FieldKey]) {
            fieldErrors[ie.path as FieldKey] = ie.message;
          }
        });
        setErrors(fieldErrors);
      }
      return;
    }

    await registerUser(values);
    setSubmittedEmail(values.email);
  };

  const handleReset = () => {
    setValues(initial);
    setErrors({});
    setSubmittedEmail(null);
  };

  return (
    <div className={classes.pageWrapper}>
      <div className={classes.card}>
        <div className={classes.leftPanel}>
          <div className={classes.iconBox}>
            <PersonAddOutlinedIcon
              sx={{ color: "#0891B2", fontSize: "28px" }}
            />
          </div>
          <h1 className={classes.title}>{variant.title}</h1>
          <p className={classes.subtitle}>{variant.subtitle}</p>
        </div>

        <div className={classes.rightPanel}>
          {submittedEmail ? (
            <div className={classes.successContainer}>
              <div className={classes.successIconBox}>
                <CheckCircleOutlineIcon
                  sx={{ color: "#10b981", fontSize: "32px" }}
                />
              </div>
              <div>
                <p className={classes.successText}>
                  {currentRole === "PATIENT"
                    ? "An invite has been sent to"
                    : "An email with a temporary password has been sent to"}
                </p>
                <p className={classes.successEmail}>{submittedEmail}</p>
              </div>
              <StyledButton
                variant="secondary"
                onClick={handleReset}
                sx={BUTTON_SX}
              >
                {variant.submitLabel}
              </StyledButton>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate className={classes.form}>
              <StyledInput
                label="First Name"
                type="text"
                required
                placeholder="John"
                value={values.firstName}
                onChange={(e) =>
                  setValues({ ...values, firstName: e.target.value })
                }
                error={!!errors.firstName}
                helperText={errors.firstName}
              />
              <StyledInput
                label="Last Name"
                type="text"
                required
                placeholder="Doe"
                value={values.lastName}
                onChange={(e) =>
                  setValues({ ...values, lastName: e.target.value })
                }
                error={!!errors.lastName}
                helperText={errors.lastName}
              />
              <StyledInput
                label="Email Address"
                type="email"
                required
                placeholder="doctor@hospital.org"
                value={values.email}
                onChange={(e) =>
                  setValues({ ...values, email: e.target.value })
                }
                error={!!errors.email}
                helperText={errors.email}
              />
              <StyledInput
                label="Phone Number"
                type="text"
                required
                placeholder="+40712345678"
                value={values.phone}
                onChange={(e) =>
                  setValues({ ...values, phone: e.target.value })
                }
                error={!!errors.phone}
                helperText={errors.phone}
              />
              {variant.showJobTitle && (
                <StyledInput
                  label="Job Title"
                  type="text"
                  required
                  placeholder="e.g. Cardiologist"
                  value={values.jobTitle}
                  onChange={(e) =>
                    setValues({ ...values, jobTitle: e.target.value })
                  }
                  error={!!errors.jobTitle}
                  helperText={errors.jobTitle}
                />
              )}

              {variant.showRoleSelector && (
                <div className={classes.fullRow}>
                  <p className={classes.roleLabel}>Role</p>
                  <div className={classes.roleOptions}>
                    {ROLES.map((r) => (
                      <label
                        key={r}
                        className={`${classes.roleOption} ${
                          values.role === r ? classes.roleOptionSelected : ""
                        }`}
                      >
                        <input
                          type="radio"
                          name="role"
                          value={r}
                          checked={values.role === r}
                          onChange={() => setValues({ ...values, role: r })}
                          className={classes.roleHiddenInput}
                        />
                        <span className={classes.roleOptionLabel}>{r}</span>
                      </label>
                    ))}
                  </div>
                  {errors.role && (
                    <p className={classes.roleError}>{errors.role}</p>
                  )}
                </div>
              )}

              <div className={classes.fullRow}>
                <StyledButton variant="secondary" type="submit" sx={BUTTON_SX}>
                  {variant.submitLabel}
                </StyledButton>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
