import { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  TextField, Box, Typography, Grid, RadioGroup,
  FormControlLabel, Radio, Tabs, Tab, Checkbox,
  IconButton, Paper, Tooltip, Select, MenuItem, FormControl, InputLabel,
  List, ListItem, ListItemIcon
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import DragHandleIcon from '@mui/icons-material/DragHandle';
import api from '../api/axios';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';

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
  // Matriz
  columnas_matriz?: string[]; // Legacy o alternativo
  filas?: OpcionFrontend[];
  columnas?: OpcionFrontend[];
  seleccion_multiple_matriz?: boolean;
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

  // Matriz: Filas y Columnas (guardadas en configuracion_json o mapeadas)
  const [filasMatriz, setFilasMatriz] = useState<OpcionFrontend[]>([{ texto_opcion: '', orden: 1 }]);
  const [colsMatriz, setColsMatriz] = useState<OpcionFrontend[]>([{ texto_opcion: '', orden: 1 }]);
  const [matrizMultiple, setMatrizMultiple] = useState(false);

  // Configuraciones
  const [obligatoria, setObligatoria] = useState(false);
  const [descripcion, setDescripcion] = useState('');
  const [mensajeError, setMensajeError] = useState('');

  // Plantillas
  const [plantillas, setPlantillas] = useState<{ id: number; nombre: string; detalles: any[] }[]>([]);
  const [plantillaSeleccionada, setPlantillaSeleccionada] = useState<string>('');

  useEffect(() => {
    cargarPlantillas();
  }, []);

  const cargarPlantillas = async () => {
    try {
      const res = await api.get('/plantillas/');
      setPlantillas(res.data);
    } catch (error) {
      console.error("Error al cargar plantillas", error);
    }
  };

  const handleCargarPlantilla = (id: number) => {
    const p = plantillas.find(pl => pl.id === id);
    if (p) {
      setPlantillaSeleccionada(String(id));
      const nuevasOpciones = p.detalles
        .sort((a: any, b: any) => a.orden - b.orden)
        .map((d: any) => ({ texto_opcion: d.texto_opcion, orden: d.orden }));
      setOpciones(nuevasOpciones);
    }
  };

  // Cargar datos si estamos editando
  useEffect(() => {
    if (preguntaEditar) {
      setTexto(preguntaEditar.texto_pregunta);
      setTipo(preguntaEditar.tipo);
      setOpciones(preguntaEditar.opciones.length > 0 ? preguntaEditar.opciones : [{ texto_opcion: '', orden: 1 }]);

      // Cargar Matriz
      if (preguntaEditar.filas) setFilasMatriz(preguntaEditar.filas);
      if (preguntaEditar.columnas) setColsMatriz(preguntaEditar.columnas);
      if (preguntaEditar.seleccion_multiple_matriz !== undefined) setMatrizMultiple(preguntaEditar.seleccion_multiple_matriz);

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
    setFilasMatriz([{ texto_opcion: '', orden: 1 }]);
    setColsMatriz([{ texto_opcion: '', orden: 1 }]);
    setMatrizMultiple(false);
    setObligatoria(false);
    setDescripcion('');
    setMensajeError('');
    setTabActual(0);
    setPlantillaSeleccionada(''); // Reset plantilla
  };

  // Manejo de Opciones (Genérico para Opciones, Filas, Cols)
  const handleAddOptionList = (setter: any, list: OpcionFrontend[]) => {
      setter([...list, { texto_opcion: '', orden: list.length + 1 }]);
  };
  const handleChangeOptionList = (setter: any, list: OpcionFrontend[], index: number, val: string) => {
      const copy = [...list];
      copy[index].texto_opcion = val;
      setter(copy);
  };
  const handleDeleteOptionList = (setter: any, list: OpcionFrontend[], index: number) => {
      setter(list.filter((_, i) => i !== index));
  };

  // Drag & Drop Handler
  const onDragEndList = (result: DropResult, list: OpcionFrontend[], setter: any) => {
      if (!result.destination) return;
      const items = Array.from(list);
      const [reorderedItem] = items.splice(result.source.index, 1);
      items.splice(result.destination.index, 0, reorderedItem);
      // Reindexar orden visualmente si se desea, o simplemente guardar el array ordenado
      setter(items.map((item, index) => ({ ...item, orden: index + 1 })));
  };

  // Wrappers para la lista principal 'opciones'
  const handleAddOpcion = () => handleAddOptionList(setOpciones, opciones);
  const handleChangeOpcion = (i: number, v: string) => handleChangeOptionList(setOpciones, opciones, i, v);
  const handleDeleteOpcion = (i: number) => handleDeleteOptionList(setOpciones, opciones, i);

  // Acción de Guardar
  const handleSave = (crearOtra: boolean) => {
    if (!texto.trim()) {
      alert("La pregunta debe tener un título");
      return;
    }

    // Generar ID temporal fresco si es nuevo (para evitar colisiones en "Guardar y Nuevo")
    const idTemp = preguntaEditar ? preguntaEditar.id_temporal : Date.now();

    // Preparar configuración JSON extendida para matriz
    let configExtra: any = {
        obligatoria: tipo === 'seccion' ? false : obligatoria,
        mensaje_error: mensajeError,
        descripcion,
    };

    let opcionesFinales: OpcionFrontend[] = [];

    if (tipo === 'matriz') {
        configExtra.filas = filasMatriz.filter(o => o.texto_opcion.trim() !== '');
        configExtra.columnas = colsMatriz.filter(o => o.texto_opcion.trim() !== '');
        configExtra.seleccion_multiple_matriz = matrizMultiple;
    } else if (tipo !== 'texto_libre' && tipo !== 'seccion') {
        opcionesFinales = opciones.filter(o => o.texto_opcion.trim() !== '');
    }

    const nuevaPregunta: PreguntaFrontend = {
      id_temporal: idTemp,
      texto_pregunta: texto,
      tipo,
      orden: 0, // Se asigna en el padre
      obligatoria: configExtra.obligatoria,
      opciones: opcionesFinales,
      descripcion,
      mensaje_error: mensajeError,
      ...configExtra
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
      slotProps={{
        backdrop: {
          sx: { backgroundColor: 'rgba(0, 0, 0, 0.7)' }
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
            autoFocus
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
              {tipo === 'opcion_multiple' && (
                <Box sx={{ width: '100%', maxWidth: 200 }}>
                  <Box display="flex" alignItems="center" gap={1} mb={1}><Checkbox checked disabled size="small" /> <Box height={8} width="80%" bgcolor="#e0e0e0" /></Box>
                  <Box display="flex" alignItems="center" gap={1}><Checkbox disabled size="small" /> <Box height={8} width="60%" bgcolor="#e0e0e0" /></Box>
                </Box>
              )}
              {(tipo === 'texto_libre') && (
                <Box sx={{ width: '100%', height: 60, border: '1px solid #bdbdbd', borderRadius: 1, bgcolor: 'white' }} />
              )}
              {tipo === 'matriz' && (
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1, width: '100%' }}>
                      <Box></Box><Box bgcolor="#e0e0e0" height={10}/><Box bgcolor="#e0e0e0" height={10}/>
                      <Box bgcolor="#e0e0e0" height={10}/><Radio disabled size="small"/><Radio disabled size="small"/>
                      <Box bgcolor="#e0e0e0" height={10}/><Radio disabled size="small"/><Radio disabled size="small"/>
                  </Box>
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

            {/* Panel: Respuestas (Opciones / Matriz) */}
            {tabActual === 0 && (
              <Box sx={{ p: 2 }}>
                {tipo === 'texto_libre' ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2, fontStyle: 'italic' }}>
                    Texto libre.
                  </Typography>
                ) : tipo === 'matriz' ? (
                    <Grid container spacing={3}>
                        <Grid size={12}>
                            <FormControlLabel
                                control={<Checkbox checked={matrizMultiple} onChange={(e) => setMatrizMultiple(e.target.checked)} />}
                                label="Permitir selección múltiple por fila"
                            />
                        </Grid>
                        <Grid size={6}>
                            <Typography variant="subtitle2" gutterBottom>Filas (Preguntas)</Typography>
                            <DragDropContext onDragEnd={(res) => onDragEndList(res, filasMatriz, setFilasMatriz)}>
                                <Droppable droppableId="filas-list">
                                    {(provided) => (
                                        <List dense {...provided.droppableProps} ref={provided.innerRef}>
                                            {filasMatriz.map((op, idx) => (
                                                <Draggable key={idx} draggableId={`fila-${idx}`} index={idx}>
                                                    {(provided) => (
                                                        <ListItem ref={provided.innerRef} {...provided.draggableProps} sx={{ px: 0 }}>
                                                            <ListItemIcon {...provided.dragHandleProps} sx={{ minWidth: 30, cursor: 'grab' }}><DragHandleIcon fontSize="small" /></ListItemIcon>
                                                            <TextField fullWidth size="small" value={op.texto_opcion} onChange={(e) => handleChangeOptionList(setFilasMatriz, filasMatriz, idx, e.target.value)} />
                                                            <IconButton size="small" color="error" onClick={() => handleDeleteOptionList(setFilasMatriz, filasMatriz, idx)}><DeleteIcon fontSize="small"/></IconButton>
                                                        </ListItem>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}
                                        </List>
                                    )}
                                </Droppable>
                            </DragDropContext>
                            <Button startIcon={<AddIcon />} size="small" onClick={() => handleAddOptionList(setFilasMatriz, filasMatriz)}>Fila</Button>
                        </Grid>

                        <Grid size={6}>
                            <Typography variant="subtitle2" gutterBottom>Columnas (Opciones)</Typography>
                            <DragDropContext onDragEnd={(res) => onDragEndList(res, colsMatriz, setColsMatriz)}>
                                <Droppable droppableId="cols-list">
                                    {(provided) => (
                                        <List dense {...provided.droppableProps} ref={provided.innerRef}>
                                            {colsMatriz.map((op, idx) => (
                                                <Draggable key={idx} draggableId={`col-${idx}`} index={idx}>
                                                    {(provided) => (
                                                        <ListItem ref={provided.innerRef} {...provided.draggableProps} sx={{ px: 0 }}>
                                                            <ListItemIcon {...provided.dragHandleProps} sx={{ minWidth: 30, cursor: 'grab' }}><DragHandleIcon fontSize="small" /></ListItemIcon>
                                                            <TextField fullWidth size="small" value={op.texto_opcion} onChange={(e) => handleChangeOptionList(setColsMatriz, colsMatriz, idx, e.target.value)} />
                                                            <IconButton size="small" color="error" onClick={() => handleDeleteOptionList(setColsMatriz, colsMatriz, idx)}><DeleteIcon fontSize="small"/></IconButton>
                                                        </ListItem>
                                                    )}
                                                </Draggable>
                                            ))}
                                            {provided.placeholder}
                                        </List>
                                    )}
                                </Droppable>
                            </DragDropContext>
                            <Button startIcon={<AddIcon />} size="small" onClick={() => handleAddOptionList(setColsMatriz, colsMatriz)}>Columna</Button>
                        </Grid>
                    </Grid>
                ) : (
                  <>
                    <Box display="flex" justifyContent="flex-end" mb={2}>
                        <FormControl size="small" sx={{ minWidth: 200 }}>
                            <InputLabel>Cargar Plantilla</InputLabel>
                            <Select
                                value={plantillaSeleccionada}
                                label="Cargar Plantilla"
                                onChange={(e) => handleCargarPlantilla(Number(e.target.value))}
                            >
                                {plantillas.map(p => (
                                    <MenuItem key={p.id} value={p.id}>{p.nombre}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Box>

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