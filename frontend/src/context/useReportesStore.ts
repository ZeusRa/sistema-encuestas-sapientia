import { create } from 'zustand';
import axios from 'axios';
import { usarAuthStore } from './authStore';

// Definición de tipos para los filtros y datos
interface FiltrosReporte {
    anho: number | '';
    semestre: 1 | 2 | '';
    campus: string;
    facultad: string;
    departamento: string;
    docente: string;
    asignatura: string;
    nombre_encuesta: string;
}

interface ReporteTablaItem {
    id_hecho: number;
    fecha: string;
    texto_pregunta: string;
    nombre_encuesta: string;
    respuesta_texto: string;
    facultad: string;
    carrera: string; // Maintain legacy name for now or update if backend sends departamento
    asignatura: string;
}

interface ReporteNubeItem {
    text: string;
    value: number;
}

interface ReporteDistribucionItem {
    pregunta: string;
    opciones: { [key: string]: number }; // "Opción A": 25.5
}

interface EncuestaResumen {
    id: number;
    nombre: string;
    estado: string;
}

interface DashboardMetrics {
    avance_global_pct: number;
    total_asignaciones: number;
    asignaciones_realizadas: number;
    asignaciones_pendientes: number;
    encuestas_activas: number;
}

interface Catalogs {
    facultades: string[];
    departamentos: string[];
    docentes: string[];
    sedes: string[];
}

interface ReportesState {
    filtros: FiltrosReporte;

    // Datos
    tablaRespuestas: ReporteTablaItem[];
    nubePalabras: ReporteNubeItem[];
    distribucion: ReporteDistribucionItem[];
    encuestasDisponibles: EncuestaResumen[];

    // Nuevo: Dashboard y Catalogos
    dashboardMetrics: DashboardMetrics | null;
    catalogs: Catalogs;

    loading: boolean;
    error: string | null;

    // Acciones
    setFiltro: (key: keyof FiltrosReporte, value: string | number) => void;
    fetchReportes: () => Promise<void>;
    fetchEncuestas: () => Promise<void>;
    fetchCatalogos: () => Promise<void>;
    fetchDashboardMetrics: () => Promise<void>;
    exportarCsv: () => Promise<void>;
    exportarExcel: () => Promise<void>;
    downloadPdf: () => Promise<void>;
    limpiarFiltros: () => void;
}

// Valores iniciales
const filtrosIniciales: FiltrosReporte = {
    anho: new Date().getFullYear(),
    semestre: '',
    campus: 'Todos',
    facultad: 'Todos',
    departamento: 'Todos',
    docente: 'Todos',
    asignatura: 'Todos',
    nombre_encuesta: '',
};

