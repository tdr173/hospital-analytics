export interface Theme {
  colors: {
    primary: {
      main: string;
      dark: string;
      light: string;
      lighter: string;
    };
    secondary: {
      main: string;
      dark: string;
      light: string;
    };
    background: {
      default: string;
      paper: string;
      alt: string;
    };
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
    border: {
      light: string;
      main: string;
      dark: string;
    };
    status: {
      success: string;
      warning: string;
      error: string;
      info: string;
    };
    grey: {
      50: string;
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
    };
    surface: {
      base: string;
      containerLow: string;
      containerLowest: string;
      containerHighest: string;
    };
    navigation: {
      bg: string;
      container: string;
      activeIndicator: string;
      activeIndicatorDim: string;
    };
    accent: {
      teal: string;
      tealDark: string;
      gradient: string;
    };
    button: {
      primary: string;
      primaryHover: string;
      primaryActive: string;
      secondary: string;
      secondaryHover: string;
      secondaryActive: string;
    };
    gender: {
      male: string;
      maleBg: string;
      female: string;
      femaleBg: string;
    };
    charts: {
      gender: { male: string; female: string };
      ageGroups: string[];
      encounterClass: Record<string, string>;
      burden: string[];
      categorical: string[];
      defaultPalette: string[];
      outlier: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      light: number;
      regular: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
    fontFamily: string;
    fontFamilyHeading: string;
  };
  borderRadius: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
    ambient: string;
  };
  layout: {
    sidebarWidth: string;
    sidebarColor: string;
    headerColor: string;
    pageColor: string;
  };
}

const theme: Theme = {
  colors: {
    primary: {
      main: "#006780",
      dark: "#004d60",
      light: "#028fb0",
      lighter: "#b7eaff",
    },
    secondary: {
      main: "#515f74",
      dark: "#3a4555",
      light: "#d5e3fc",
    },
    background: {
      default: "#ffffff",
      paper: "#f7f9fb",
      alt: "#f2f4f6",
    },
    text: {
      primary: "#191c1e",
      secondary: "#6b7280",
      disabled: "#9ca3af",
    },
    border: {
      light: "rgba(198, 198, 205, 0.2)",
      main: "rgba(198, 198, 205, 0.35)",
      dark: "#c6c6cd",
    },
    status: {
      success: "#00201d",
      warning: "#F59E0B",
      error: "#EF4444",
      info: "#006780",
    },
    grey: {
      50: "#f7f9fb",
      100: "#f2f4f6",
      200: "#e0e3e5",
      300: "#c6c6cd",
      400: "#9ca3af",
      500: "#6b7280",
      600: "#515f74",
    },
    surface: {
      base: "#f7f9fb",
      containerLow: "#f2f4f6",
      containerLowest: "#ffffff",
      containerHighest: "#e0e3e5",
    },
    navigation: {
      bg: "#515f74",
      container: "#d5e3fc",
      activeIndicator: "#b7eaff",
      activeIndicatorDim: "#6cd3f7",
    },
    accent: {
      teal: "#006780",
      tealDark: "#00201d",
      gradient: "linear-gradient(135deg, #191c1e 0%, #028fb0 100%)",
    },
    button: {
      primary: "#006780",
      primaryHover: "#004d60",
      primaryActive: "#00364a",
      secondary: "#f2f4f6",
      secondaryHover: "#e0e3e5",
      secondaryActive: "#c6c6cd",
    },
    gender: {
      male: "#2563eb",
      maleBg: "#dbeafe",
      female: "#9333ea",
      femaleBg: "#f3e8ff",
    },
    charts: {
      gender: {
        male: "#2563eb",
        female: "#9333ea",
      },
      ageGroups: ["#006780", "#028fb0", "#6cd3f7", "#515f74", "#b7eaff"],
      encounterClass: {
        emergency: "#ef4444",
        ambulatory: "#006780",
        inpatient: "#8b5cf6",
        wellness: "#10b981",
        urgentcare: "#f59e0b",
        other: "#515f74",
      },
      burden: ["#84CC16", "#EAB308", "#DC2626"],
      categorical: [
        "#DC2626",
        "#2563EB",
        "#16A34A",
        "#F97316",
        "#06B6D4",
        "#7C3AED",
        "#92400E",
        "#EAB308",
        "#9CA3AF",
        "#BE185D",
      ],
      defaultPalette: [
        "#006780",
        "#028fb0",
        "#6cd3f7",
        "#515f74",
        "#b7eaff",
        "#3a4555",
        "#d5e3fc",
        "#00201d",
        "#8ba4c4",
        "#c6c6cd",
      ],
      outlier: "#9CA3AF",
    },
  },
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
    xxl: "48px",
  },
  typography: {
    fontSize: {
      xs: "0.75rem",
      sm: "0.875rem",
      md: "1rem",
      lg: "1.125rem",
      xl: "2rem",
    },
    fontWeight: {
      light: 300,
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
    fontFamily:
      '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontFamilyHeading:
      '"Manrope", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  borderRadius: {
    xs: "2px",
    sm: "4px",
    md: "6px",
    lg: "12px",
    full: "9999px",
  },
  shadows: {
    sm: "0px 2px 8px rgba(25, 28, 30, 0.04)",
    md: "0px 4px 16px rgba(25, 28, 30, 0.06)",
    lg: "0px 8px 24px rgba(25, 28, 30, 0.08)",
    xl: "0px 12px 32px rgba(25, 28, 30, 0.06)",
    ambient: "0px 12px 32px rgba(25, 28, 30, 0.06)",
  },
  layout: {
    sidebarWidth: "220px",
    sidebarColor: "#515f74",
    headerColor: "#ffffff",
    pageColor: "#f7f9fb",
  },
};

export default theme;
