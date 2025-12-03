import { useState, useEffect } from 'react';
import {
    Box, Typography, Button, Breadcrumbs, Link, IconButton, TextField,
    Paper, Tabs, Tab, RadioGroup, FormControlLabel, Radio,
    Grid, Tooltip, Alert, Chip, Avatar, List, ListItem, ListItemText, ListItemIcon,
    CircularProgress
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import CloudUploadIcon from '@mui/icons-material/CloudUpload'; // Guardar manual
import CloseIcon from '@mui/icons-material/Close';             // Descartar
import SettingsIcon from '@mui/icons-material/Settings';       // Acciones
import LockIcon from '@mui/icons-material/Lock';
import DragHandleIcon from '@mui/icons-material/DragHandle';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import PublishIcon from '@mui/icons-material/Publish';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import ViewHeadlineIcon from '@mui/icons-material/ViewHeadline';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useForm, Controller, type SubmitHandler } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { usarAuthStore } from '../context/authStore';
import { useDebounce } from '../hooks/useDebounce'; // Asegurarse de tener este hook o implementarlo

import ModalPregunta, { type PreguntaFrontend } from '../components/ModalPregunta';

import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';

// Tipos para el formulario
interface FormularioEncuesta {
    titulo: string;
    publico_objetivo: 'alumnos' | 'docentes' | 'ambos';
    responsable: string;
    restringido_a?: string; // Lista negra 
    prioridad: 'obligatoria' | 'opcional' | 'evaluacion_docente';
    acciones_disparadoras: string[];
    configuracion: {
        paginacion: 'por_pregunta' | 'por_seccion' | 'todas';
        mostrar_progreso: 'porcentaje' | 'numero';
        permitir_saltar: boolean;
    };
    descripcion?: string;
    mensaje_final?: string;
    fecha_inicio: string;
    fecha_fin: string;
}

