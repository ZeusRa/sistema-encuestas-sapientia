import { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, IconButton, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  MenuItem, Tooltip, CircularProgress
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import KeyIcon from '@mui/icons-material/Key';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AddIcon from '@mui/icons-material/Add';
import { useForm } from 'react-hook-form';
import api from '../../api/axios';
import { toast } from 'react-toastify';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

// Interfaces
interface Usuario {
  id_admin: number;
  nombre_usuario: string;
  rol: 'ADMINISTRADOR' | 'DIRECTIVO';
  fecha_creacion: string;
  fecha_ultimo_login: string | null;
  activo: boolean;
  debe_cambiar_clave: boolean;
}

interface FormularioCrearUsuario {
  nombre_usuario: string;
  rol: 'ADMINISTRADOR' | 'DIRECTIVO';
  clave?: string;
}

const GestionUsuarios = () => {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [cargando, setCargando] = useState(true);
  const [modalAbierto, setModalAbierto] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormularioCrearUsuario>();

  const cargarUsuarios = async () => {
    try {
      setCargando(true);
      const res = await api.get('/usuarios/');
      setUsuarios(res.data);
    } catch (error) {
      console.error("Error al cargar usuarios", error);
      toast.error("No se pudieron cargar los usuarios.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarUsuarios();
  }, []);

  const handleCrearUsuario = async (data: FormularioCrearUsuario) => {
    try {
      await api.post('/usuarios/', data);
      toast.success("Usuario creado correctamente.");
      setModalAbierto(false);
      reset();
      cargarUsuarios();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Error al crear usuario.");
    }
  };

  const toggleEstado = async (usuario: Usuario) => {
    try {
      await api.put(`/usuarios/${usuario.id_admin}/estado`, { activo: !usuario.activo });
      toast.success(`Usuario ${!usuario.activo ? 'activado' : 'desactivado'}.`);
      cargarUsuarios();
    } catch (error) {
      toast.error("Error al cambiar estado.");
    }
  };

  const regenerarClave = async (id: number, nombre: string) => {
    if (!confirm(`¿Estás seguro de regenerar la clave para ${nombre}? Se establecerá una clave genérica.`)) return;
    try {
      const res = await api.put(`/usuarios/${id}/regenerar-clave`);
      toast.success(res.data.mensaje);
      cargarUsuarios(); // Para actualizar flag debe_cambiar_clave
    } catch (error) {
      toast.error("Error al regenerar clave.");
    }
  };

  const cambiarRol = async (id: number, rolActual: string) => {
      // Implementación simple toggleando rol para demo, idealmente tendria que preparar un modal
      const nuevoRol = rolActual === 'ADMINISTRADOR' ? 'DIRECTIVO' : 'ADMINISTRADOR';
      if (!confirm(`¿Cambiar rol a ${nuevoRol}?`)) return;

      try {
          await api.put(`/usuarios/${id}/rol`, { rol: nuevoRol });
          toast.success("Rol actualizado");
          cargarUsuarios();
      } catch (error) {
          toast.error("Error al cambiar rol");
      }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" color="primary" fontWeight="bold">
          Gestión de Usuarios
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setModalAbierto(true)}
        >
          Nuevo Usuario
        </Button>
      </Box>

      <TableContainer component={Paper} elevation={2}>
        <Table>
          <TableHead sx={{ bgcolor: 'grey.100' }}>
            <TableRow>
              <TableCell>Usuario</TableCell>
              <TableCell>Rol</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Último Login</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cargando ? (
               <TableRow>
                 <TableCell colSpan={5} align="center"><CircularProgress /></TableCell>
               </TableRow>
            ) : usuarios.map((user) => (
              <TableRow key={user.id_admin}>
                <TableCell>
                    <Typography fontWeight="bold">{user.nombre_usuario}</Typography>
                    <Typography variant="caption" color="text.secondary">Creado: {format(new Date(user.fecha_creacion), 'dd/MM/yyyy', { locale: es })}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.rol}
                    color={user.rol === 'ADMINISTRADOR' ? 'primary' : 'default'}
                    size="small"
                    onClick={() => cambiarRol(user.id_admin, user.rol)}
                    sx={{ cursor: 'pointer' }}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.activo ? "Activo" : "Inactivo"}
                    color={user.activo ? "success" : "error"}
                    variant="outlined"
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {user.fecha_ultimo_login
                    ? format(new Date(user.fecha_ultimo_login), 'dd/MM/yyyy HH:mm', { locale: es })
                    : "Nunca"}
                </TableCell>
                <TableCell>
                  <Tooltip title={user.activo ? "Desactivar" : "Activar"}>
                    <IconButton onClick={() => toggleEstado(user)} color={user.activo ? "error" : "success"}>
                      {user.activo ? <BlockIcon /> : <CheckCircleIcon />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Regenerar Contraseña">
                    <IconButton onClick={() => regenerarClave(user.id_admin, user.nombre_usuario)} color="warning">
                      <KeyIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Modal Crear Usuario */}
      <Dialog open={modalAbierto} onClose={() => setModalAbierto(false)}>
        <DialogTitle>Crear Nuevo Usuario</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <TextField
              fullWidth
              margin="normal"
              label="Nombre de Usuario"
              {...register("nombre_usuario", { required: true })}
              error={!!errors.nombre_usuario}
            />
            <TextField
              select
              fullWidth
              margin="normal"
              label="Rol"
              defaultValue="DIRECTIVO"
              {...register("rol")}
            >
              <MenuItem value="ADMINISTRADOR">Administrador</MenuItem>
              <MenuItem value="DIRECTIVO">Directivo</MenuItem>
            </TextField>
            <TextField
              fullWidth
              margin="normal"
              label="Contraseña (Opcional)"
              placeholder="Dejar en blanco para genérica"
              helperText="Si se deja vacío, se generará una temporal y se pedirá cambio."
              {...register("clave")}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModalAbierto(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleSubmit(handleCrearUsuario)}>Crear</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GestionUsuarios;
