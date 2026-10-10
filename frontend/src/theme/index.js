import { createTheme, alpha } from '@mui/material/styles'

const colors = {
  sea: '#0B5F6B',
  seaLight: '#1A7A88',
  seaDark: '#084852',
  sand: '#C4A574',
  sandLight: '#D4BC94',
  sandDark: '#A8895A',
  paper: '#FFFCF8',
  canvas: '#F7F4EF',
  ink: '#1A2426',
  inkMuted: '#5C6B6E',
  border: '#E5DFD4',
  success: '#2E7D57',
  warning: '#C47F17',
  error: '#B23A3A',
}

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: colors.sea,
      light: colors.seaLight,
      dark: colors.seaDark,
      contrastText: '#ffffff',
    },
    secondary: {
      main: colors.sand,
      light: colors.sandLight,
      dark: colors.sandDark,
      contrastText: colors.ink,
    },
    background: {
      default: colors.canvas,
      paper: colors.paper,
    },
    text: {
      primary: colors.ink,
      secondary: colors.inkMuted,
    },
    divider: colors.border,
    success: { main: colors.success },
    warning: { main: colors.warning },
    error: { main: colors.error },
  },
  typography: {
    fontFamily: '"Source Sans 3", "Helvetica Neue", sans-serif',
    h1: {
      fontFamily: '"Fraunces", Georgia, serif',
      fontWeight: 600,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontFamily: '"Fraunces", Georgia, serif',
      fontWeight: 600,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontFamily: '"Fraunces", Georgia, serif',
      fontWeight: 600,
    },
    h4: {
      fontFamily: '"Fraunces", Georgia, serif',
      fontWeight: 600,
    },
    h5: {
      fontFamily: '"Fraunces", Georgia, serif',
      fontWeight: 600,
    },
    h6: {
      fontFamily: '"Source Sans 3", sans-serif',
      fontWeight: 600,
    },
    button: {
      fontFamily: '"Source Sans 3", sans-serif',
      fontWeight: 600,
      letterSpacing: '0.01em',
    },
  },
  shape: {
    borderRadius: 10,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        ':root': {
          '--nephele-sea': colors.sea,
          '--nephele-sea-dark': colors.seaDark,
          '--nephele-sand': colors.sand,
          '--nephele-canvas': colors.canvas,
          '--nephele-paper': colors.paper,
          '--nephele-ink': colors.ink,
          '--nephele-border': colors.border,
        },
        body: {
          backgroundColor: colors.canvas,
          color: colors.ink,
        },
        '::selection': {
          backgroundColor: alpha(colors.sea, 0.2),
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 999,
          paddingInline: 20,
          boxShadow: 'none',
          '&:focus-visible': {
            outline: `2px solid ${colors.sea}`,
            outlineOffset: 2,
          },
        },
        containedPrimary: {
          '&:hover': {
            boxShadow: `0 6px 18px ${alpha(colors.sea, 0.28)}`,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: `1px solid ${colors.border}`,
          boxShadow: `0 1px 2px ${alpha(colors.ink, 0.04)}`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        outlined: {
          borderColor: colors.border,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: `1px solid ${colors.border}`,
          backgroundColor: colors.paper,
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          marginInline: 8,
          '&.Mui-selected': {
            backgroundColor: alpha(colors.sea, 0.1),
            color: colors.seaDark,
            '& .MuiListItemIcon-root': {
              color: colors.sea,
            },
          },
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: 'outlined',
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: colors.paper,
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: colors.seaLight,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: colors.sea,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
  },
})

export { colors }
export default theme
