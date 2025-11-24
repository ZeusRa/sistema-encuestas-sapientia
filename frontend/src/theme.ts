import { createTheme } from '@mui/material/styles';

// Paleta personalizada
const colors = {
  continentalBlue: '#023E8A',
  coastalSurge: '#48CAE4',
  frostlinePale: '#CAF0F8',
  trenchBlue: '#03045E',
  white: '#FFFFFF',
};

const theme = createTheme({
  palette: {
    primary: {
      main: colors.continentalBlue,
      light: colors.coastalSurge,
      dark: colors.trenchBlue,
      contrastText: colors.white,
    },
    secondary: {
      main: colors.coastalSurge,
      contrastText: colors.trenchBlue,
    },
    background: {
      default: colors.frostlinePale,
      paper: colors.white,
    },
    text: {
      primary: colors.trenchBlue,
      secondary: colors.continentalBlue,
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      color: colors.trenchBlue,
    },
    h4: {
        fontWeight: 600,
        color: colors.continentalBlue
    }
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8, // Bordes ligeramente redondeados
          textTransform: 'none', // Evitar mayúsculas forzadas
          fontWeight: 600,
        },
      },
    },
    MuiTextField: {
        styleOverrides: {
            root: {
                backgroundColor: colors.white,
                borderRadius: 4
            }
        }
    }
  },
});

export default theme;