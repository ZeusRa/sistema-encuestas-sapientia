import { create } from 'zustand';
import axios from 'axios';
import { usarAuthStore } from './authStore';

// Definición de tipos para los filtros y datos
interface FiltrosReporte {
    anho: number | '';
    semestre: 1 | 2 | '';
    campus: string;
    facultad: string;
    carrera: string;
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
    carrera: string;
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
}

interface Catalogs {
    facultades: string[];
    carreras: string[];
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
    downloadPdf: () => Promise<void>;
    limpiarFiltros: () => void;
}

// Valores iniciales
const filtrosIniciales: FiltrosReporte = {
    anho: new Date().getFullYear(),
    semestre: '',
    campus: 'Todos',
    facultad: 'Todos',
    carrera: 'Todos',
    docente: 'Todos',
    asignatura: 'Todos',
    nombre_encuesta: '',
};

// URL del backend (asumiendo proxy o variable de entorno, ajusta según tu config)
const API_URL = 'http://localhost:8000';

export const useReportesStore = create<ReportesState>((set, get) => ({
    filtros: { ...filtrosIniciales },
    tablaRespuestas: [],
    nubePalabras: [],
    distribucion: [],
    encuestasDisponibles: [],
    dashboardMetrics: null,
    catalogs: { facultades: [], carreras: [], sedes: [] },
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
            const res = await axios.get(`${API_URL}/reportes-avanzados/catalogos`, {
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
            const params: any = {};
            if (filtros.anho) params.anho = filtros.anho;
            // Filtrar por ID de encuesta si tenemos el nombre (frontend logic needed to map name->id or update filter to store ID)
            // Por ahora enviamos lo que tenemos

            // Fix: Store filter stores 'nombre_encuesta'. Backend expects 'encuesta_id' ideally.
            // We need to find the ID from the name in 'encuestasDisponibles'
            const encuesta = get().encuestasDisponibles.find(e => e.nombre === filtros.nombre_encuesta);
            if (encuesta) params.encuesta_id = encuesta.id;

            const res = await axios.get(`${API_URL}/reportes-avanzados/dashboard/kpis`, {
                headers: { Authorization: `Bearer ${token}` },
                params
            });
            set({ dashboardMetrics: res.data });
        } catch (err) {
            console.error("Error fetching KPIs", err);
        }
    },

    exportarCsv: async () => {
        const { filtros, encuestasDisponibles } = get();
        const token = usarAuthStore.getState().token;
        const encuesta = encuestasDisponibles.find(e => e.nombre === filtros.nombre_encuesta);

        if (!encuesta) {
            alert("Selecciona una encuesta para exportar.");
            return;
        }

        try {
            const response = await axios.get(`${API_URL}/reportes-avanzados/exportar/csv`, {
                headers: { Authorization: `Bearer ${token}` },
                params: { encuesta_id: encuesta.id },
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `respuestas_${encuesta.id}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Error exporting CSV", err);
        }
    },

    downloadPdf: async () => {
        const { filtros, encuestasDisponibles } = get();
        const token = usarAuthStore.getState().token;
        const encuesta = encuestasDisponibles.find(e => e.nombre === filtros.nombre_encuesta);

        if (!encuesta) {
            alert("Selecciona una encuesta para generar reporte.");
            return;
        }

        try {
            const response = await axios.get(`${API_URL}/reportes-avanzados/exportar/pdf`, {
                headers: { Authorization: `Bearer ${token}` },
                params: { encuesta_id: encuesta.id },
                responseType: 'blob',
            });

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `reporte_${encuesta.id}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (err) {
            console.error("Error generating PDF", err);
            alert("Error generando PDF. Verifica que el backend soporte WeasyPrint.");
        }
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
            if (filtros.carrera && filtros.carrera !== 'Todos') params.carrera = filtros.carrera;
            if (filtros.docente && filtros.docente !== 'Todos') params.docente = filtros.docente;
            if (filtros.asignatura && filtros.asignatura !== 'Todos') params.asignatura = filtros.asignatura;
            if (filtros.campus && filtros.campus !== 'Todos') params.campus = filtros.campus;
            if (filtros.facultad && filtros.facultad !== 'Todos') params.facultad = filtros.facultad;
            if (filtros.carrera && filtros.carrera !== 'Todos') params.carrera = filtros.carrera;
            if (filtros.docente && filtros.docente !== 'Todos') params.docente = filtros.docente;
            if (filtros.asignatura && filtros.asignatura !== 'Todos') params.asignatura = filtros.asignatura;
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
