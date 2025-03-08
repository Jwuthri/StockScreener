import { createTheme } from '@mui/material/styles';

// Robinhood-inspired color palette
const palette = {
  primary: {
    main: '#00C805', // Robinhood green
    light: '#33D331',
    dark: '#00A804',
    contrastText: '#FFFFFF',
  },
  secondary: {
    main: '#5AC53B', // Lighter green for secondary elements
    light: '#7ED962',
    dark: '#489D31',
    contrastText: '#FFFFFF',
  },
  success: {
    main: '#00C805', // Green (same as primary)
    light: '#33D331',
    dark: '#00A804',
  },
  error: {
    main: '#FF5000', // Robinhood red/orange
    light: '#FF7334',
    dark: '#D44500',
  },
  warning: {
    main: '#FFBF00', // Amber
    light: '#FFCF33',
    dark: '#D69F00',
  },
  info: {
    main: '#1F1F1F', // Dark for info
    light: '#4B4B4B',
    dark: '#171717',
  },
  grey: {
    50: '#F7F7F7',
    100: '#F0F0F0',
    200: '#E4E4E4',
    300: '#D1D1D1',
    400: '#A8A8A8',
    500: '#757575',
    600: '#545454',
    700: '#333333',
    800: '#1F1F1F',
    900: '#121212',
  },
  background: {
    default: '#FFFFFF', // Pure white background
    paper: '#FFFFFF',
    card: '#FFFFFF',
    dark: '#1E2023', // Dark background for dark mode
  },
  text: {
    primary: '#000000', // Pure black text
    secondary: '#6F7885',
    disabled: '#A0AEC0',
    darkPrimary: '#FFFFFF', // Dark mode text
    darkSecondary: '#B4B4B4', // Dark mode secondary text
  },
  divider: 'rgba(0, 0, 0, 0.05)',
};

// Typography settings
const typography = {
  fontFamily: "'Inter', -apple-system, sans-serif",
  h1: {
    fontWeight: 600,
    fontSize: '2.5rem',
    lineHeight: 1.2,
    letterSpacing: '-0.03em',
  },
  h2: {
    fontWeight: 600,
    fontSize: '2rem',
    lineHeight: 1.2,
    letterSpacing: '-0.02em',
  },
  h3: {
    fontWeight: 600,
    fontSize: '1.75rem',
    lineHeight: 1.2,
    letterSpacing: '-0.02em',
  },
  h4: {
    fontWeight: 600,
    fontSize: '1.5rem',
    lineHeight: 1.2,
    letterSpacing: '-0.01em',
  },
  h5: {
    fontWeight: 600,
    fontSize: '1.25rem',
    lineHeight: 1.2,
    letterSpacing: '-0.01em',
  },
  h6: {
    fontWeight: 600,
    fontSize: '1rem',
    lineHeight: 1.2,
    letterSpacing: '0em',
  },
  subtitle1: {
    fontSize: '1rem',
    lineHeight: 1.5,
    letterSpacing: '0em',
    fontWeight: 500,
  },
  subtitle2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
    letterSpacing: '0em',
    fontWeight: 500,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
    letterSpacing: '0em',
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
    letterSpacing: '0em',
  },
  button: {
    fontSize: '0.875rem',
    lineHeight: 1.75,
    letterSpacing: '0em',
    textTransform: 'none',
    fontWeight: 600,
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
    letterSpacing: '0em',
  },
  overline: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    fontWeight: 600,
  },
};

// Component overrides
const components = {
  MuiCssBaseline: {
    styleOverrides: {
      '@global': {
        html: {
          WebkitFontSmoothing: 'auto',
        },
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 30, // More rounded buttons like Robinhood
        padding: '10px 24px',
        boxShadow: 'none',
        transition: 'all 0.2s ease-in-out',
        textTransform: 'none',
        fontWeight: 500,
      },
      containedPrimary: {
        backgroundColor: palette.primary.main,
        '&:hover': {
          backgroundColor: palette.primary.dark,
          boxShadow: 'none',
        },
      },
      containedSecondary: {
        backgroundColor: palette.secondary.main,
        '&:hover': {
          backgroundColor: palette.secondary.dark,
          boxShadow: 'none',
        },
      },
      outlined: {
        borderWidth: 1,
        '&:hover': {
          borderWidth: 1,
          boxShadow: 'none',
        },
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        boxShadow: '0 1px 5px rgba(0, 0, 0, 0.05)',
      },
      elevation1: {
        boxShadow: '0 1px 5px rgba(0, 0, 0, 0.05)',
      },
      elevation2: {
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)',
      },
      elevation3: {
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        overflow: 'hidden',
        transition: 'transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out',
        boxShadow: '0 1px 5px rgba(0, 0, 0, 0.05)',
      },
    },
  },
  MuiCardHeader: {
    styleOverrides: {
      root: {
        padding: '16px 20px 8px',
      },
      title: {
        fontSize: '1.15rem',
        fontWeight: 600,
      },
    },
  },
  MuiCardContent: {
    styleOverrides: {
      root: {
        padding: '8px 20px 20px',
        '&:last-child': {
          paddingBottom: 20,
        },
      },
    },
  },
  MuiTableHead: {
    styleOverrides: {
      root: {
        backgroundColor: palette.grey[50],
      },
    },
  },
  MuiTableCell: {
    styleOverrides: {
      root: {
        borderBottom: `1px solid ${palette.grey[100]}`,
        padding: '16px 20px',
      },
      head: {
        fontWeight: 600,
        color: palette.text.secondary,
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 6,
        fontWeight: 500,
        '&.MuiChip-colorPrimary': {
          backgroundColor: `${palette.primary.main}15`,
          color: palette.primary.main,
        },
        '&.MuiChip-colorSecondary': {
          backgroundColor: `${palette.secondary.main}15`,
          color: palette.secondary.main,
        },
        '&.MuiChip-colorSuccess': {
          backgroundColor: `${palette.success.main}15`,
          color: palette.success.main,
        },
        '&.MuiChip-colorError': {
          backgroundColor: `${palette.error.main}15`,
          color: palette.error.main,
        },
        '&.MuiChip-colorWarning': {
          backgroundColor: `${palette.warning.main}15`,
          color: palette.warning.main,
        },
        '&.MuiChip-colorInfo': {
          backgroundColor: `${palette.info.main}15`,
          color: palette.info.main,
        },
      },
    },
  },
  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 500,
        minWidth: 'auto',
        padding: '12px 24px',
      },
    },
  },
  MuiTabs: {
    styleOverrides: {
      indicator: {
        height: 2,
      },
    },
  },
  MuiAlert: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        padding: '12px 16px',
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: palette.grey[800],
        padding: '8px 12px',
        fontSize: '0.75rem',
        borderRadius: 6,
      },
    },
  },
  MuiBackdrop: {
    styleOverrides: {
      root: {
        backgroundColor: 'rgba(0, 0, 0, 0.2)',
      },
    },
  },
};

// Create and export theme
const theme = createTheme({
  palette,
  typography,
  components,
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0 1px 3px rgba(0, 0, 0, 0.05)',
    '0 2px 6px rgba(0, 0, 0, 0.05)',
    '0 4px 10px rgba(0, 0, 0, 0.05)',
    '0 6px 15px rgba(0, 0, 0, 0.05)',
    // ... other shadow levels can be defined similarly
  ],
});

export default theme;