const CrearEncuesta = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const idEncuesta = searchParams.get("id");
    const usuario = usarAuthStore(state => state.usuario);

    // Estado de la UI
    const [cargandoDatos, setCargandoDatos] = useState(false);
    const [tabActual, setTabActual] = useState(0);
    const [esNuevo, setEsNuevo] = useState(true);
    const [estado, setEstado] = useState<string>('borrador'); // borrador, en_curso, finalizada
    const [errorValidacion, setErrorValidacion] = useState(false);

    // Si es nuevo o está en borrador, es editable.
    const esEditable = esNuevo || estado === 'borrador';

    // ESTADOS PARA PREGUNTAS
    const [modalAbierto, setModalAbierto] = useState(false);
    const [preguntas, setPreguntas] = useState<PreguntaFrontend[]>([]);
    const [preguntaEditando, setPreguntaEditando] = useState<PreguntaFrontend | null>(null);

    // React Hook Form
    const { control, register, handleSubmit, formState: { errors }, reset, setValue, watch } = useForm<FormularioEncuesta>({
        defaultValues: {
            titulo: '',
            publico_objetivo: 'alumnos',
            responsable: usuario?.sub || 'Admin',
            prioridad: 'opcional',
            acciones_disparadoras: ['al_iniciar_sesion'],
            // Fechas por defecto: Mañana inicio del día, Pasado mañana fin del día (como placeholder válido)
            // Backend espera ISO String.
            fecha_inicio: new Date(new Date().setHours(0, 0, 1, 0)).toISOString().slice(0, 16),
            fecha_fin: new Date(new Date().setHours(23, 59, 59, 0)).toISOString().slice(0, 16),
            configuracion: {
                paginacion: 'por_pregunta',
                mostrar_progreso: 'porcentaje',
                permitir_saltar: true
            }
        }
    });

    const prioridad = watch('prioridad');

    // Efecto para Evaluación Docente
    useEffect(() => {
        if (prioridad === 'evaluacion_docente') {
            setValue('acciones_disparadoras', ['al_inscribir_examen']);
        }
    }, [prioridad, setValue]);

    // --- EFECTO: CARGAR DATOS SI ES EDICIÓN ---
    useEffect(() => {
        if (idEncuesta) {
            setEsNuevo(false);
            cargarEncuestaExistente(parseInt(idEncuesta));
        }
    }, [idEncuesta]);

    const cargarEncuestaExistente = async (id: number) => {
        setCargandoDatos(true);
        try {
            const { data } = await api.get(`/admin/encuestas/${id}`);
            console.log("Datos cargados:", data);

            setValue("titulo", data.nombre);
            setValue("descripcion", data.descripcion || '');
            setValue("mensaje_final", data.mensaje_final || '');
            setEstado(data.estado || 'borrador');
            setValue("prioridad", data.prioridad || 'opcional');
            setValue("acciones_disparadoras", data.acciones_disparadoras || []);

            // Cargar fechas (convertir ISO a formato input datetime-local: YYYY-MM-DDTHH:mm)
            if (data.fecha_inicio) setValue("fecha_inicio", data.fecha_inicio.slice(0, 16));
            if (data.fecha_fin) setValue("fecha_fin", data.fecha_fin.slice(0, 16));

            // Cargar configuración asegurando valores por defecto
            if (data.configuracion) {
                setValue("configuracion.paginacion", data.configuracion.paginacion || 'por_pregunta');
                setValue("configuracion.mostrar_progreso", data.configuracion.mostrar_progreso || 'porcentaje');
                setValue("configuracion.permitir_saltar", data.configuracion.permitir_saltar ?? true);
            }

            if (data.reglas && data.reglas.length > 0) {
                setValue("publico_objetivo", data.reglas[0].publico_objetivo);
            }

            const preguntasMapeadas: PreguntaFrontend[] = data.preguntas.map((p: any) => ({
                id_temporal: p.id,
                texto_pregunta: p.texto_pregunta,
                tipo: p.tipo,
                orden: p.orden,
                obligatoria: p.configuracion_json?.obligatoria || false,
                mensaje_error: p.configuracion_json?.mensaje_error || '',
                descripcion: p.configuracion_json?.descripcion || '',
                // Mapeo inverso de matriz si existe
                columnas_matriz: p.configuracion_json?.columnas?.map((c:any) => c.texto) || [],
                // Si es matriz, las filas suelen guardarse en config o en opciones, aquí asumimos opciones
                opciones: p.opciones.map((o: any) => ({
                    texto_opcion: o.texto_opcion,
                    orden: o.orden
                }))
            }));
            // Ordenar estrictamente por el campo orden
            setPreguntas(preguntasMapeadas.sort((a, b) => a.orden - b.orden));

        } catch (error) {
            console.error("Error cargando encuesta:", error);
            toast.error("No se pudo cargar la encuesta");
            navigate('/encuestas');
        } finally {
            setCargandoDatos(false);
        }
    };

    const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
        setTabActual(newValue);
    };

    // --- LÓGICA DE PREGUNTAS ---
    const abrirModalNueva = () => {
        if (!esEditable) return;
        setPreguntaEditando(null);
        setModalAbierto(true);
    };

    // Abre el modal pero preconfigurado para ser tipo "seccion"
    const abrirModalNuevaSeccion = () => {
        if (!esEditable) return;
        setPreguntaEditando({
            id_temporal: Date.now(),
            texto_pregunta: '',
            tipo: 'seccion', // Pre-seleccionar tipo sección
            orden: 0,
            obligatoria: false,
            opciones: []
        });
        setModalAbierto(true);
    };

    const abrirModalEdicion = (pregunta: PreguntaFrontend) => {
        if (!esEditable) return;
        setPreguntaEditando(pregunta);
        setModalAbierto(true);
    };

    const guardarPreguntaLocal = (pregunta: PreguntaFrontend, crearOtra: boolean) => {
        if (preguntaEditando && preguntas.some(p => p.id_temporal === pregunta.id_temporal)) {
            // Actualizar existente
            setPreguntas(prev => prev.map(p => p.id_temporal === pregunta.id_temporal ? pregunta : p));
        } else {
            // Crear nueva (asignar orden al final)
            // Aseguramos que el ID temporal sea único si venimos de "Guardar y Nuevo"
            // El modal ya genera un ID nuevo, pero validamos aquí
            const nuevaConOrden = { ...pregunta, orden: preguntas.length + 1 };
            setPreguntas(prev => [...prev, nuevaConOrden]);
        }

        // AUTO-SAVE IMPLÍCITO (Disparar efecto)
        // Nota: Al actualizar estado 'preguntas', el efecto de auto-save se activará abajo

        if (!crearOtra) {
            setModalAbierto(false);
        } else {
            // Si es crear otra, reseteamos el estado de edición para que el modal sepa que es nueva
            setPreguntaEditando(null);
        }
    };

    const borrarPregunta = (id_temporal: number | string) => {
        if (!esEditable) return;
        const id = typeof id_temporal === 'string' ? Number(id_temporal) : id_temporal;
        if (isNaN(id)) {
            console.error("ID inválido para borrar:", id_temporal);
            return;
        }
        if (window.confirm("¿Estás seguro de borrar este elemento?")) {
            const nuevas = preguntas.filter(p => p.id_temporal !== id);
            const reordenadas = nuevas.map((p, index) => ({ ...p, orden: index + 1 }));
            setPreguntas(reordenadas);
        }
    };

    // Manejador de Drag & Drop
    const onDragEnd = (result: DropResult) => {
        if (!result.destination || !esEditable) return;

        const items = Array.from(preguntas);
        const [reorderedItem] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reorderedItem);

        // Actualizar orden numérico interno después del arrastre
        const updatedItems = items.map((item, index) => ({ ...item, orden: index + 1 }));
        setPreguntas(updatedItems);
    };

    // Acción: Guardar Global (Manual o Auto)
    const guardarEncuesta = async (data: FormularioEncuesta, silencioso = false) => {
        if (!silencioso) setErrorValidacion(false);

        const inicio = new Date(data.fecha_inicio);
        const fin = new Date(data.fecha_fin);
        const ahora = new Date();
        ahora.setMinutes(ahora.getMinutes() - 1);

        if (esNuevo && inicio < ahora) {
            toast.error("La fecha de inicio no puede ser anterior a la actual.");
            return;
        }
        if (fin <= inicio) {
            toast.error("La fecha de fin debe ser posterior a la fecha de inicio.");
            return;
        }

        if (!silencioso) console.log("Guardando...", data);

        try {
            const payload = {
                nombre: data.titulo,
                fecha_inicio: new Date(data.fecha_inicio).toISOString(),
                fecha_fin: new Date(data.fecha_fin).toISOString(),
                prioridad: data.prioridad,
                acciones_disparadoras: data.acciones_disparadoras,
                configuracion: data.configuracion,
                activo: true,
                estado: estado,
                reglas: [{ publico_objetivo: data.publico_objetivo }],
                descripcion: data.descripcion,
                mensaje_final: data.mensaje_final,
                preguntas: preguntas.map((p, index) => ({
                    texto_pregunta: p.texto_pregunta,
                    orden: index + 1,
                    tipo: p.tipo,
                    configuracion_json: {
                        obligatoria: p.obligatoria,
                        mensaje_error: p.mensaje_error,
                        descripcion: p.descripcion,
                        // Mapeo de campos extra de matriz
                        filas: p.filas, // Si existen
                        columnas: p.columnas, // Si existen
                        seleccion_multiple_matriz: p.seleccion_multiple_matriz
                    },
                    activo: true,
                    opciones: p.opciones.map((o, i) => ({
                        texto_opcion: o.texto_opcion,
                        orden: i + 1
                    }))
                }))
            };

            if (esNuevo) {
                const res = await api.post('/admin/encuestas/', payload);
                if (!silencioso) toast.success("Encuesta creada exitosamente");
                setEsNuevo(false);
                navigate(`/encuestas/crear?id=${res.data.id}`, { replace: true });
            } else {
                const res = await api.put(`/admin/encuestas/${idEncuesta}`, payload);
                if (!silencioso) toast.success("Encuesta actualizada exitosamente");
                // Actualizar estado local con la respuesta para asegurar sincronía
                setEstado(res.data.estado);
            }
        } catch (error: any) {
            console.error(error);
            if (!silencioso) {
                const msj = error.response?.data?.detail || "Error al guardar la encuesta";
                toast.error(msj);
            }
        }
    };

    // Auto-save Effect
    // Escuchamos cambios en 'preguntas' y valores del formulario
    const values = watch();
    useEffect(() => {
        if (!esNuevo && idEncuesta) { // Solo auto-guardar si ya existe
            const timer = setTimeout(() => {
                onGuardar(values, true);
            }, 2000); // 2 segundos de debounce
            return () => clearTimeout(timer);
        }
    }, [values, preguntas]); // Dependencias: formulario y estructura preguntas

    // Acciones de Estado
    const cambiarEstadoEncuesta = async (nuevoEstado: 'publicar' | 'finalizar') => {
        const accion = nuevoEstado === 'publicar' ? 'publicar' : 'cerrar';
        if (!window.confirm(`¿Estás seguro de ${accion} la encuesta?`)) return;

        try {
            const endpoint = nuevoEstado === 'publicar' ? 'publicar' : 'finalizar';
            const { data } = await api.post(`/admin/encuestas/${idEncuesta}/${endpoint}`);
            setEstado(data.estado);
            toast.success(`Encuesta ${accion === 'publicar' ? 'publicada' : 'cerrada'} exitosamente`);
        } catch (error) {
            console.error(error);
            toast.error(`Error al ${accion} la encuesta`);
        }
    };

    // Acción: Publicar
    const onPublicar = async () => {
        cambiarEstadoEncuesta('publicar');
    };

    // Acción: Finalizar
    const onFinalizar = async () => {
        cambiarEstadoEncuesta('finalizar');
    };

    // Acción: Probar
    const onProbar = () => {
        if (idEncuesta) window.open(`/encuestas/prueba/${idEncuesta}`, '_blank');
    };

    // Acción: Descartar (X)
    const onDescartar = () => {
        if (window.confirm("¿Estás seguro de descartar los cambios?")) {
            reset();
            navigate('/encuestas');
        }
    };

    // Manejador de error de validación (para mostrar la alerta roja)
    const onError = () => {
        setErrorValidacion(true);
        toast.error("Faltan campos obligatorios", { icon: false, style: { borderLeft: '5px solid red' } });
    };

    if (cargandoDatos) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', height: '100vh', alignItems: 'center' }}><CircularProgress /></Box>;
    }
    return (
        <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>

            {/* 1. CABECERA DE NAVEGACIÓN Y ACCIONES */}
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
                            <Tooltip title="Guardar de forma manual">
                                <IconButton
                                    size="small"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleSubmit(onGuardar, onError)();
                                    }}
                                    color="primary"
                                    disabled={cargandoDatos}
                                >
                                    <CloudUploadIcon />
                                </IconButton>
                            </Tooltip>
                        )}
                        <Tooltip title="Descartar cambios"><IconButton size="small" onClick={onDescartar} color="error"><CloseIcon /></IconButton></Tooltip>
                        <Tooltip title="Acciones"><IconButton size="small"><SettingsIcon /></IconButton></Tooltip>
                    </Box>
                </Box>
                <Box display="flex" gap={1}>
                    {!esNuevo && (
                        <Button variant="outlined" startIcon={<PlayArrowIcon />} onClick={onProbar} sx={{ textTransform: 'none' }}>Probar</Button>
                    )}
                    {!esNuevo && estado === 'borrador' && (
                        <Button variant="contained" color="success" startIcon={<PublishIcon />} onClick={onPublicar} sx={{ textTransform: 'none' }}>Publicar</Button>
                    )}
                    {(estado === 'en_curso' || estado === 'publicado') && (
                        <Button variant="contained" color="warning" startIcon={<CheckCircleIcon />} onClick={onFinalizar} sx={{ textTransform: 'none' }}>Cerrar Encuesta</Button>
                    )}
                    <Button variant="outlined" color="secondary" startIcon={<LockIcon />} sx={{ textTransform: 'none' }}>Salir</Button>
                </Box>
            </Box>

            {/* 2. ALERTA DE VALIDACIÓN */}
            {errorValidacion && <Alert severity="error" variant="filled" onClose={() => setErrorValidacion(false)} sx={{ mb: 2, borderRadius: 1 }}>Faltan algunos campos obligatorios</Alert>}

            {/* 3. FORMULARIO PRINCIPAL */}
            <Paper sx={{ p: 4, flexGrow: 1, borderRadius: 2 }}>
                <form onSubmit={handleSubmit(onGuardar, onError)}>
                    <Grid container spacing={4}>

                        {/* Título Gigante (Input transparente) */}
                        <Grid size={12}>
                            <TextField
                                autoFocus // UX: Foco al abrir
                                fullWidth
                                placeholder="Por ejemplo, Encuesta de Evaluación de Docentes"
                                variant="standard"
                                error={!!errors.titulo}
                                {...register("titulo", { required: true })}
                                disabled={!esEditable}
                                sx={{
                                    '& .MuiInputBase-input': { fontSize: '2rem', fontWeight: 300 },
                                    '& .MuiInput-underline:before': { borderBottom: '1px solid #e0e0e0' },
                                    '& .MuiInput-underline:after': { borderBottom: '2px solid #023E8A' }
                                }}
                            />
                        </Grid >

                        {/* Campos de Cabecera (Responsable, Restricción) */}
                        < Grid size={{ xs: 12, md: 6 }}>
                            <Box display="flex" alignItems="center" gap={2} mb={2}>
                                <Typography variant="body2" fontWeight="bold" width={100}>Responsable</Typography>
                                <Chip
                                    avatar={<Avatar>{usuario?.sub?.charAt(0)}</Avatar>}
                                    label={usuario?.sub}
                                    variant="outlined"
                                />
                            </Box>
                            <Box display="flex" alignItems="center" gap={2}>
                                <Typography variant="body2" fontWeight="bold" width={100}>Restringido a</Typography>
                                <TextField
                                    placeholder="Ej: Facultad de Ingeniería"
                                    variant="standard"
                                    fullWidth
                                    disabled={!esEditable}
                                    {...register("restringido_a")}
                                />
                            </Box>

                            {/* Fechas de Inicio y Fin */}
                            <Box display="flex" gap={2} mt={2}>
                                <TextField
                                    label="Inicio"
                                    type="datetime-local"
                                    fullWidth
                                    InputLabelProps={{ shrink: true }}
                                    {...register("fecha_inicio", { required: true })}
                                    disabled={!esEditable}
                                />
                                <TextField
                                    label="Fin"
                                    type="datetime-local"
                                    fullWidth
                                    InputLabelProps={{ shrink: true }}
                                    {...register("fecha_fin", { required: true })}
                                    disabled={!esEditable}
                                />
                            </Box>
                        </Grid >

                        {/* Radio Buttons (Público Objetivo) */}
                        < Grid size={12} >
                            <Controller
                                name="publico_objetivo"
                                control={control}
                                render={({ field }) => (
                                    <RadioGroup row {...field}>
                                        <FormControlLabel disabled={!esEditable} value="alumnos" control={<Radio />} label="Solo Alumnos" />
                                        <FormControlLabel disabled={!esEditable} value="docentes" control={<Radio />} label="Solo Docentes" />
                                        <FormControlLabel disabled={!esEditable} value="ambos" control={<Radio />} label="Todos (Campus)" />
                                    </RadioGroup>
                                )}
                            />
                        </Grid >

                        {/* 4. TABS DE DETALLE */}
                        < Grid size={12} sx={{ mt: 2 }}>
                            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                                <Tabs value={tabActual} onChange={handleTabChange} aria-label="tabs encuesta">
                                    <Tab label="Preguntas" />
                                    <Tab label="Opciones" />
                                    <Tab label="Descripción" />
                                    <Tab label="Mensaje final" />
                                </Tabs>
                            </Box>

                            {/* Panel: Preguntas */}
                            <Box role="tabpanel" hidden={tabActual !== 0} sx={{ p: 3 }}>
                                {tabActual === 0 && (
                                    <>
                                        <DragDropContext onDragEnd={onDragEnd}>
                                            <Droppable droppableId="lista-preguntas">
                                                {(provided) => (
                                                    <List {...provided.droppableProps} ref={provided.innerRef}>
                                                        {preguntas.map((preg, idx) => (
                                                            <Draggable
                                                                key={preg.id_temporal}
                                                                draggableId={String(preg.id_temporal)}
                                                                index={idx}
                                                                isDragDisabled={!esEditable}
                                                            >
                                                                {(provided) => (
                                                                    <ListItem
                                                                        ref={provided.innerRef}
                                                                        {...provided.draggableProps}
                                                                        sx={{
                                                                            borderBottom: '1px solid #eee',
                                                                            bgcolor: preg.tipo === 'seccion' ? '#e3f2fd' : 'white', // Color distinto para sección
                                                                            '&:hover': { bgcolor: preg.tipo === 'seccion' ? '#bbdefb' : '#f5f5f5' }
                                                                        }}
                                                                        secondaryAction={
                                                                            <Box>
                                                                                {esEditable && (
                                                                                    <>
                                                                                        <IconButton onClick={() => abrirModalEdicion(preg)} title="Editar">
                                                                                            <EditIcon fontSize="small" />
                                                                                        </IconButton>
                                                                                        <IconButton
                                                                                            onClick={(e) => {
                                                                                                e.stopPropagation();
                                                                                                console.log("Borrando pregunta:", preg.id_temporal);
                                                                                                borrarPregunta(preg.id_temporal);
                                                                                            }}
                                                                                            color="error"
                                                                                            title="Borrar"
                                                                                        >
                                                                                            <DeleteIcon fontSize="small" />
                                                                                        </IconButton>
                                                                                    </>
                                                                                )}
                                                                            </Box>
                                                                        }
                                                                    >
                                                                        <ListItemIcon {...provided.dragHandleProps} sx={{ cursor: esEditable ? 'grab' : 'default' }}>
                                                                            <DragHandleIcon color="disabled" />
                                                                        </ListItemIcon>

                                                                        {/* Renderizado condicional según tipo */}
                                                                        {preg.tipo === 'seccion' ? (
                                                                            <ListItemText
                                                                                primary={<Typography variant="subtitle1" fontWeight="bold" color="primary">{preg.texto_pregunta}</Typography>}
                                                                                secondary="Sección"
                                                                            />
                                                                        ) : (
                                                                            <ListItemText
                                                                                primary={`${idx + 1}. ${preg.texto_pregunta}`}
                                                                                secondary={preg.tipo.replace('_', ' ')}
                                                                            />
                                                                        )}
                                                                    </ListItem>
                                                                )}
                                                            </Draggable>
                                                        ))}
                                                        {provided.placeholder}
                                                    </List>
                                                )}
                                            </Droppable>
                                        </DragDropContext>

                                        {/* Botones para agregar */}
                                        {esEditable && (
                                            <Box display="flex" gap={2} mt={2}>
                                                <Button variant="text" startIcon={<AddIcon />} onClick={abrirModalNueva}>
                                                    Agregar una pregunta
                                                </Button>
                                                <Button variant="text" color="secondary" startIcon={<ViewHeadlineIcon />} onClick={abrirModalNuevaSeccion}>
                                                    Agregar una sección
                                                </Button>
                                            </Box>
                                        )}

                                        {preguntas.length === 0 && (
                                            <Typography variant="body2" color="text.secondary" mt={2} fontStyle="italic">
                                                No hay preguntas. Haz clic en "Agregar una pregunta" para comenzar.
                                            </Typography>
                                        )}
                                    </>
                                )}
                            </Box>

                            {/* TAB 2: OPCIONES */}
                            <Box role="tabpanel" hidden={tabActual !== 1} sx={{ p: 3 }}>
                                {tabActual === 1 && (
                                    <Grid container spacing={3}>
                                        <Grid size={{ xs: 12, md: 6 }}>
                                            <Paper sx={{ p: 3 }}>
                                                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', mb: 3 }}>
                                                    PREGUNTAS
                                                </Typography>

                                                <Box mb={4}>
                                                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Paginación</Typography>
                                                    <Controller
                                                        name="configuracion.paginacion"
                                                        control={control}
                                                        render={({ field }) => (
                                                            <RadioGroup {...field}>
                                                                <FormControlLabel disabled={!esEditable} value="por_pregunta" control={<Radio size="small" />} label="Una página por pregunta" />
                                                                <FormControlLabel disabled={!esEditable} value="por_seccion" control={<Radio size="small" />} label="Una página por sección" />
                                                                <FormControlLabel disabled={!esEditable} value="todas" control={<Radio size="small" />} label="Una página con todas las preguntas" />
                                                            </RadioGroup>
                                                        )}
                                                    />
                                                </Box>
                                                {/* ... Resto de Opciones ... */}
                                                <Box mb={4}>
                                                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Mostrar progreso como</Typography>
                                                    <Controller
                                                        name="configuracion.mostrar_progreso"
                                                        control={control}
                                                        render={({ field }) => (
                                                            <RadioGroup {...field}>
                                                                <FormControlLabel disabled={!esEditable} value="porcentaje" control={<Radio size="small" />} label="Porcentaje restante" />
                                                                <FormControlLabel disabled={!esEditable} value="numero" control={<Radio size="small" />} label="Número (Ej: 6 / 10)" />
                                                            </RadioGroup>
                                                        )}
                                                    />
                                                </Box>
                                                <Box>
                                                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                                                        <Typography variant="subtitle2" fontWeight="bold">Permitir saltar entre preguntas</Typography>
                                                    </Box>
                                                    <Controller
                                                        name="configuracion.permitir_saltar"
                                                        control={control}
                                                        render={({ field: { value, onChange } }) => (
                                                            <FormControlLabel
                                                                control={<CheckCircleIcon color={value ? "primary" : "disabled"} onClick={() => esEditable && onChange(!value)} />}
                                                                label={value ? "Habilitado" : "Deshabilitado"}
                                                                disabled={!esEditable}
                                                            />
                                                        )}
                                                    />
                                                </Box>
                                            </Paper>
                                        </Grid>

                                        <Grid size={{ xs: 12, md: 6 }}>
                                            <Paper sx={{ p: 3 }}>
                                                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', mb: 3 }}>
                                                    PARTICIPANTES
                                                </Typography>

                                                <Box mb={4}>
                                                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Prioridad de la Encuesta</Typography>
                                                    <Controller
                                                        name="prioridad"
                                                        control={control}
                                                        render={({ field }) => (
                                                            <RadioGroup {...field}>
                                                                <FormControlLabel disabled={!esEditable} value="obligatoria" control={<Radio size="small" />} label="Obligatoria" />
                                                                <FormControlLabel disabled={!esEditable} value="opcional" control={<Radio size="small" />} label="Opcional" />
                                                                <FormControlLabel disabled={!esEditable} value="evaluacion_docente" control={<Radio size="small" />} label="Evaluación Docente" />
                                                            </RadioGroup>
                                                        )}
                                                    />
                                                </Box>

                                                <Box>
                                                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Acción disparadora</Typography>
                                                    <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                                                        En qué condiciones se mostrará la encuesta.
                                                    </Typography>

                                                    <Controller
                                                        name="acciones_disparadoras"
                                                        control={control}
                                                        render={({ field: { value, onChange } }) => (
                                                            <Box display="flex" flexDirection="column" gap={1}>
                                                                {[
                                                                    { val: 'al_iniciar_sesion', label: 'Al iniciar sesión' },
                                                                    { val: 'al_ver_curso', label: 'Al ver curso' },
                                                                    { val: 'al_inscribir_examen', label: 'Al inscribirse al examen' }
                                                                ].map((opcion) => {
                                                                    const isChecked = value.includes(opcion.val);
                                                                    return (
                                                                        <FormControlLabel
                                                                            key={opcion.val}
                                                                            control={
                                                                                <CheckCircleIcon
                                                                                    color={isChecked ? "primary" : "disabled"}
                                                                                    onClick={() => {
                                                                                        if (!esEditable) return;
                                                                                        if (isChecked) {
                                                                                            onChange(value.filter((v: string) => v !== opcion.val));
                                                                                        } else {
                                                                                            onChange([...value, opcion.val]);
                                                                                        }
                                                                                    }}
                                                                                />
                                                                            }
                                                                            label={opcion.label}
                                                                            disabled={!esEditable}
                                                                        />
                                                                    );
                                                                })}
                                                            </Box>
                                                        )}
                                                    />
                                                </Box>
                                            </Paper>
                                        </Grid>
                                    </Grid>
                                )}
                            </Box>

                            {/* TAB 2: DESCRIPCIÓN */}
                            <Box role="tabpanel" hidden={tabActual !== 2} sx={{ p: 3 }}>
                                {tabActual === 2 && (
                                    <TextField
                                        fullWidth multiline rows={4}
                                        label="Descripción / Encabezado de la encuesta"
                                        placeholder="Esta encuesta tiene como objetivo..."
                                        {...register("descripcion")}
                                    />
                                )}
                            </Box>
                            {/* TAB 3: MENSAJE FINAL */}
                            <Box role="tabpanel" hidden={tabActual !== 3} sx={{ p: 3 }}>
                                {tabActual === 3 && (
                                    <TextField
                                        fullWidth multiline rows={4}
                                        label="Mensaje de agradecimiento"
                                        placeholder="¡Gracias por participar! Sus respuestas han sido guardadas."
                                        {...register("mensaje_final")}
                                    />
                                )}
                            </Box>

                        </Grid >

                    </Grid>
                </form>
            </Paper>

            <ModalPregunta
                open={modalAbierto}
                onClose={() => setModalAbierto(false)}
                onSave={guardarPreguntaLocal}
                preguntaEditar={preguntaEditando}
            />

        </Box >
    );
};

export default CrearEncuesta;