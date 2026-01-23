import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../api/axios';
import { usarAuthStore } from '../context/authStore';
import { type PreguntaFrontend } from '../components/ModalPregunta';
import { type ReglaRestriccion } from '../components/ConstructorReglas';
import { type DropResult } from '@hello-pangea/dnd';

// Definición de Tipos y Interfaces
export interface FormularioEncuesta {
    titulo: string;
    publico_objetivo: 'alumnos' | 'docentes' | 'ambos';
    responsable: string;
    restringido_a?: string;
    filtros_json?: ReglaRestriccion[];
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

export const useEncuestaForm = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const idEncuesta = searchParams.get("id");
    const usuario = usarAuthStore(state => state.usuario);

    // Estado Local
    const [cargandoDatos, setCargandoDatos] = useState(false);
    const [tabActual, setTabActual] = useState(0);
    const [esNuevo, setEsNuevo] = useState(true);
    const [estado, setEstado] = useState<string>('borrador');
    const [errorValidacion, setErrorValidacion] = useState(false);

    // Estado de Preguntas
    const [modalAbierto, setModalAbierto] = useState(false);
    const [preguntas, setPreguntas] = useState<PreguntaFrontend[]>([]);
    const [preguntaEditando, setPreguntaEditando] = useState<PreguntaFrontend | null>(null);

    // Estado Usuarios
    const [usuariosDisponibles, setUsuariosDisponibles] = useState<any[]>([]);
    const [cargandoUsuarios, setCargandoUsuarios] = useState(true);

    const esEditable = esNuevo || estado === 'borrador';

    // Constantes
    const TODAS_ACCIONES_DISPARADORAS = ['al_iniciar_sesion', 'al_ver_curso', 'al_inscribir_examen'];

    // Configuración React Hook Form
    const methods = useForm<FormularioEncuesta>({
        defaultValues: {
            titulo: '',
            publico_objetivo: 'alumnos',
            responsable: usuario?.sub || 'Admin',
            prioridad: 'opcional',
            acciones_disparadoras: [], // Por defecto vacío para Opcional/Obligatoria
            fecha_inicio: new Date(new Date().setHours(0, 0, 1, 0)).toISOString().slice(0, 16),
            fecha_fin: new Date(new Date().setHours(23, 59, 59, 0)).toISOString().slice(0, 16),
            configuracion: {
                paginacion: 'por_pregunta',
                mostrar_progreso: 'porcentaje',
                permitir_saltar: true
            },
            filtros_json: []
        }
    });

    const { setValue, watch, reset } = methods;
    const prioridad = watch('prioridad');

    // --- EFECTOS ---

    // 1. Efecto Evaluación Docente
    useEffect(() => {
        if (prioridad === 'evaluacion_docente') {
            setValue('acciones_disparadoras', TODAS_ACCIONES_DISPARADORAS);
        } else {
            // Opcional: Si cambia a otra prioridad, ¿limpiamos o dejamos lo que estaba?
            // El requerimiento dice "por defecto ninguna", pero si el usuario ya eligió algo, mejor no borrarlo agresivamente 
            // a menos que sea el cambio inicial.
            // Para simplificar y cumplir "por defecto ninguna", si venimos de 'evaluacion_docente', podríamos limpiar.
            // Pero mejor dejemos que el usuario decida.
        }
    }, [prioridad, setValue]);

    // 2. Cargar Datos Iniciales
    useEffect(() => {
        if (idEncuesta) {
            setEsNuevo(false);
            cargarEncuestaExistente(parseInt(idEncuesta));
        }
    }, [idEncuesta]);

    // 3. Cargar Usuarios
    useEffect(() => {
        const fetchUsuarios = async () => {
            try {
                const res = await api.get('/usuarios/');
                setUsuariosDisponibles(res.data);
            } catch (error) {
                if (import.meta.env.DEV) console.warn("No se pudo cargar lista de usuarios", error);
                if (usuario?.sub) {
                    setUsuariosDisponibles([{ nombre_usuario: usuario.sub }]);
                }
            } finally {
                setCargandoUsuarios(false);
            }
        };
        fetchUsuarios();
    }, [usuario]);

    // 4. Sincronizar Responsable
    useEffect(() => {
        if (!cargandoUsuarios && usuariosDisponibles.length > 0 && usuario?.sub) {
            if (!watch('responsable') || watch('responsable') === 'Admin') {
                setValue('responsable', usuario.sub);
            }
        }
    }, [cargandoUsuarios, usuariosDisponibles, usuario, setValue, watch]);

    // 5. Auto-guardado
    const values = watch();
    useEffect(() => {
        if (!esNuevo && idEncuesta) {
            const timer = setTimeout(() => {
                guardarDatos(values, true);
            }, 2000);
            return () => clearTimeout(timer);
        }
    }, [values, preguntas]);


    // --- FUNCIONES DE CARGA Y GUARDADO ---

