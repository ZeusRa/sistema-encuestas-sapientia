import React, { useState } from 'react';
import {
    Box, Typography, Button, Breadcrumbs, Link, IconButton, TextField,
    Paper, Tabs, Tab, RadioGroup, FormControlLabel, Radio,
    Grid, Tooltip, Alert, Chip, List, ListItem, ListItemText, ListItemIcon,
    CircularProgress, MenuItem
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CloseIcon from '@mui/icons-material/Close';
import SettingsIcon from '@mui/icons-material/Settings';
import Menu from '@mui/material/Menu';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AssessmentIcon from '@mui/icons-material/Assessment';
import LockIcon from '@mui/icons-material/Lock';
import DragHandleIcon from '@mui/icons-material/DragHandle';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import PublishIcon from '@mui/icons-material/Publish';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import ViewHeadlineIcon from '@mui/icons-material/ViewHeadline';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { Controller, FormProvider } from 'react-hook-form'; // Use FormProvider
import api from '../api/axios';
import { toast } from 'react-toastify';

import ModalPregunta from '../components/ModalPregunta';
import ConstructorReglas from '../components/ConstructorReglas';

import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { useEncuestaForm } from '../hooks/useEncuestaForm';

const CrearEncuesta = () => {
    // Usamos el Custom Hook (SOLID: Single Responsibility - Componente solo Renderiza)
    const {
        methods,
        cargandoDatos,
        tabActual,
        setTabActual,
        esNuevo,
        estado,
        esEditable,
        errorValidacion,
        setErrorValidacion,
        usuariosDisponibles,
        preguntas,
        modalAbierto,
        setModalAbierto,
        preguntaEditando,
        guardarDatos,
        cambiarEstadoEncuesta,
        accionesPregunta,
        idEncuesta,
        navigate
    } = useEncuestaForm();

    const { control, register, handleSubmit, formState: { errors }, watch } = methods;

    // Menú de acciones (UI Logic pura)
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const openMenu = Boolean(anchorEl);
    const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget);
    const handleMenuClose = () => setAnchorEl(null);

    const handleAccionMenu = async (accion: 'duplicar' | 'eliminar' | 'resultados') => {
        handleMenuClose();
        if (accion === 'duplicar') {
            try {
                const res = await api.post(`/admin/encuestas/${idEncuesta}/duplicar`);
                toast.success("Encuesta duplicada");
                window.location.href = `/encuestas/crear?id=${res.data.id}`;
            } catch (error) {
                console.error(error);
                toast.error("Error al duplicar");
            }
        } else if (accion === 'eliminar') {
            if (!window.confirm("¿Estás seguro de eliminar esta encuesta?")) return;
            try {
                await api.delete(`/admin/encuestas/${idEncuesta}`);
                toast.success("Encuesta eliminada");
                navigate('/encuestas');
            } catch (error) {
                toast.error("No se pudo eliminar");
            }
        } else if (accion === 'resultados') {
            // watch es necesario aquí, lo sacamos de methods
            navigate(`/reportes/avanzados?encuesta=${encodeURIComponent(watch('titulo') || '')}`);
        }
    };

    const onError = () => {
        setErrorValidacion(true);
        toast.error("Faltan campos obligatorios", { icon: false, style: { borderLeft: '5px solid red' } });
    };

    const onProbar = () => {
        if (idEncuesta) window.open(`/encuestas/prueba/${idEncuesta}`, '_blank');
    };

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setTabActual(newValue);
    };

    if (cargandoDatos) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', height: '100vh', alignItems: 'center' }}><CircularProgress /></Box>;
    }

    return (
        <FormProvider {...methods}>
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>

                {/* 1. CABECERA */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, pb: 1, borderBottom: '1px solid #e0e0e0' }}>
                    <Box display="flex" alignItems="center" gap={2}>
                        <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
                            <Link underline="hover" color="inherit" href="/encuestas">Encuestas</Link>
                            <Typography color="text.primary">{esNuevo ? "Nuevo" : "Edición"}</Typography>
                        </Breadcrumbs>
                        <Chip
                            label={esNuevo ? "Nuevo" : estado.toUpperCase().replace('_', ' ')}
                            color={(estado === 'en_curso' || estado === 'publicado') ? 'success' : estado === 'finalizado' ? 'default' : 'warning'}
                            size="small" sx={{ fontWeight: 'bold', borderRadius: 1 }}
                        />
                        <Box display="flex" gap={1}>
                            {esEditable && (
                                <Tooltip title="Guardar cambios">
                                    <IconButton size="small" onClick={handleSubmit((d) => guardarDatos(d, false), onError)} color="primary"><CloudUploadIcon /></IconButton>
                                </Tooltip>
                            )}
                            <Tooltip title="Descartar / Salir"><IconButton size="small" onClick={() => navigate('/encuestas')} color="error"><CloseIcon /></IconButton></Tooltip>

                            <Tooltip title="Acciones">
                                <IconButton size="small" onClick={handleMenuClick}><SettingsIcon /></IconButton>
                            </Tooltip>
                            <Menu anchorEl={anchorEl} open={openMenu} onClose={handleMenuClose}>
                                <MenuItem onClick={onProbar} disabled={esNuevo}><ListItemIcon><PlayArrowIcon fontSize="small" /></ListItemIcon><ListItemText>Probar Encuesta</ListItemText></MenuItem>
                                <MenuItem onClick={() => handleAccionMenu('duplicar')} disabled={esNuevo}><ListItemIcon><ContentCopyIcon fontSize="small" /></ListItemIcon><ListItemText>Duplicar</ListItemText></MenuItem>
                                <MenuItem onClick={() => handleAccionMenu('resultados')} disabled={esNuevo}><ListItemIcon><AssessmentIcon fontSize="small" /></ListItemIcon><ListItemText>Ver Resultados</ListItemText></MenuItem>
                                <MenuItem onClick={() => handleAccionMenu('eliminar')} disabled={esNuevo || estado !== 'borrador'} sx={{ color: 'error.main' }}>
                                    <ListItemIcon><DeleteIcon fontSize="small" color="error" /></ListItemIcon><ListItemText>Eliminar</ListItemText>
                                </MenuItem>
                            </Menu>
                        </Box>
                    </Box>
                    <Box display="flex" gap={1}>
                        {!esNuevo && (
                            <Button variant="outlined" startIcon={<PlayArrowIcon />} onClick={onProbar} sx={{ textTransform: 'none' }}>Probar</Button>
                        )}
                        {!esNuevo && estado === 'borrador' && (
                            <Button variant="contained" color="success" startIcon={<PublishIcon />} onClick={() => cambiarEstadoEncuesta('publicar')} sx={{ textTransform: 'none' }}>Publicar</Button>
                        )}
                        {(estado === 'en_curso' || estado === 'publicado') && (
                            <Button variant="contained" color="warning" startIcon={<CheckCircleIcon />} onClick={() => cambiarEstadoEncuesta('finalizar')} sx={{ textTransform: 'none' }}>Cerrar Encuesta</Button>
                        )}
                        <Button variant="outlined" color="secondary" startIcon={<LockIcon />} onClick={() => navigate('/encuestas')} sx={{ textTransform: 'none' }}>Salir</Button>
                    </Box>
                </Box>

                {/* 2. ALERTA */}
                {errorValidacion && <Alert severity="error" variant="filled" onClose={() => setErrorValidacion(false)} sx={{ mb: 2, borderRadius: 1 }}>Faltan campos obligatorios</Alert>}

                {/* 3. FORMULARIO */}
                <Paper sx={{ p: 4, flexGrow: 1, borderRadius: 2 }}>
                    <form onSubmit={handleSubmit((d) => guardarDatos(d, false), onError)}>
                        <Grid container spacing={4}>
                            {/* Título */}
                            <Grid size={12}>
                                <TextField
                                    autoFocus fullWidth placeholder="Título de la Encuesta" variant="standard"
                                    error={!!errors.titulo}
                                    {...register("titulo", { required: true })}
                                    disabled={!esEditable}
                                    sx={{ '& .MuiInputBase-input': { fontSize: '2rem', fontWeight: 300 } }}
                                />
                            </Grid>

                            {/* Cabecera */}
                            <Grid size={{ xs: 12, md: 6 }}>
                                <Box display="flex" alignItems="center" gap={2} mb={2}>
                                    <Typography variant="body2" fontWeight="bold" width={100}>Responsable</Typography>
                                    <Controller
                                        name="responsable" control={control}
                                        render={({ field }) => (
                                            <TextField {...field} select size="small" variant="outlined" sx={{ minWidth: 200 }} disabled={!esEditable} label={field.value ? "" : "Seleccionar"}>
                                                {usuariosDisponibles.map((u) => (
                                                    <MenuItem key={u.id_admin || u.nombre_usuario} value={u.nombre_usuario}>
                                                        {u.nombre_usuario}
                                                    </MenuItem>
                                                ))}
                                            </TextField>
                                        )}
                                    />
                                </Box>
                                <Box mt={2}>
                                    <Typography variant="subtitle2" fontWeight="bold" mb={1}>Reglas Avanzadas</Typography>
                                    {esEditable ? (
                                        <Controller name="filtros_json" control={control} render={({ field }) => (
                                            <ConstructorReglas reglas={field.value || []} onChange={field.onChange} />
                                        )} />
                                    ) : (
                                        <Typography variant="body2" color="text.secondary">{(watch('filtros_json') || []).length} reglas definidas</Typography>
                                    )}
                                </Box>
                                <Box display="flex" gap={2} mt={2}>
                                    <TextField label="Inicio" type="datetime-local" fullWidth InputLabelProps={{ shrink: true }} {...register("fecha_inicio", { required: true })} disabled={!esEditable} />
                                    <TextField label="Fin" type="datetime-local" fullWidth InputLabelProps={{ shrink: true }} {...register("fecha_fin", { required: true })} disabled={!esEditable} />
                                </Box>
                            </Grid>

                            {/* Público */}
                            <Grid size={12}>
                                <Controller name="publico_objetivo" control={control} render={({ field }) => (
                                    <RadioGroup row {...field}>
                                        <FormControlLabel disabled={!esEditable} value="alumnos" control={<Radio />} label="Solo Alumnos" />
                                        <FormControlLabel disabled={!esEditable} value="docentes" control={<Radio />} label="Solo Docentes" />
                                        <FormControlLabel disabled={!esEditable} value="ambos" control={<Radio />} label="Todos (Campus)" />
                                    </RadioGroup>
                                )} />
                            </Grid>

                            {/* TABS */}
                            <Grid size={12} sx={{ mt: 2 }}>
                                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                                    <Tabs value={tabActual} onChange={handleTabChange}>
                                        <Tab label="Preguntas" />
                                        <Tab label="Configuración" />
                                        <Tab label="Descripción" />
                                        <Tab label="Mensaje final" />
                                    </Tabs>
                                </Box>

                                {/* PANEL PREGUNTAS */}
                                <Box role="tabpanel" hidden={tabActual !== 0} sx={{ p: 3 }}>
                                    {tabActual === 0 && (
                                        <>
                                            <DragDropContext onDragEnd={accionesPregunta.reordenar}>
                                                <Droppable droppableId="lista-preguntas">
                                                    {(provided) => (
                                                        <List {...provided.droppableProps} ref={provided.innerRef}>
                                                            {preguntas.map((preg, idx) => (
                                                                <Draggable key={preg.id_temporal} draggableId={String(preg.id_temporal)} index={idx} isDragDisabled={!esEditable}>
                                                                    {(provided) => (
                                                                        <ListItem
                                                                            ref={provided.innerRef} {...provided.draggableProps}
                                                                            sx={{ borderBottom: '1px solid #eee', bgcolor: preg.tipo === 'seccion' ? '#e3f2fd' : 'white' }}
                                                                            secondaryAction={esEditable && (
                                                                                <Box>
                                                                                    <IconButton onClick={() => accionesPregunta.editar(preg)}><EditIcon fontSize="small" /></IconButton>
                                                                                    <IconButton type="button" onClick={(e) => { e.stopPropagation(); accionesPregunta.borrar(Number(preg.id_temporal)); }} color="error"><DeleteIcon fontSize="small" /></IconButton>
                                                                                </Box>
                                                                            )}
                                                                        >
                                                                            <ListItemIcon {...provided.dragHandleProps} sx={{ cursor: esEditable ? 'grab' : 'default' }}><DragHandleIcon color="disabled" /></ListItemIcon>
                                                                            <ListItemText
                                                                                primary={preg.tipo === 'seccion' ? <Typography variant="subtitle1" fontWeight="bold" color="primary">{preg.texto_pregunta}</Typography> : `${idx + 1}. ${preg.texto_pregunta}`}
                                                                                secondary={preg.tipo.replace('_', ' ')}
                                                                            />
                                                                        </ListItem>
                                                                    )}
                                                                </Draggable>
                                                            ))}
                                                            {provided.placeholder}
                                                        </List>
                                                    )}
                                                </Droppable>
                                            </DragDropContext>
                                            {esEditable && (
                                                <Box display="flex" gap={2} mt={2}>
                                                    <Button variant="text" startIcon={<AddIcon />} onClick={accionesPregunta.abrirNueva}>Agregar Pregunta</Button>
                                                    <Button variant="text" color="secondary" startIcon={<ViewHeadlineIcon />} onClick={accionesPregunta.abrirNuevaSeccion}>Agregar Sección</Button>
                                                </Box>
                                            )}
                                        </>
                                    )}
                                </Box>

                                {/* PANEL CONFIGURACION */}
                                <Box role="tabpanel" hidden={tabActual !== 1} sx={{ p: 3 }}>
                                    {tabActual === 1 && (
                                        <Grid container spacing={3}>
                                            <Grid size={{ xs: 12, md: 6 }}>
                                                <Typography variant="subtitle2" fontWeight="bold">Paginación</Typography>
                                                <Controller name="configuracion.paginacion" control={control} render={({ field }) => (
                                                    <RadioGroup {...field}>
                                                        <FormControlLabel disabled={!esEditable} value="por_pregunta" control={<Radio size="small" />} label="Por Pregunta" />
                                                        <FormControlLabel disabled={!esEditable} value="por_seccion" control={<Radio size="small" />} label="Por Sección" />
                                                        <FormControlLabel disabled={!esEditable} value="todas" control={<Radio size="small" />} label="Una sola página" />
                                                    </RadioGroup>
                                                )} />
                                            </Grid>
                                            <Grid size={{ xs: 12, md: 6 }}>
                                                <Typography variant="subtitle2" fontWeight="bold">Prioridad</Typography>
                                                <Controller name="prioridad" control={control} render={({ field }) => (
                                                    <RadioGroup {...field}>
                                                        <FormControlLabel disabled={!esEditable} value="opcional" control={<Radio size="small" />} label="Opcional" />
                                                        <FormControlLabel disabled={!esEditable} value="obligatoria" control={<Radio size="small" />} label="Obligatoria" />
                                                        <FormControlLabel disabled={!esEditable} value="evaluacion_docente" control={<Radio size="small" />} label="Evaluación Docente" />
                                                    </RadioGroup>
                                                )} />
                                            </Grid>
                                            {/* Campo agregado: Acciones Disparadoras */}
                                            <Grid size={{ xs: 12, md: 6 }}>
                                                <Typography variant="subtitle2" fontWeight="bold">Acciones Disparadoras</Typography>
                                                <Controller
                                                    name="acciones_disparadoras"
                                                    control={control}
                                                    render={({ field }) => (
                                                        <TextField
                                                            {...field}
                                                            select
                                                            fullWidth
                                                            size="small"
                                                            SelectProps={{
                                                                multiple: true,
                                                                renderValue: (selected) => (selected as string[]).map(val => val.replace(/_/g, ' ')).join(', ')
                                                            }}
                                                            label="Seleccionar acciones"
                                                            disabled={!esEditable || watch('prioridad') === 'evaluacion_docente'}
                                                        >
                                                            <MenuItem value="al_iniciar_sesion">Al Iniciar Sesión</MenuItem>
                                                            <MenuItem value="al_ver_curso">Al Ver Curso</MenuItem>
                                                            <MenuItem value="al_inscribir_examen">Al Inscribir Examen</MenuItem>
                                                        </TextField>
                                                    )}
                                                />
                                                {watch('prioridad') === 'evaluacion_docente' && (
                                                    <Typography variant="caption" color="text.secondary">
                                                        * Obligatorio para Evaluación Docente
                                                    </Typography>
                                                )}
                                            </Grid>
                                        </Grid>
                                    )}
                                </Box>

                                {/* PANELES SIMPLES */}
                                <Box role="tabpanel" hidden={tabActual !== 2} sx={{ p: 3 }}>
                                    {tabActual === 2 && <TextField fullWidth multiline rows={4} label="Descripción pública" {...register("descripcion")} disabled={!esEditable} />}
                                </Box>
                                <Box role="tabpanel" hidden={tabActual !== 3} sx={{ p: 3 }}>
                                    {tabActual === 3 && <TextField fullWidth multiline rows={4} label="Mensaje de Agradecimiento" {...register("mensaje_final")} disabled={!esEditable} />}
                                </Box>
                            </Grid>
                        </Grid>
                    </form>
                </Paper>
            </Box>

            {/* MODAL PREGUNTA */}
            <ModalPregunta
                open={modalAbierto}
                onClose={() => setModalAbierto(false)}
                onSave={accionesPregunta.agregar}
                preguntaEditar={preguntaEditando}
            />
        </FormProvider>
    );
};

export default CrearEncuesta;