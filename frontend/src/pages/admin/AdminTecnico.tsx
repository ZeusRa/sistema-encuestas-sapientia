import { useState, useEffect } from 'react';
import {
    Box, Typography, Paper, Tabs, Tab, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, Chip, Button, TextField,
    Grid, LinearProgress, IconButton, Tooltip, Dialog, DialogContent, DialogTitle,
    FormControlLabel, Checkbox
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DataObjectIcon from '@mui/icons-material/DataObject';
import api from '../../api/axios';
import { toast } from 'react-toastify';

interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
}

function CustomTabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;

    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            {...other}
        >
            {value === index && (
                <Box sx={{ p: 3 }}>
                    {children}
                </Box>
            )}
        </div>
    );
}

const AdminTecnico = () => {
    const [value, setValue] = useState(0);

    const handleChange = (_: React.SyntheticEvent, newValue: number) => {
        setValue(newValue);
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom fontWeight="bold" color="primary">
                Panel Técnico
            </Typography>
            <Paper sx={{ width: '100%', mb: 2 }}>
                <Tabs value={value} onChange={handleChange} indicatorColor="secondary" textColor="inherit">
                    <Tab label="Encuestas" />
                    <Tab label="Asignados" />
                    <Tab label="ETL / OLAP" />
                    <Tab label="Playground / Simulación" />
                </Tabs>

                <CustomTabPanel value={value} index={0}>
                    <TablaEncuestas />
                </CustomTabPanel>
                <CustomTabPanel value={value} index={1}>
                    <TablaAsignaciones />
                </CustomTabPanel>
                <CustomTabPanel value={value} index={2}>
                    <PanelETL />
                </CustomTabPanel>
                <CustomTabPanel value={value} index={3}>
                    <PlaygroundSimulacion />
                </CustomTabPanel>
            </Paper>
        </Box>
    );
};

// --- SUBCOMPONENTES ---

