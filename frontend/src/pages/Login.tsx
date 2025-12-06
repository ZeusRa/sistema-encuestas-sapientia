import { useState } from 'react';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton
} from '@mui/material';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { jwtDecode } from 'jwt-decode';
import api from '../api/axios';
import { usarAuthStore } from '../context/authStore';
import { toast } from 'react-toastify';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

// Definimos la estructura de los datos del formulario
interface FormularioLogin {
  usuario: string;
  clave: string;
}

const Login = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<FormularioLogin>();
  const [cargando, setCargando] = useState(false);
  const [errorApi, setErrorApi] = useState<string | null>(null);
  const [mostrarClave, setMostrarClave] = useState(false);

  const navegar = useNavigate();
  const iniciarSesionStore = usarAuthStore(state => state.iniciarSesion);

  // Función para alternar visibilidad
  const handleClickMostrarClave = () => setMostrarClave((show) => !show);
  const handleMouseDownClave = (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault(); // Evita que el botón robe el foco
  };

  // Función que se ejecuta al enviar el formulario
  const onSubmit = async (datos: FormularioLogin) => {
    setCargando(true);
    setErrorApi(null);

    // El backend espera x-www-form-urlencoded para OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append('username', datos.usuario); // OJO: FastAPI espera 'username'
    formData.append('password', datos.clave);   // OJO: FastAPI espera 'password'

    try {
      const respuesta = await api.post('/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token } = respuesta.data;

      // Guardar en el store global (Zustand)
      iniciarSesionStore(access_token);

      toast.success(`¡Bienvenido de nuevo!`);

      // Verificar si debe cambiar clave
      const decoded: any = jwtDecode(access_token);
      if (decoded.debe_cambiar_clave) {
        toast.warning("Debes actualizar tu contraseña por seguridad.");
        navegar('/cambiar-clave');
      } else {
        navegar('/dashboard');
      }

    } catch (error: any) {
      console.error("Error de login:", error);
      if (error.response?.status === 401) {
        // Puede ser credenciales incorrectas o usuario inactivo
        const mensaje = error.response?.data?.detail || "Credenciales incorrectas o usuario inactivo.";
        setErrorApi(mensaje);
      } else if (error.response?.status === 500) {
        setErrorApi("Error interno del servidor (500). Contacte al administrador (Posible error de BD).");
      } else {
        setErrorApi("Error de conexión con el servidor. Intenta más tarde.");
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'background.default' // Frostline Pale
      }}
    >
      <Container maxWidth="xs">
        <Paper
          elevation={6}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            borderRadius: 3,
            borderTop: 6, // Borde superior grueso
            borderColor: 'primary.main' // Continental Blue
          }}
        >
          {/* Encabezado */}
          <Typography component="h1" variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            SISTEMA DE ENCUESTAS
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Acceso Administrativo
          </Typography>

          {/* Mensaje de Error de API */}
          {errorApi && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {errorApi}
            </Alert>
          )}

          {/* Formulario */}
          <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 1, width: '100%' }}>

            <TextField
              margin="normal"
              fullWidth
              id="usuario"
              label="Usuario"
              autoComplete="username"
              autoFocus
              disabled={cargando}
              error={!!errors.usuario}
              helperText={errors.usuario ? "El usuario es requerido" : ""}
              {...register("usuario", { required: true })}
            />

            <TextField
              margin="normal"
              fullWidth
              label="Contraseña"
              type={mostrarClave ? 'text' : 'password'}
              id="clave"
              autoComplete="current-password"
              disabled={cargando}
              error={!!errors.clave}
              helperText={errors.clave ? "La contraseña es requerida" : ""}
              {...register("clave", { required: true })}
              // AÑADIDO: Icono de visibilidad
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="alternar visibilidad de contraseña"
                      onClick={handleClickMostrarClave}
                      onMouseDown={handleMouseDownClave}
                      edge="end"
                    >
                      {mostrarClave ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={cargando}
              sx={{ mt: 3, mb: 2, py: 1.5, fontSize: '1rem' }}
            >
              {cargando ? <CircularProgress size={24} color="inherit" /> : "Ingresar"}
            </Button>

          </Box>
        </Paper>

        <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 4 }}>
          © 2025 Sistema de Encuestas UCA
        </Typography>
      </Container>
    </Box>
  );
};

export default Login;