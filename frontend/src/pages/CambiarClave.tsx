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
import api from '../api/axios';
import { toast } from 'react-toastify';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

// Definimos la estructura de los datos del formulario
interface FormularioCambioClave {
  claveActual: string;
  claveNueva: string;
  confirmacionClaveNueva: string;
}

const CambiarClave = () => {
  const { register, handleSubmit, watch, formState: { errors } } = useForm<FormularioCambioClave>();
  const [cargando, setCargando] = useState(false);
  const [errorApi, setErrorApi] = useState<string | null>(null);

  // Estados para visibilidad de contraseñas
  const [mostrarClaveActual, setMostrarClaveActual] = useState(false);
  const [mostrarClaveNueva, setMostrarClaveNueva] = useState(false);
  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false);

  const navegar = useNavigate();

  // Funciones para alternar visibilidad
  const toggleVisibility = (setter: React.Dispatch<React.SetStateAction<boolean>>) => () => setter((show) => !show);
  const preventDefault = (event: React.MouseEvent<HTMLButtonElement>) => event.preventDefault();

  // Validación personalizada: Claves nuevas deben coincidir
  const claveNueva = watch('claveNueva');

  const onSubmit = async (datos: FormularioCambioClave) => {
    setCargando(true);
    setErrorApi(null);

    try {
      // Mapeamos a los nombres que espera el backend (snake_case)
      const payload = {
        clave_actual: datos.claveActual,
        clave_nueva: datos.claveNueva,
        confirmacion_clave_nueva: datos.confirmacionClaveNueva
      };

      await api.post('/auth/cambiar-clave', payload);

      toast.success("Contraseña actualizada correctamente");
      navegar('/dashboard');

    } catch (error: any) {
      console.error("Error al cambiar clave:", error);
      if (error.response?.data?.detail) {
        setErrorApi(error.response.data.detail);
      } else {
        setErrorApi("Ocurrió un error al intentar cambiar la contraseña.");
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper
        elevation={3}
        sx={{
          p: 4,
          mt: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          borderRadius: 2
        }}
      >
        <Typography component="h1" variant="h5" gutterBottom sx={{ color: 'primary.main', fontWeight: 'bold' }}>
          Cambiar Contraseña
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Ingresa tu contraseña actual y define una nueva.
        </Typography>

        {errorApi && (
          <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
            {errorApi}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ width: '100%' }}>

          {/* Clave Actual */}
          <TextField
            margin="normal"
            fullWidth
            label="Contraseña Actual"
            type={mostrarClaveActual ? 'text' : 'password'}
            id="claveActual"
            disabled={cargando}
            error={!!errors.claveActual}
            helperText={errors.claveActual ? "La contraseña actual es requerida" : ""}
            {...register("claveActual", { required: true })}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={toggleVisibility(setMostrarClaveActual)}
                    onMouseDown={preventDefault}
                    edge="end"
                  >
                    {mostrarClaveActual ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* Nueva Clave */}
          <TextField
            margin="normal"
            fullWidth
            label="Nueva Contraseña"
            type={mostrarClaveNueva ? 'text' : 'password'}
            id="claveNueva"
            disabled={cargando}
            error={!!errors.claveNueva}
            helperText={errors.claveNueva ? "La nueva contraseña es requerida" : ""}
            {...register("claveNueva", { required: true, minLength: { value: 6, message: "Mínimo 6 caracteres" } })}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={toggleVisibility(setMostrarClaveNueva)}
                    onMouseDown={preventDefault}
                    edge="end"
                  >
                    {mostrarClaveNueva ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          {/* Confirmación Nueva Clave */}
          <TextField
            margin="normal"
            fullWidth
            label="Confirmar Nueva Contraseña"
            type={mostrarConfirmacion ? 'text' : 'password'}
            id="confirmacionClaveNueva"
            disabled={cargando}
            error={!!errors.confirmacionClaveNueva}
            helperText={errors.confirmacionClaveNueva?.message || ""}
            {...register("confirmacionClaveNueva", {
                required: "Confirma tu nueva contraseña",
                validate: (val) => val === claveNueva || "Las contraseñas no coinciden"
            })}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={toggleVisibility(setMostrarConfirmacion)}
                    onMouseDown={preventDefault}
                    edge="end"
                  >
                    {mostrarConfirmacion ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
                variant="outlined"
                onClick={() => navegar('/dashboard')}
                disabled={cargando}
            >
                Cancelar
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={cargando}
            >
              {cargando ? <CircularProgress size={24} color="inherit" /> : "Actualizar Contraseña"}
            </Button>
          </Box>

        </Box>
      </Paper>
    </Container>
  );
};

export default CambiarClave;