// URL del backend - usar variable de entorno
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useReportesStore = create<ReportesState>((set, get) => ({
    filtros: { ...filtrosIniciales },
    tablaRespuestas: [],
    nubePalabras: [],
    distribucion: [],
    encuestasDisponibles: [],
    dashboardMetrics: null,
    catalogs: { facultades: [], departamentos: [], sedes: [], docentes: [] },
    loading: false,
    error: null,

    setFiltro: (key, value) => {
        set((state) => ({
            filtros: { ...state.filtros, [key]: value }
        }));
        // Si cambiamos un filtro, recargamos reportes y dashboard
        //get().fetchReportes(); // Debouncing ideal here, but manual trigger is better or use effect in component
    },

    limpiarFiltros: () => {
        set({ filtros: { ...filtrosIniciales } });
        get().fetchReportes();
    },

    fetchEncuestas: async () => {
        const token = usarAuthStore.getState().token;
        if (!token) return;

        try {
            const config = {
                headers: { Authorization: `Bearer ${token}` },
                params: {
                    estados: ['publicado', 'en_curso', 'finalizado']
                },
                paramsSerializer: {
                    indexes: null
                }
            };

            const res = await axios.get(`${API_URL}/admin/encuestas/`, config);
            set({ encuestasDisponibles: res.data });

        } catch (err) {
            console.error("Error cargando encuestas para filtro:", err);
        }
    },

    fetchCatalogos: async () => {
        const token = usarAuthStore.getState().token;
        if (!token) return;
        try {
            const res = await axios.get(`${API_URL}/reportes/catalogos`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            set({ catalogs: res.data });
        } catch (err) {
            console.error("Error fetching catalogs", err);
        }
    },

    fetchDashboardMetrics: async () => {
        const { filtros } = get();
        const token = usarAuthStore.getState().token;
        if (!token) return;

        try {
            const res = await axios.get(`${API_URL}/reportes-avanzados/dashboard/kpis`, {
                headers: { Authorization: `Bearer ${token}` },
                params: {
                    encuesta_id: filtros.nombre_encuesta ? undefined : undefined, // Simplificación: Dashboard global o refinar filtro ID
                    anho: filtros.anho,
                    semestre: filtros.semestre
                }
            });

            set({
                dashboardMetrics: {
                    avance_global_pct: res.data.avance_global_pct,
                    total_asignaciones: res.data.total_asignaciones,
                    asignaciones_realizadas: res.data.asignaciones_realizadas,
                    asignaciones_pendientes: res.data.asignaciones_pendientes,
                    encuestas_activas: res.data.encuestas_activas
                }
            });
        } catch (err) {
            console.error("Error fetching KPIs", err);
        }
    },

    exportarCsv: async () => {
        // Alias for exportExcel logic basically
        await get().exportarExcel();
    },

    exportarExcel: async () => {
        const { filtros, encuestasDisponibles } = get();
        const token = usarAuthStore.getState().token;

        // Intentar buscar ID por nombre o usar filtro directo si backend lo soportara
        const encuesta = encuestasDisponibles.find(e => e.nombre === filtros.nombre_encuesta);

        if (!encuesta) {
            alert("Selecciona una encuesta para exportar.");
            return;
        }

        try {
            const response = await axios.get(`${API_URL}/reportes/exportar/excel`, {
                headers: { Authorization: `Bearer ${token}` },
                params: { encuesta_id: encuesta.id },
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `reporte_encuesta_${encuesta.id}.xlsx`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Error exporting Excel", err);
            alert("Error al descargar Excel.");
        }
    },

    downloadPdf: async () => {
        // ... feature pending or remove ...
        alert("Funcionalidad PDF pendiente de implementación en backend.");
    },

    fetchReportes: async () => {
        const { filtros } = get();
        set({ loading: true, error: null });

        // Trigger KPIs refresh parallel
        get().fetchDashboardMetrics();

        try {
            const params: Record<string, string | number> = {};

            if (filtros.anho) params.anho = filtros.anho;
            if (filtros.semestre) params.semestre = filtros.semestre;
            if (filtros.facultad && filtros.facultad !== 'Todos') params.facultad = filtros.facultad;
            // Rename to departamento
            if (filtros.departamento && filtros.departamento !== 'Todos') params.departamento = filtros.departamento;
            if (filtros.docente && filtros.docente !== 'Todos') params.docente = filtros.docente;
            if (filtros.asignatura && filtros.asignatura !== 'Todos') params.asignatura = filtros.asignatura;
            if (filtros.campus && filtros.campus !== 'Todos') params.campus = filtros.campus;
            if (filtros.nombre_encuesta) params.nombre_encuesta = filtros.nombre_encuesta;

            const token = usarAuthStore.getState().token;

            if (!token) {
                set({ error: "No hay sesión activa.", loading: false });
                return;
            }

            const config = {
                headers: { Authorization: `Bearer ${token}` },
                params
            };

            const [resTabla, resNube, resDist] = await Promise.all([
                axios.get(`${API_URL}/reportes/respuestas-tabla`, config),
                axios.get(`${API_URL}/reportes/analisis-texto`, config),
                axios.get(`${API_URL}/reportes/distribucion-respuestas`, config)
            ]);

            set({
                tablaRespuestas: resTabla.data,
                nubePalabras: resNube.data,
                distribucion: resDist.data,
                loading: false
            });

        } catch (err: unknown) {
            console.error("Error cargando reportes:", err);
            set({
                loading: false,
                error: (err as any)?.response?.data?.detail || "Error cargando datos."
            });
        }
    }
}));
