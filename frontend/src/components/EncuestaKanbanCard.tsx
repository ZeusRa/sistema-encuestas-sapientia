import { useState } from 'react';
import {
  Card, CardContent, Typography, Box, Button, Chip, Divider, IconButton, Menu, MenuItem, ListItemIcon, ListItemText
} from '@mui/material';
import AssessmentIcon from '@mui/icons-material/Assessment';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import EditIcon from '@mui/icons-material/Edit';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

interface EncuestaData {
  id: number;
  nombre: string;
  fecha_inicio: string;
  prioridad: string;
  activo: boolean;
  estado?: string; // borrador, en_curso, finalizado
  cantidad_preguntas?: number;
  cantidad_respuestas?: number;
}

interface Props {
  data: EncuestaData;
  onClick: (id: number) => void; // Clic general (ir a edición/lectura)
  onResultados: (id: number) => void; // Botón Resultados
  onEditar: (id: number) => void; // Opción de menú Editar

  // Nuevas acciones
  onDuplicar: (id: number) => void;
  onEliminar: (id: number) => void;
  onProbar: (id: number) => void;
}

const EncuestaKanbanCard = ({ data, onClick, onResultados, onEditar, onDuplicar, onEliminar, onProbar }: Props) => {


  // Estado para el menú de 3 puntos
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const openMenu = Boolean(anchorEl);
  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation(); // Evitar que el clic se propague a la tarjeta
    setAnchorEl(event.currentTarget);
  };
  const handleMenuClose = () => {
    setAnchorEl(null);
  };
  const handleAccion = (accion: 'editar' | 'resultados' | 'duplicar' | 'eliminar' | 'probar') => {
    handleMenuClose();
    if (accion === 'editar') onEditar(data.id);
    if (accion === 'resultados') onResultados(data.id);
    if (accion === 'duplicar') onDuplicar(data.id);
    if (accion === 'eliminar') onEliminar(data.id);
    if (accion === 'probar') onProbar(data.id);
  };

  // Formato de fecha 
  const fecha = new Date(data.fecha_inicio).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' });

  let colorBorde = '#FF9800'; // Naranja (Borrador)
  let colorChip = 'warning';

  if (data.estado === 'en_curso' || data.estado === 'publicado') {
    colorBorde = '#4CAF50'; // Verde
    colorChip = 'success';
  } else if (data.estado === 'finalizado') {
    colorBorde = '#9e9e9e'; // Gris
    colorChip = 'default';
  }


  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        borderLeft: `5px solid ${colorBorde}`,
        transition: 'box-shadow 0.3s, transform 0.2s',
        cursor: 'pointer',
        '&:hover': { boxShadow: 4, transform: 'translateY(-2px)' }
      }}
      onClick={() => onClick(data.id)}
    >
      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        {/* Cabecera */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
          <Typography variant="h6" fontWeight="bold" sx={{ fontSize: '1rem', lineHeight: 1.2 }}>
            {data.nombre}
          </Typography>
          <IconButton size="small" onClick={handleMenuClick}>
            <MoreVertIcon fontSize="small" />
          </IconButton>
        </Box>

        {/* Menú Desplegable */}
        <Menu
          anchorEl={anchorEl}
          open={openMenu}
          onClose={handleMenuClose}
          onClick={(e) => e.stopPropagation()}
        >
          <MenuItem onClick={() => handleAccion('probar')}>
            <ListItemIcon><PlayArrowIcon fontSize="small" color="primary" /></ListItemIcon>
            <ListItemText>Probar Encuesta</ListItemText>
          </MenuItem>
          <Divider />
          <MenuItem onClick={() => handleAccion('editar')}>
            <ListItemIcon><EditIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Editar Encuesta</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => handleAccion('duplicar')}>
            <ListItemIcon><ContentCopyIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Duplicar</ListItemText>
          </MenuItem>
          <MenuItem onClick={() => handleAccion('resultados')}>
            <ListItemIcon><AssessmentIcon fontSize="small" /></ListItemIcon>
            <ListItemText>Ver Resultados</ListItemText>
          </MenuItem>
          <Divider />
          <MenuItem onClick={() => handleAccion('eliminar')} disabled={data.estado !== 'borrador'}>
            <ListItemIcon><DeleteIcon fontSize="small" color={data.estado !== 'borrador' ? 'disabled' : 'error'} /></ListItemIcon>
            <ListItemText sx={{ color: data.estado !== 'borrador' ? 'text.disabled' : 'error.main' }}>Eliminar</ListItemText>
          </MenuItem>
        </Menu>

        {/* Subtítulo */}
        <Box display="flex" alignItems="center" gap={1} mb={2} flexWrap="wrap">
          <Typography variant="caption" color="text.secondary">
            {fecha}
          </Typography>
          {data.prioridad === 'obligatoria' && (
            <Chip label="Obligatoria" size="small" color="error" sx={{ height: 20, fontSize: '0.65rem' }} />
          )}
          {data.estado && (
            <Chip
              label={data.estado.replace('_', ' ').toUpperCase()}
              size="small"
              color={colorChip as any}
              variant="outlined"
              sx={{ height: 20, fontSize: '0.65rem' }}
            />
          )}
        </Box>

        {/* Estadísticas */}
        <Box display="flex" gap={4} mb={2} flexWrap="wrap">
          <Box>
            <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold', lineHeight: 1 }}>
              {data.cantidad_preguntas || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Preguntas
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6" color="secondary.main" sx={{ fontWeight: 'bold', lineHeight: 1 }}>
              {data.cantidad_respuestas || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Terminadas
            </Typography>
          </Box>
        </Box>
      </CardContent>

      <Divider />

      {/* Footer Acciones */}
      <Box sx={{ p: 1, display: 'flex', justifyContent: 'flex-end', bgcolor: '#F8F9FA' }}>
        <Button
          size="small"
          startIcon={<AssessmentIcon />}
          onClick={(e) => { e.stopPropagation(); onResultados(data.id); }}
          variant="text"
          color="primary"
          sx={{ textTransform: 'none', boxShadow: 'none' }}
        >
          Resultados
        </Button>
      </Box>
    </Card>
  );
};

export default EncuestaKanbanCard;