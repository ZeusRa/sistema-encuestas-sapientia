import { useEffect, useState } from 'react';
import {
  Box, Typography, Button, Breadcrumbs, Link, IconButton,
  Grid, CircularProgress, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper, Chip, Avatar
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ViewModuleIcon from '@mui/icons-material/ViewModule'; // Icono Kanban
import ViewListIcon from '@mui/icons-material/ViewList';     // Icono Lista
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import api from '../api/axios';
import EncuestaKanbanCard from '../components/EncuestaKanbanCard';
import SearchBar from '../components/SearchBar';
import { useNavigate } from 'react-router-dom';

// Tipo para la encuesta
interface Encuesta {
  id: number;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  prioridad: string;
  activo: boolean;
  reglas: { publico_objetivo: string }[];
  estado: string; // borrador, en_curso, finalizado

  cantidad_preguntas: number;
  cantidad_respuestas: number;
  // Simularemos el responsable porque la API básica de listar no lo trae aun
  responsable?: string;
  asignados_count?: number; // Simulado
}

const Encuestas = () => {
  const [encuestas, setEncuestas] = useState<Encuesta[]>([]);
  const [cargando, setCargando] = useState(true);
  const [vista, setVista] = useState<'kanban' | 'lista'>('kanban');
  const navigate = useNavigate();

  useEffect(() => {
    const cargarEncuestas = async () => {
      try {
        if (import.meta.env.DEV) console.log("Cargando encuestas...");
        const respuesta = await api.get('/admin/encuestas/');
        if (import.meta.env.DEV) console.log("Respuesta API Encuestas:", respuesta.data);

        if (Array.isArray(respuesta.data)) {
          const datosEnriquecidos = respuesta.data.map((e: any) => ({
            ...e,
            asignados_count: Math.floor(Math.random() * 200) + 50, // Mock
            responsable: "Admin" // Mock
          }));
          setEncuestas(datosEnriquecidos);
        } else {
          if (import.meta.env.DEV) console.error("Formato de respuesta inesperado:", respuesta.data);
          setEncuestas([]);
        }
      } catch (error) {
        console.error("Error cargando encuestas", error);
      } finally {
        setCargando(false);
      }
    };
    cargarEncuestas();
  }, []);

  // Acciones de Navegación
  const irAEdicion = (id: number) => navigate(`/encuestas/crear?id=${id}`); // Modo edición (usaremos query param o ruta dinámica)
  const irAResultados = (id: number) => {
    const encuesta = encuestas.find(e => e.id === id);
    if (encuesta) {
      navigate(`/reportes/avanzados?encuesta=${encodeURIComponent(encuesta.nombre)}`);
    }
  };

  // Acciones (Duplicar, Eliminar)
  const handleDuplicar = async (id: number) => {
    try {
      const res = await api.post(`/admin/encuestas/${id}/duplicar`);
      navigate(`/encuestas/crear?id=${res.data.id}`); // Ir a la copia
    } catch (error) {
      console.error("Error duplicando", error);
    }
  };

  const handleEliminar = async (id: number) => {
    if (!confirm("¿Estás seguro de eliminar esta encuesta?")) return;
    try {
      await api.delete(`/admin/encuestas/${id}`);
      // Recargar lista
      setEncuestas(prev => prev.filter(e => e.id !== id));
    } catch (error) {
      console.error("Error eliminando", error);
      alert("No se puede eliminar la encuesta (probablemente no esté en borrador).");
    }
  };

  const handleProbar = (id: number) => {
    window.open(`/encuestas/prueba/${id}`, '_blank');
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>

      {/* 1. BARRA DE CONTROL SUPERIOR (Action Bar) */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
          pb: 2,
          borderBottom: '1px solid #e0e0e0'
        }}
      >
        {/* Izquierda: Título y Breadcrumbs */}
        <Box>
          <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
            <Link underline="hover" color="inherit" href="/dashboard">
              Inicio
            </Link>
            <Typography color="text.primary">Encuestas</Typography>
          </Breadcrumbs>
          <Typography variant="h5" fontWeight="bold" color="primary.main" sx={{ mt: 0.5 }}>
            Encuestas
          </Typography>
        </Box>

        {/* Centro: Buscador */}
        <SearchBar />

        {/* Derecha: Paginación y Vistas */}
        <Box display="flex" alignItems="center" gap={2}>
          {/* Paginación Corregida - Muestra rango real de items */}
          <Box display="flex" alignItems="center" color="text.secondary">
            <Typography variant="body2" sx={{ mr: 1 }}>
              {encuestas.length > 0 ? `1-${encuestas.length}` : '0'} / {encuestas.length}
            </Typography>
            <IconButton size="small" disabled><NavigateBeforeIcon /></IconButton>
            <IconButton size="small" disabled={encuestas.length === 0}><NavigateNextIcon /></IconButton>
          </Box>

          {/* Switcher de Vistas */}
          <Box sx={{ border: '1px solid #e0e0e0', borderRadius: 1, display: 'flex' }}>
            <IconButton
              size="small"
              onClick={() => setVista('kanban')}
              color={vista === 'kanban' ? 'primary' : 'default'}
              sx={{ borderRadius: 0, borderRight: '1px solid #e0e0e0', bgcolor: vista === 'kanban' ? '#e3f2fd' : 'transparent' }}
            >
              <ViewModuleIcon />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => setVista('lista')}
              color={vista === 'lista' ? 'primary' : 'default'}
              sx={{ borderRadius: 0, bgcolor: vista === 'lista' ? '#e3f2fd' : 'transparent' }}
            >
              <ViewListIcon />
            </IconButton>
          </Box>
        </Box>
      </Box>

      {/* 2. BARRA DE ACCIONES */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/encuestas/crear')}
          sx={{ boxShadow: 'none', textTransform: 'none', borderRadius: 1 }}
        >
          Nuevo
        </Button>
      </Box>

      {/* 3. ZONA DE REGISTROS (Kanban) */}
      {cargando ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>
      ) : (
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          {encuestas.length === 0 ? (
            <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', opacity: 0.7 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>No hay encuestas creadas</Typography>
            </Box>
          ) : (
            <>
              {/* VISTA KANBAN */}
              {vista === 'kanban' && (
                <Grid container spacing={2}>
                  {encuestas.map((encuesta) => (
                    <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={encuesta.id}>
                      <EncuestaKanbanCard
                        data={encuesta}
                        onClick={irAEdicion}
                        onResultados={irAResultados}
                        onEditar={irAEdicion}
                        // Nuevas props para acciones
                        onDuplicar={() => handleDuplicar(encuesta.id)}
                        onEliminar={() => handleEliminar(encuesta.id)}
                        onProbar={() => handleProbar(encuesta.id)}
                      />
                    </Grid>
                  ))}
                </Grid>
              )}

              {/* VISTA LISTA */}
              {vista === 'lista' && (
                <TableContainer component={Paper} sx={{ boxShadow: 'none', border: '1px solid #e0e0e0' }}>
                  <Table sx={{ minWidth: 650 }} aria-label="lista de encuestas">
                    <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Título de la Encuesta</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Responsable</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Creación</TableCell>
                        <TableCell sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Cierre</TableCell>
                        <TableCell align="center" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Asignados</TableCell>
                        <TableCell align="center" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Respuestas</TableCell>
                        <TableCell align="center" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>Estado</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {encuestas.map((row) => (
                        <TableRow
                          key={row.id}
                          hover
                          onClick={() => irAEdicion(row.id)}
                          sx={{ cursor: 'pointer' }}
                        >
                          <TableCell component="th" scope="row" sx={{ fontWeight: 500, color: 'primary.main' }}>
                            {row.nombre}
                          </TableCell>
                          <TableCell>
                            <Box display="flex" alignItems="center" gap={1}>
                              <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>{row.responsable?.charAt(0)}</Avatar>
                              {row.responsable}
                            </Box>
                          </TableCell>
                          <TableCell>{new Date(row.fecha_inicio).toLocaleDateString()}</TableCell>
                          <TableCell>{new Date(row.fecha_fin).toLocaleDateString()}</TableCell>
                          <TableCell align="center">{row.asignados_count}</TableCell>
                          <TableCell align="center">
                            <Chip label={row.cantidad_respuestas} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={row.estado ? row.estado.toUpperCase().replace('_', ' ') : "BORRADOR"}
                              color={
                                (row.estado === 'en_curso' || row.estado === 'publicado') ? "success" :
                                  row.estado === 'finalizado' ? "default" : "warning"
                              }
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  );
};

export default Encuestas;