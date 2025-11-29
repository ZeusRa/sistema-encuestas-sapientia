
import { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Button, Grid, FormControl, InputLabel, Select, MenuItem, Switch, Card, CardContent,
  CircularProgress, Alert
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import api from '../../api/axios';
import { toast } from 'react-toastify';

interface Permiso {
  id_permiso: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  categoria: string;
}

interface Usuario {
  id_admin: number;
  nombre_usuario: string;
  rol: string;
}

interface AsignacionUsuario {
  id_permiso: number;
  tiene: boolean;
}

const GestionPermisos = () => {
  const [tab, setTab] = useState<'roles' | 'usuarios'>('roles');
  const [permisos, setPermisos] = useState<Permiso[]>([]);
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [rolSeleccionado, setRolSeleccionado] = useState<string>('ADMINISTRADOR');
  const [permisosRol, setPermisosRol] = useState<string[]>([]); // Lista de códigos
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState<number | null>(null);
  const [permisosUsuarioExplicitos, setPermisosUsuarioExplicitos] = useState<AsignacionUsuario[]>([]);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    cargarPermisos();
    cargarUsuarios();
  }, []);

  useEffect(() => {
    if (tab === 'roles') {
      cargarPermisosRol(rolSeleccionado);
    }
  }, [rolSeleccionado, tab]);

  useEffect(() => {
    if (tab === 'usuarios' && usuarioSeleccionado) {
      cargarPermisosUsuario(usuarioSeleccionado);
    }
  }, [usuarioSeleccionado, tab]);

  const cargarPermisos = async () => {
    try {
      const res = await api.get('/permisos/');
      setPermisos(res.data);
    } catch (error) {
      console.error("Error cargando permisos", error);
    }
  };

  const cargarUsuarios = async () => {
    try {
      const res = await api.get('/usuarios/');
      setUsuarios(res.data);
    } catch (error) {
        // Puede fallar si no es admin, pero esta página es solo para admins
      console.error("Error cargando usuarios", error);
    }
  };

  const cargarPermisosRol = async (rol: string) => {
    setCargando(true);
    try {
      const res = await api.get(`/permisos/roles/${rol}`);
      setPermisosRol(res.data); // Devuelve lista de códigos
    } catch (error) {
      toast.error("Error cargando permisos del rol");
    } finally {
      setCargando(false);
    }
  };

  const cargarPermisosUsuario = async (id: number) => {
    setCargando(true);
    try {
      const res = await api.get(`/permisos/usuarios/${id}`);
      setPermisosUsuarioExplicitos(res.data);
    } catch (error) {
      toast.error("Error cargando excepciones de usuario");
    } finally {
      setCargando(false);
    }
  };

  // --- LOGICA ROLES ---
  const togglePermisoRol = async (id_permiso: number, codigo: string, activoActual: boolean) => {
    const nuevosCodigos = activoActual
        ? permisosRol.filter(c => c !== codigo)
        : [...permisosRol, codigo];

    // Mapear codigos a IDs para el backend
    const ids = permisos
        .filter(p => nuevosCodigos.includes(p.codigo))
        .map(p => p.id_permiso);

    try {
        await api.put(`/permisos/roles/${rolSeleccionado}`, { id_permisos: ids });
        setPermisosRol(nuevosCodigos);
        toast.success("Permisos de rol actualizados");
    } catch (error) {
        toast.error("Error actualizando permisos");
    }
  };

  // --- LOGICA USUARIOS ---
  const getEstadoPermisoUsuario = (id_permiso: number) => {
      const expl = permisosUsuarioExplicitos.find(p => p.id_permiso === id_permiso);
      if (expl) return expl.tiene ? 'otorgado' : 'denegado';
      return 'heredado';
  };

  const handlePermisoUsuario = async (id_permiso: number, accion: 'otorgar' | 'denegar' | 'reset') => {
      if (!usuarioSeleccionado) return;

      try {
          if (accion === 'reset') {
              await api.delete(`/permisos/usuarios/${usuarioSeleccionado}/${id_permiso}`);
          } else {
              await api.put(`/permisos/usuarios/${usuarioSeleccionado}`, {
                  id_permiso,
                  tiene: accion === 'otorgar'
              });
          }
          cargarPermisosUsuario(usuarioSeleccionado);
          toast.success("Permiso de usuario actualizado");
      } catch (error) {
          toast.error("Error actualizando excepción");
      }
  };

  // Agrupar permisos por categoría para visualización
  const categorias = Array.from(new Set(permisos.map(p => p.categoria)));

  return (
    <Box>
        <Typography variant="h4" gutterBottom color="primary" fontWeight="bold">
            Matriz de Permisos
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Button
                onClick={() => setTab('roles')}
                sx={{ mr: 2, borderBottom: tab === 'roles' ? 2 : 0, borderRadius: 0 }}
            >
                Por Roles
            </Button>
            <Button
                onClick={() => setTab('usuarios')}
                sx={{ borderBottom: tab === 'usuarios' ? 2 : 0, borderRadius: 0 }}
            >
                Por Usuarios (Excepciones)
            </Button>
        </Box>

        {tab === 'roles' && (
            <Box>
                <FormControl sx={{ minWidth: 200, mb: 3 }}>
                    <InputLabel>Rol</InputLabel>
                    <Select value={rolSeleccionado} label="Rol" onChange={(e) => setRolSeleccionado(e.target.value)}>
                        <MenuItem value="ADMINISTRADOR">Administrador</MenuItem>
                        <MenuItem value="DIRECTIVO">Directivo</MenuItem>
                    </Select>
                </FormControl>

                {cargando ? <CircularProgress /> : (
                    <Grid container spacing={3}>
                        {categorias.map(cat => (
                            <Grid item xs={12} md={6} key={cat}>
                                <Card variant="outlined">
                                    <CardContent>
                                        <Typography variant="h6" sx={{ textTransform: 'capitalize', mb: 2 }}>
                                            {cat}
                                        </Typography>
                                        <Table size="small">
                                            <TableBody>
                                                {permisos.filter(p => p.categoria === cat).map(permiso => {
                                                    const activo = permisosRol.includes(permiso.codigo);
                                                    return (
                                                        <TableRow key={permiso.id_permiso}>
                                                            <TableCell>
                                                                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                                                                    <Typography variant="subtitle2">{permiso.nombre}</Typography>
                                                                    <Typography variant="caption" color="text.secondary">{permiso.descripcion}</Typography>
                                                                </Box>
                                                            </TableCell>
                                                            <TableCell align="right">
                                                                <Switch
                                                                    checked={activo}
                                                                    onChange={() => togglePermisoRol(permiso.id_permiso, permiso.codigo, activo)}
                                                                />
                                                            </TableCell>
                                                        </TableRow>
                                                    );
                                                })}
                                            </TableBody>
                                        </Table>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                )}
            </Box>
        )}

        {tab === 'usuarios' && (
            <Box>
                <Alert severity="info" sx={{ mb: 3 }}>
                    Aquí puedes asignar permisos adicionales o denegar permisos específicos a un usuario, anulando lo que hereda de su rol.
                </Alert>
                <FormControl sx={{ minWidth: 300, mb: 3 }}>
                    <InputLabel>Seleccionar Usuario</InputLabel>
                    <Select
                        value={usuarioSeleccionado || ''}
                        label="Seleccionar Usuario"
                        onChange={(e) => setUsuarioSeleccionado(Number(e.target.value))}
                    >
                        {usuarios.map(u => (
                            <MenuItem key={u.id_admin} value={u.id_admin}>
                                {u.nombre_usuario} ({u.rol})
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                {usuarioSeleccionado && !cargando && (
                     <TableContainer component={Paper}>
                     <Table>
                         <TableHead sx={{ bgcolor: 'grey.100' }}>
                             <TableRow>
                                 <TableCell>Permiso</TableCell>
                                 <TableCell>Categoría</TableCell>
                                 <TableCell align="center">Estado</TableCell>
                                 <TableCell align="center">Acciones</TableCell>
                             </TableRow>
                         </TableHead>
                         <TableBody>
                             {permisos.map(permiso => {
                                 const estado = getEstadoPermisoUsuario(permiso.id_permiso);
                                 return (
                                     <TableRow key={permiso.id_permiso}>
                                         <TableCell>
                                             <Typography variant="subtitle2">{permiso.nombre}</Typography>
                                             <Typography variant="caption">{permiso.codigo}</Typography>
                                         </TableCell>
                                         <TableCell sx={{ textTransform: 'capitalize' }}>{permiso.categoria}</TableCell>
                                         <TableCell align="center">
                                             {estado === 'heredado' && <Chip label="Heredado" size="small" />}
                                             {estado === 'otorgado' && <Chip label="Otorgado Explícitamente" color="success" size="small" />}
                                             {estado === 'denegado' && <Chip label="Denegado Explícitamente" color="error" size="small" />}
                                         </TableCell>
                                         <TableCell align="center">
                                             <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                                                 <Button
                                                     size="small"
                                                     variant={estado === 'otorgado' ? 'contained' : 'outlined'}
                                                     color="success"
                                                     onClick={() => handlePermisoUsuario(permiso.id_permiso, 'otorgar')}
                                                 >
                                                     Permitir
                                                 </Button>
                                                 <Button
                                                     size="small"
                                                     variant={estado === 'denegado' ? 'contained' : 'outlined'}
                                                     color="error"
                                                     onClick={() => handlePermisoUsuario(permiso.id_permiso, 'denegar')}
                                                 >
                                                     Denegar
                                                 </Button>
                                                 {estado !== 'heredado' && (
                                                     <Button
                                                         size="small"
                                                         color="inherit"
                                                         onClick={() => handlePermisoUsuario(permiso.id_permiso, 'reset')}
                                                     >
                                                         Reset
                                                     </Button>
                                                 )}
                                             </Box>
                                         </TableCell>
                                     </TableRow>
                                 );
                             })}
                         </TableBody>
                     </Table>
                 </TableContainer>
                )}
            </Box>
        )}
    </Box>
  );
};

export default GestionPermisos;
