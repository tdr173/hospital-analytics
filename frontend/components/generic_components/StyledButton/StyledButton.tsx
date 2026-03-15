"use client";

import Button, { ButtonProps } from "@mui/material/Button";

interface StyledButtonProps extends ButtonProps {
  variant?: "primary" | "secondary" | "ghost";
}

export default function StyledButton({
  variant = "primary",
  children,
  sx,
  ...props
}: StyledButtonProps) {
  const variantStyles = {
    primary: {
      backgroundColor: "white",
      color: "black",
      border: "2px solid black",
      boxShadow: "3px 3px 0px 0px black",
      "&:hover": {
        backgroundColor: "white",
        boxShadow: "1px 1px 0px 0px black",
        transform: "translate(2px, 2px)",
      },
      "&:active": {
        backgroundColor: "white",
        boxShadow: "none",
        transform: "translate(3px, 3px)",
      },
    },
    secondary: {
      backgroundColor: "transparent",
      color: "black",
      border: "2px solid black",
      boxShadow: "none",
      "&:hover": {
        backgroundColor: "rgba(0,0,0,0.05)",
      },
    },
    ghost: {
      backgroundColor: "transparent",
      color: "black",
      border: "2px solid transparent",
      boxShadow: "none",
      "&:hover": {
        backgroundColor: "transparent",
        border: "2px solid black",
      },
    },
  };

  return (
    <Button
      disableRipple
      disableElevation
      {...props}
      sx={{
        fontFamily: '"Balsamiq Sans", cursive',
        fontWeight: 700,
        fontSize: "14px",
        textTransform: "none",
        borderRadius: "10px",
        padding: "8px 18px",
        transition: "box-shadow 0.1s, transform 0.1s",
        minWidth: "unset",
        ...variantStyles[variant],
        ...sx,
      }}
    >
      {children}
    </Button>
  );
}