const TablaEncuestas = () => {
    const [encuestas, setEncuestas] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [jsonOpen, setJsonOpen] = useState(false);
    const [previewData, setPreviewData] = useState<any>(null);

    const cargarEncuestas = async () => {
        setLoading(true);
        try {
            const res = await api.get('/admin/tecnico/encuestas');
            setEncuestas(res.data);
        } catch (error) {
            toast.error("Error cargando encuestas");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        cargarEncuestas();
    }, []);

    const verPreview = async (id: number) => {
        try {
            const res = await api.get(`/admin/tecnico/encuestas/${id}/preview`);
            setPreviewData(res.data);
            setJsonOpen(true);
        } catch (error) {
            toast.error("Error cargando preview");
        }
    }

    return (
        <>
            <Box display="flex" justifyContent="flex-end" mb={2}>
                <Button
                    startIcon={<RefreshIcon />}
                    onClick={cargarEncuestas}
                    disabled={loading}
                >
                    Recargar
                </Button>
            </Box>
            <TableContainer>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>Nombre</TableCell>
                            <TableCell>Estado</TableCell>
                            <TableCell># Preguntas</TableCell>
                            <TableCell># Asignados</TableCell>
                            <TableCell>Acciones</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {encuestas.map((row) => (
                            <TableRow key={row.id}>
                                <TableCell>{row.id}</TableCell>
                                <TableCell>{row.nombre}</TableCell>
                                <TableCell>
                                    <Chip label={row.estado} size="small" color={row.estado === 'publicado' || row.estado === 'en_curso' ? 'success' : 'default'} />
                                </TableCell>
                                <TableCell>{row.preguntas}</TableCell>
                                <TableCell>{row.asignaciones}</TableCell>
                                <TableCell>
                                    <Tooltip title="Ver Estructura JSON">
                                        <IconButton size="small" onClick={() => verPreview(row.id)}>
                                            <DataObjectIcon />
                                        </IconButton>
                                    </Tooltip>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            <Dialog open={jsonOpen} onClose={() => setJsonOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>Estructura de Encuesta (JSON)</DialogTitle>
                <DialogContent>
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5', maxHeight: '60vh', overflow: 'auto' }}>
                        <pre>{JSON.stringify(previewData, null, 2)}</pre>
                    </Paper>
                </DialogContent>
            </Dialog>
        </>
    );
}

const TablaAsignaciones = () => {
    const [asignaciones, setAsignaciones] = useState<any[]>([]);

    const cargar = async () => {
        try {
            const res = await api.get('/admin/tecnico/asignaciones');
            setAsignaciones(res.data);
        } catch (error) {
            toast.error("Error cargando asignaciones");
        }
    };

    useEffect(() => { cargar() }, []);

    return (
        <>
            <Box display="flex" justifyContent="flex-end" mb={2}>
                <Button startIcon={<RefreshIcon />} onClick={cargar}>Recargar</Button>
            </Box>
            <TableContainer>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>ID Asignación</TableCell>
                            <TableCell>ID Usuario</TableCell>
                            <TableCell>ID Encuesta</TableCell>
                            <TableCell>Contexto</TableCell>
                            <TableCell>Estado</TableCell>
                            <TableCell>Fecha</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {asignaciones.map((row) => (
                            <TableRow key={row.id}>
                                <TableCell>{row.id}</TableCell>
                                <TableCell>{row.id_usuario}</TableCell>
                                <TableCell>{row.id_encuesta}</TableCell>
                                <TableCell>{row.id_referencia_contexto || 'N/A'}</TableCell>
                                <TableCell>
                                    <Chip label={row.estado} color={row.estado === 'realizada' ? 'success' : row.estado === 'pendiente' ? 'warning' : 'default'} size="small" />
                                </TableCell>
                                <TableCell>{new Date(row.fecha_asignacion).toLocaleString()}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </>
    )
}

const PanelETL = () => {
    const [estado, setEstado] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const cargarEstado = async () => {
        try {
            const res = await api.get('/admin/tecnico/etl/estado');
            setEstado(res.data);
        } catch { }
    };

    useEffect(() => { cargarEstado() }, []);

    const ejecutarETL = async () => {
        setLoading(true);
        try {
            await api.post('/admin/tecnico/etl/ejecutar');
            toast.success("Proceso ETL Ejecutado");
            cargarEstado();
        } catch (e) {
            toast.error("Fallo al ejecutar ETL");
        } finally {
            setLoading(false);
        }
    }

    return (
        <Box textAlign="center" py={4}>
            <Typography variant="h6">Estado del Warehouse (OLAP)</Typography>
            <Box display="flex" justifyContent="center" gap={4} my={4}>
                <Paper sx={{ p: 3, minWidth: 200, bgcolor: '#e3f2fd' }}>
                    <Typography variant="h3" color="primary">
                        {estado?.pendientes_etl ?? '-'}
                    </Typography>
                    <Typography variant="subtitle1">Transacciones Pendientes</Typography>
                </Paper>
                <Paper sx={{ p: 3, minWidth: 200 }}>
                    <Typography variant="h3">
                        {estado?.total_transacciones ?? '-'}
                    </Typography>
                    <Typography variant="subtitle1">Total Histórico</Typography>
                </Paper>
            </Box>

            <Button
                variant="contained"
                size="large"
                color="secondary"
                onClick={ejecutarETL}
                disabled={loading}
                startIcon={!loading && <PlayArrowIcon />}
            >
                {loading ? "Ejecutando ETL..." : "Ejecutar ETL Manualmente"}
            </Button>
            {loading && <LinearProgress sx={{ mt: 2, maxWidth: 400, mx: 'auto' }} />}
        </Box>
    )
}

const PlaygroundSimulacion = () => {
    const [idEncuesta, setIdEncuesta] = useState("");
    const [activeSurveys, setActiveSurveys] = useState<any[]>([]); // New state for surveys
    const [idUsuario, setIdUsuario] = useState("");
    const [crearSiNoExiste, setCrearSiNoExiste] = useState(true);
    const [escenario, setEscenario] = useState("alumno_2_completo");
    const [logs, setLogs] = useState<{ id: number, text: string }[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Fetch active surveys for the dropdown
        api.get('/admin/tecnico/encuestas').then(res => {
            const activos = res.data.filter((e: any) => e.estado === 'en_curso');
            setActiveSurveys(activos);
        }).catch(err => toast.error("Error cargando encuestas activas"));
    }, []);

    // Estado para chequeo sapientia
    const [chkAlumno, setChkAlumno] = useState("");
    const [chkResultado, setChkResultado] = useState<any>(null);

    const simular = async () => {
        if (!idEncuesta || !idUsuario) return toast.warning("Complete todos los campos");

        setLoading(true);
        setLogs([{ id: Date.now(), text: "Iniciando solicitud..." }]);

        try {
            const res = await api.post('/admin/tecnico/simulacion', {
                id_encuesta: parseInt(idEncuesta),
                id_usuario: parseInt(idUsuario),
                crear_asignacion: crearSiNoExiste,
                escenario: escenario
            });

            if (res.data.exito) {
                toast.success("Simulación Exitosa");
            } else {
                toast.error("Simulación con errores");
            }
            setLogs(prev => [
                ...prev,
                ...res.data.logs.map((l: string, idx: number) => ({ id: Date.now() + idx, text: l }))
            ]);
        } catch (error: any) {
            toast.error("Error en la simulación");
            setLogs(prev => [
                ...prev,
                { id: Date.now(), text: "ERROR HTTP: " + (error.response?.data?.detail || error.message) }
            ]);
        } finally {
            setLoading(false);
        }
    };

    const verificarPendientes = async () => {
        if (!chkAlumno) return;
        try {
            const res = await api.get(`/admin/tecnico/chequeo-sapientia/${chkAlumno}`);
            setChkResultado(res.data);
            toast.info("Consulta realizada");
        } catch (error) {
            toast.error("Error consultando sapientia");
        }
    }

    return (
        <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 5 }}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h6" gutterBottom>Configuración de Simulacro</Typography>
                    <TextField
                        select
                        label="Encuesta (En Curso)"
                        fullWidth
                        margin="normal"
                        value={idEncuesta}
                        onChange={(e) => setIdEncuesta(e.target.value)}
                        SelectProps={{ native: true }}
                        helperText="Seleccione una encuesta activa"
                    >
                        <option value="">-- Seleccione --</option>
                        {activeSurveys.map((s) => (
                            <option key={s.id} value={s.id}>
                                #{s.id} - {s.nombre}
                            </option>
                        ))}
                    </TextField>
                    <TextField
                        label="ID Usuario (Alumno)"
                        fullWidth
                        type="number"
                        margin="normal"
                        value={idUsuario}
                        onChange={(e) => setIdUsuario(e.target.value)}
                        helperText="ID del usuario que responderá"
                    />

                    <FormControlLabel
                        control={
                            <Checkbox
                                checked={crearSiNoExiste}
                                onChange={(e) => setCrearSiNoExiste(e.target.checked)}
                            />
                        }
                        label="Crear asignación si no existe"
                    />

                    <Box mt={2}>
                        <TextField
                            select
                            label="Escenario de Simulación"
                            fullWidth
                            SelectProps={{ native: true }}
                            value={escenario}
                            onChange={(e) => setEscenario(e.target.value)}
                            helperText="Define el comportamiento del alumno simulado"
                        >
                            <option value="alumno_1_borrador">Alumno 1: Inicia, guarda borrador y sale</option>
                            <option value="alumno_2_completo">Alumno 2: Inicia y completa (Happy Path)</option>
                            <option value="alumno_3_flujo_completo">Alumno 3: Borrador -&gt; Abandona -&gt; Retoma -&gt; Completa</option>
                        </TextField>
                    </Box>

                    <Box mt={3}>
                        <Button
                            variant="contained"
                            fullWidth
                            size="large"
                            onClick={simular}
                            disabled={loading}
                        >
                            {loading ? "Simulando..." : "Iniciar Simulación"}
                        </Button>
                    </Box>

                    <Box mt={4} pt={2} borderTop={1} borderColor="divider">
                        <Typography variant="h6" gutterBottom>Chequeo API Sapientia</Typography>
                        <Box display="flex" gap={2}>
                            <TextField
                                label="ID Alumno"
                                size="small"
                                value={chkAlumno}
                                onChange={(e) => setChkAlumno(e.target.value)}
                            />
                            <Button variant="outlined" onClick={verificarPendientes}>Consultar</Button>
                        </Box>
                        {chkResultado && (
                            <Paper variant="outlined" sx={{ p: 1, mt: 1, bgcolor: '#e0f7fa' }}>
                                <Typography variant="body2" fontWeight="bold">Bloqueo: {chkResultado.estado_bloqueo ? "SÍ" : "NO"}</Typography>
                                <Typography variant="caption">{chkResultado.mensaje}</Typography>
                            </Paper>
                        )}
                    </Box>
                </Paper>
            </Grid>
            <Grid size={{ xs: 12, md: 7 }}>
                <Paper sx={{ p: 2, bgcolor: '#212121', color: '#00e676', fontFamily: 'monospace', minHeight: 300, maxHeight: 500, overflow: 'auto' }}>
                    <Typography variant="subtitle2" sx={{ color: '#bdbdbd', mb: 1 }}>Console Output &gt;_</Typography>
                    {logs.map((log) => (
                        <div key={log.id}>$ {log.text}</div>
                    ))}
                    {logs.length === 0 && <span style={{ opacity: 0.5 }}>Esperando ejecución...</span>}
                </Paper>
            </Grid>
        </Grid>
    )
}

export default AdminTecnico;
