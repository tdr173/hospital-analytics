"use client";

import { useEffect, useState } from "react";
import * as yup from "yup";
import StyledInput from "@/components/generic_components/StyledInput/StyledInput";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import PersonAddOutlinedIcon from "@mui/icons-material/PersonAddOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { RegisterPageStyles } from "./styles";
import { registerUser, UserRole } from "@/store/slices/auth/thunks";

const ROLES: UserRole[] = ["MANAGER", "DOCTOR", "PATIENT"];

const registerSchema = yup.object({
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
  jobTitle: yup.string().required("This field is required."),
  role: yup.string().oneOf(ROLES).required("This field is required."),
});

const INITIAL = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  jobTitle: "",
  role: "DOCTOR" as UserRole,
};

const BUTTON_SX = {
  width: "100%",
  padding: "12px",
  fontSize: "0.875rem",
  backgroundColor: "#0891B2",
  color: "#ffffff",
  border: "none",
  "&:hover": { backgroundColor: "#0e7490" },
};

type FieldKey = keyof typeof INITIAL;

export default function RegisterPage() {
  const classes = useClasses(RegisterPageStyles, { name: "RegisterPage" });
  const [values, setValues] = useState(INITIAL);
  const [errors, setErrors] = useState<Partial<Record<FieldKey, string>>>({});
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      setValues(INITIAL);
      setErrors({});
      setSubmittedEmail(null);
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    try {
      await registerSchema.validate(values, { abortEarly: false });
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
    setValues(INITIAL);
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
          <h1 className={classes.title}>Register New User</h1>
          <p className={classes.subtitle}>
            Fill in the details below to create a new account.
          </p>
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
                  An email with a temporary password has been sent to
                </p>
                <p className={classes.successEmail}>{submittedEmail}</p>
              </div>
              <StyledButton
                variant="secondary"
                onClick={handleReset}
                sx={BUTTON_SX}
              >
                Add User
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
                placeholder="clinician@hospital.org"
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

              <div className={classes.fullRow}>
                <StyledButton variant="secondary" type="submit" sx={BUTTON_SX}>
                  Register User
                </StyledButton>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