    const cargarEncuestaExistente = async (id: number) => {
        setCargandoDatos(true);
        try {
            const { data } = await api.get(`/admin/encuestas/${id}`);

            setValue("titulo", data.nombre);
            setValue("descripcion", data.descripcion || '');
            setValue("mensaje_final", data.mensaje_final || '');
            setEstado(data.estado || 'borrador');
            setValue("prioridad", data.prioridad || 'opcional');
            setValue("acciones_disparadoras", data.acciones_disparadoras || []);
            if (data.fecha_inicio) setValue("fecha_inicio", data.fecha_inicio.slice(0, 16));
            if (data.fecha_fin) setValue("fecha_fin", data.fecha_fin.slice(0, 16));

            if (data.configuracion) {
                setValue("configuracion.paginacion", data.configuracion.paginacion || 'por_pregunta');
                setValue("configuracion.mostrar_progreso", data.configuracion.mostrar_progreso || 'porcentaje');
                setValue("configuracion.permitir_saltar", data.configuracion.permitir_saltar ?? true);
            }

            if (data.reglas && data.reglas.length > 0) {
                setValue("publico_objetivo", data.reglas[0].publico_objetivo);
                if (data.reglas[0].filtros_json) {
                    setValue("filtros_json", data.reglas[0].filtros_json);
                }
            }

            const preguntasMapeadas: PreguntaFrontend[] = data.preguntas.map((p: any) => ({
                id_temporal: p.id,
                texto_pregunta: p.texto_pregunta,
                tipo: p.tipo,
                orden: p.orden,
                obligatoria: p.configuracion_json?.obligatoria || false,
                mensaje_error: p.configuracion_json?.mensaje_error || '',
                descripcion: p.configuracion_json?.descripcion || '',
                filas: p.configuracion_json?.filas || [],
                columnas: p.configuracion_json?.columnas || [],
                seleccion_multiple_matriz: p.configuracion_json?.seleccion_multiple_matriz,
                columnas_matriz: p.configuracion_json?.columnas?.map((c: any) => c.texto) || [],
                opciones: p.opciones.map((o: any) => ({
                    texto_opcion: o.texto_opcion,
                    orden: o.orden
                }))
            }));
            setPreguntas(preguntasMapeadas.sort((a, b) => a.orden - b.orden));

        } catch (error) {
            console.error("Error cargando encuesta:", error);
            toast.error("No se pudo cargar la encuesta");
            navigate('/encuestas');
        } finally {
            setCargandoDatos(false);
        }
    };

    const guardarDatos = async (data: FormularioEncuesta, silencioso = false) => {
        if (!silencioso) setErrorValidacion(false);

        // Validaciones
        const inicio = new Date(data.fecha_inicio);
        const fin = new Date(data.fecha_fin);
        const ahora = new Date();
        ahora.setMinutes(ahora.getMinutes() - 1);

        if (esNuevo && inicio < ahora) {
            if (!silencioso) toast.error("Fecha de inicio no puede ser anterior a la actual.");
            return;
        }
        if (fin <= inicio) {
            if (!silencioso) toast.error("Fecha fin debe ser posterior a fecha inicio.");
            return;
        }

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
                reglas: [{
                    publico_objetivo: data.publico_objetivo,
                    filtros_json: data.filtros_json
                }],
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
                        filas: p.filas,
                        columnas: p.columnas,
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
                setEstado(res.data.estado);
            }
        } catch (error: any) {
            console.error(error);
            if (!silencioso) {
                toast.error(error.response?.data?.detail || "Error al guardar la encuesta");
            }
        }
    };

    // --- ACCIONES DE UI ---

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

    const accionesPregunta = {
        agregar: (pregunta: PreguntaFrontend, crearOtra: boolean) => {
            if (preguntaEditando && preguntas.some(p => p.id_temporal === pregunta.id_temporal)) {
                setPreguntas(prev => prev.map(p => p.id_temporal === pregunta.id_temporal ? pregunta : p));
            } else {
                const nuevaConOrden = { ...pregunta, orden: preguntas.length + 1 };
                setPreguntas(prev => [...prev, nuevaConOrden]);
            }
            if (!crearOtra) setModalAbierto(false);
            else setPreguntaEditando(null);
        },
        borrar: (id_temporal: number | string) => {
            if (!esEditable) return;
            if (window.confirm("¿Estás seguro de borrar este elemento?")) {
                const id = Number(id_temporal);
                const nuevas = preguntas.filter(p => Number(p.id_temporal) !== id);
                setPreguntas(nuevas.map((p, index) => ({ ...p, orden: index + 1 })));
            }
        },
        reordenar: (result: DropResult) => {
            if (!result.destination || !esEditable) return;
            const items = Array.from(preguntas);
            const [reorderedItem] = items.splice(result.source.index, 1);
            items.splice(result.destination.index, 0, reorderedItem);
            setPreguntas(items.map((item, index) => ({ ...item, orden: index + 1 })));
        },
        abrirNueva: () => {
            if (!esEditable) return;
            setPreguntaEditando(null);
            setModalAbierto(true);
        },
        abrirNuevaSeccion: () => {
            if (!esEditable) return;
            setPreguntaEditando({
                id_temporal: Date.now(),
                texto_pregunta: '',
                tipo: 'seccion',
                orden: 0,
                obligatoria: false,
                opciones: []
            });
            setModalAbierto(true);
        },
        editar: (p: PreguntaFrontend) => {
            if (!esEditable) return;
            setPreguntaEditando(p);
            setModalAbierto(true);
        }
    };

    return {
        // Estado
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
        cargandoUsuarios,
        // Preguntas
        preguntas,
        modalAbierto,
        setModalAbierto,
        preguntaEditando,
        setPreguntaEditando,
        // Acciones
        guardarDatos,
        cambiarEstadoEncuesta,
        accionesPregunta,
        idEncuesta,
        navigate,
        reset
    };
};
