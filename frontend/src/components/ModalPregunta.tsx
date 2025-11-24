import { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  TextField, Box, Typography, Grid, RadioGroup,
  FormControlLabel, Radio, Tabs, Tab, Checkbox,
  IconButton, Paper, Tooltip
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

// Tipos de datos (deben coincidir con el Backend)
export type TipoPreguntaFrontend = 'texto_libre' | 'opcion_unica' | 'opcion_multiple' | 'matriz' | 'seccion';

export interface OpcionFrontend {
  texto_opcion: string;
  orden: number;
}

export interface PreguntaFrontend {
  id_temporal: number; // Para identificarla antes de guardar en BD
  texto_pregunta: string;
  tipo: TipoPreguntaFrontend;
  orden: number;
  obligatoria: boolean;
  opciones: OpcionFrontend[];
  // Configuraciones extra (JSONB en backend)
  descripcion?: string;
  mensaje_error?: string;
  columnas_matriz?: string[]; // Para tipo matriz
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (pregunta: PreguntaFrontend, crearOtra: boolean) => void;
  preguntaEditar?: PreguntaFrontend | null;
}

const ModalPregunta = ({ open, onClose, onSave, preguntaEditar }: Props) => {
  // Estados del formulario local
  const [texto, setTexto] = useState('');
  const [tipo, setTipo] = useState<TipoPreguntaFrontend>('opcion_unica');
  const [tabActual, setTabActual] = useState(0);

  // Opciones (Respuestas)
  const [opciones, setOpciones] = useState<OpcionFrontend[]>([{ texto_opcion: '', orden: 1 }]);

  // Configuraciones
  const [obligatoria, setObligatoria] = useState(false);
  const [descripcion, setDescripcion] = useState('');
  const [mensajeError, setMensajeError] = useState('');

  // Cargar datos si estamos editando
  useEffect(() => {
    if (preguntaEditar) {
      setTexto(preguntaEditar.texto_pregunta);
      setTipo(preguntaEditar.tipo);
      setOpciones(preguntaEditar.opciones.length > 0 ? preguntaEditar.opciones : [{ texto_opcion: '', orden: 1 }]);
      setObligatoria(preguntaEditar.obligatoria);
      setDescripcion(preguntaEditar.descripcion || '');
      setMensajeError(preguntaEditar.mensaje_error || '');
    } else {
      // Resetear para nueva pregunta
      limpiarFormulario();
    }
  }, [preguntaEditar, open]);

  const limpiarFormulario = () => {
    setTexto('');
    setTipo('opcion_unica');
    setOpciones([{ texto_opcion: '', orden: 1 }]);
    setObligatoria(false);
    setDescripcion('');
    setMensajeError('');
    setTabActual(0);
  };

  // Manejo de Opciones
  const handleAddOpcion = () => {
    setOpciones([...opciones, { texto_opcion: '', orden: opciones.length + 1 }]);
  };

  const handleChangeOpcion = (index: number, valor: string) => {
    const nuevas = [...opciones];
    nuevas[index].texto_opcion = valor;
    setOpciones(nuevas);
  };

  const handleDeleteOpcion = (index: number) => {
    const nuevas = opciones.filter((_, i) => i !== index);
    setOpciones(nuevas);
  };

  // Acción de Guardar
  const handleSave = (crearOtra: boolean) => {
    if (!texto.trim()) {
      alert("La pregunta debe tener un título");
      return;
    }

    const nuevaPregunta: PreguntaFrontend = {
      id_temporal: preguntaEditar?.id_temporal || Date.now(),
      texto_pregunta: texto,
      tipo,
      orden: 0,
      obligatoria: tipo === 'seccion' ? false : obligatoria,
      opciones: (tipo === 'texto_libre' || tipo === 'seccion') ? [] : opciones.filter(o => o.texto_opcion.trim() !== ''),
      descripcion,
      mensaje_error: mensajeError
    };

    onSave(nuevaPregunta, crearOtra);
    if (crearOtra) {
      limpiarFormulario();
    } else {
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
      // Atenuado de fondo (Backdrop)
      slotProps={{
        backdrop: {
          sx: { backgroundColor: 'rgba(0, 0, 0, 0.7)' } // Más oscuro
        }
      }}
    >
      <DialogTitle sx={{ borderBottom: '1px solid #e0e0e0', pb: 1 }}>
        {preguntaEditar ? 'Editar' : 'Crear'} {tipo === 'seccion' ? 'Sección' : 'Pregunta'}
      </DialogTitle>

      <DialogContent dividers>
        <Box mb={3} mt={1}>
          <Typography variant="caption" fontWeight="bold" color="primary">
            {tipo === 'seccion' ? 'Título de la Sección' : 'Pregunta'}
          </Typography>
          <TextField
            fullWidth
            placeholder={tipo === 'seccion' ? "Ej: Información Personal" : "Ej: ¿Qué opinas...?"}
            variant="standard"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            sx={{
              '& .MuiInputBase-input': { fontSize: '1.2rem', fontWeight: tipo === 'seccion' ? 'bold' : 'normal' },
              '& .MuiInput-underline:after': { borderBottom: '2px solid #023E8A' }
            }}
          />
        </Box>

        <Grid container spacing={4}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography variant="caption" fontWeight="bold" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Tipo de elemento
            </Typography>
            <RadioGroup value={tipo} onChange={(e) => setTipo(e.target.value as TipoPreguntaFrontend)}>
              <FormControlLabel value="seccion" control={<Radio size="small" color="secondary" />} label={<Typography fontWeight="bold">Título (Sección)</Typography>} />
              <FormControlLabel value="opcion_unica" control={<Radio size="small" />} label="Opción múltiple (una respuesta)" />
              <FormControlLabel value="opcion_multiple" control={<Radio size="small" />} label="Opción múltiple (varias respuestas)" />
              <FormControlLabel value="texto_libre" control={<Radio size="small" />} label="Cuadro de texto" />
              <FormControlLabel value="matriz" control={<Radio size="small" />} label="Matriz" />
            </RadioGroup>
          </Grid>

          {/* 3. Vista Previa (Derecha) */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Paper
              variant="outlined"
              sx={{
                p: 3, height: '100%', bgcolor: '#f8f9fa',
                display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'
              }}
            >
              <Typography variant="caption" color="text.disabled" mb={2}>VISTA PREVIA</Typography>
              {tipo === 'seccion' && (
                <Box sx={{ width: '100%', p: 1, bgcolor: '#e3f2fd', borderLeft: '4px solid #023E8A' }}>
                  <Typography variant="h6" color="primary.main">Título de Sección</Typography>
                </Box>
              )}
              {tipo === 'opcion_unica' && (
                <Box sx={{ width: '100%', maxWidth: 200 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}><Radio checked disabled size="small" /> <Box height={8} width="80%" bgcolor="#e0e0e0" /></Box>
                  <Box display="flex" alignItems="center" gap={1}><Radio disabled size="small" /> <Box height={8} width="60%" bgcolor="#e0e0e0" /></Box>
                </Box>
              )}
              {(tipo === 'texto_libre') && (
                <Box sx={{ width: '100%', height: 60, border: '1px solid #bdbdbd', borderRadius: 1, bgcolor: 'white' }} />
              )}
            </Paper>
          </Grid>
        </Grid>

        {/* 4. Tabs de Configuración */}
        {tipo !== 'seccion' && (
          <>
            <Box sx={{ mt: 3, borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabActual} onChange={(_, v) => setTabActual(v)}>
                <Tab label="Respuestas" />
                <Tab label="Descripción" />
                <Tab label="Opciones" />
              </Tabs>
            </Box>

            {/* Panel: Respuestas (Opciones) */}
            {tabActual === 0 && (
              <Box sx={{ p: 2 }}>
                {tipo === 'texto_libre' ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, fontStyle: 'italic' }}>
                    Texto libre.
                  </Typography>
                ) : (
                  <>
                    {opciones.map((opcion, idx) => (
                      <Box key={idx} display="flex" alignItems="center" gap={1} mb={1}>
                        <TextField
                          fullWidth size="small" placeholder={`Opción ${idx + 1}`}
                          value={opcion.texto_opcion}
                          onChange={(e) => handleChangeOpcion(idx, e.target.value)}
                        />
                        <IconButton size="small" color="error" onClick={() => handleDeleteOpcion(idx)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    ))}
                    <Button startIcon={<AddIcon />} size="small" onClick={handleAddOpcion} sx={{ mt: 1 }}>Agregar opción</Button>
                  </>
                )}
              </Box>
            )}

            {/* Panel: Descripción */}
            {tabActual === 1 && (
              <Box sx={{ p: 2 }}>
                <TextField
                  fullWidth multiline rows={3}
                  label="Instrucciones adicionales"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                />
              </Box>
            )}

            {/* Panel: Opciones (Validaciones) */}
            {tabActual === 2 && (
              <Box sx={{ p: 2 }}>
                <Grid container spacing={4}>
                  <Grid size={6}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>RESTRICCIONES</Typography>

                    <Box display="flex" alignItems="center" gap={1}>
                      <FormControlLabel
                        control={<Checkbox checked={obligatoria} onChange={(e) => setObligatoria(e.target.checked)} />}
                        label="Respuesta obligatoria"
                      />
                    </Box>

                    {obligatoria && (
                      <TextField
                        fullWidth
                        size="small"
                        margin="dense"
                        label="Mensaje de error"
                        placeholder="Esta pregunta requiere una respuesta."
                        value={mensajeError}
                        onChange={(e) => setMensajeError(e.target.value)}
                      />
                    )}
                  </Grid>

                  <Grid size={6}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle2" fontWeight="bold">VISUALIZACIÓN CONDICIONAL</Typography>
                      <Tooltip title="Muestra esta pregunta solo si se cumple una condición previa">
                        <HelpOutlineIcon fontSize="small" color="action" sx={{ cursor: 'help' }} />
                      </Tooltip>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      (Funcionalidad avanzada disponible en futuras versiones)
                    </Typography>
                  </Grid>
                </Grid>
              </Box>

            )}
          </>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: '#F8F9FA' }}>
        <Button variant="contained" onClick={() => handleSave(false)}>Guardar y cerrar</Button>
        <Button variant="outlined" onClick={() => handleSave(true)}>Guardar y crear nuevo</Button>
        <Button onClick={onClose}>Descartar</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ModalPregunta;