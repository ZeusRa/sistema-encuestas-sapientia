import React, { useEffect, useState } from 'react';
import {
    Grid, Paper, Typography, Box, CircularProgress,
    Card, CardContent, Divider
} from '@mui/material';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Cell
} from 'recharts';
import { useReportesStore } from '../../context/useReportesStore';
import SapientiaFilters from './SapientiaFilters';

// Componente de Gauge simple (o KPI grande con color)
const ScoreCard = ({ title, score, benchmark }: { title: string, score: number, benchmark: number }) => {
    const diff = score - benchmark;
    const color = score >= 3.5 ? '#4caf50' : score >= 3.0 ? '#ff9800' : '#f44336';

    return (
        <Card elevation={3} sx={{ height: '100%', textAlign: 'center', position: 'relative', overflow: 'visible' }}>
            <Box sx={{ position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)', bgcolor: color, color: 'white', px: 2, py: 0.5, borderRadius: 2, fontWeight: 'bold' }}>
                {title}
            </Box>
            <CardContent sx={{ pt: 4 }}>
                <Typography variant="h2" fontWeight="bold" sx={{ color }}>
                    {score ? score.toFixed(1) : '-'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    / 4.0
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="caption" display="block">
                    Promedio Facultad: <strong>{benchmark ? benchmark.toFixed(1) : '-'}</strong>
                </Typography>
                <Typography variant="caption" sx={{ color: diff >= 0 ? 'success.main' : 'error.main' }}>
                    {diff > 0 ? '+' : ''}{diff ? diff.toFixed(1) : '-'} vs Benchmark
                </Typography>
            </CardContent>
        </Card>
    );
};

const TeacherDashboard: React.FC = () => {
    const { filtros, encuestasDisponibles } = useReportesStore();

    const [iddData, setIddData] = useState<any>(null);
    const [radarData, setRadarData] = useState<any[]>([]);
    const [divergingData, setDivergingData] = useState<any[]>([]);
    const [limitationsData, setLimitationsData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);

    const token = localStorage.getItem('token_acceso');
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    useEffect(() => {
        const fetchData = async () => {
            const encuesta = encuestasDisponibles.find(e => e.nombre === filtros.nombre_encuesta);
            if (!encuesta) return;

            setLoading(true);
            try {
                const headers = { Authorization: `Bearer ${token}` };
                const queryParams = new URLSearchParams({ encuesta_id: String(encuesta.id) });

                if (filtros.campus && filtros.campus !== 'Todos') queryParams.append('campus', filtros.campus);
                if (filtros.facultad && filtros.facultad !== 'Todos') queryParams.append('facultad', filtros.facultad);
                if (filtros.departamento && filtros.departamento !== 'Todos') queryParams.append('departamento', filtros.departamento);
                if (filtros.docente && filtros.docente !== 'Todos') queryParams.append('docente', filtros.docente);
                if (filtros.asignatura && filtros.asignatura !== 'Todos') queryParams.append('asignatura', filtros.asignatura);
                if (filtros.anho) queryParams.append('anho', String(filtros.anho));
                if (filtros.semestre) queryParams.append('semestre', String(filtros.semestre));

                const queryString = queryParams.toString();

                const [iddRes, radarRes, divRes, limRes] = await Promise.all([
                    fetch(`${API_URL}/reportes-avanzados/dashboard/docente/idd?${queryString}`, { headers }).then(r => r.json()),
                    fetch(`${API_URL}/reportes-avanzados/dashboard/docente/radar?${queryString}`, { headers }).then(r => r.json()),
                    fetch(`${API_URL}/reportes-avanzados/dashboard/docente/divergencia?${queryString}`, { headers }).then(r => r.json()),
                    fetch(`${API_URL}/reportes-avanzados/dashboard/docente/limitantes?${queryString}`, { headers }).then(r => r.json())
                ]);

                setIddData(iddRes);
                setRadarData(radarRes);
                setDivergingData(divRes);
                setLimitationsData(limRes);

            } catch (error) {
                console.error("Error fetching teacher dashboard data", error);
            } finally {
                setLoading(false);
            }
        };

        if (filtros.nombre_encuesta) {
            fetchData();
        }
    }, [filtros, encuestasDisponibles]);

    if (!filtros.nombre_encuesta) return (
        <Box>
            <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold', color: '#1565c0' }}>
                Tablero de Desempeño Docente
            </Typography>
            <SapientiaFilters />
            <Typography sx={{ mt: 2 }}>Seleccione una encuesta para ver el reporte docente.</Typography>
        </Box>
    );

    return (
        <Box>
            <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold', color: '#1565c0' }}>
                Tablero de Desempeño Docente
            </Typography>

            <SapientiaFilters />

            {loading && <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}><CircularProgress /></Box>}

            {(!loading && iddData) && (
                <>
                    <Grid container spacing={3} sx={{ mb: 4 }}>
                        <Grid size={{ xs: 12, md: 4, lg: 3 }}>
                            <ScoreCard title="IDD Global" score={iddData.idd_score} benchmark={iddData.benchmark_score} />
                        </Grid>
                        <Grid size={{ xs: 12, md: 4, lg: 3 }}>
                            <Card elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                                <Typography variant="h6" color="text.secondary">Tasa de Respuesta</Typography>
                                <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                                    <CircularProgress variant="determinate" value={iddData.tasa_respuesta || 0} size={80} thickness={4} />
                                    <Box
                                        sx={{
                                            top: 0,
                                            left: 0,
                                            bottom: 0,
                                            right: 0,
                                            position: 'absolute',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                        }}
                                    >
                                        <Typography variant="caption" component="div" color="text.secondary">
                                            {`${Math.round(iddData.tasa_respuesta || 0)}%`}
                                        </Typography>
                                    </Box>
                                </Box>
                            </Card>
                        </Grid>
                        <Grid size={{ xs: 12, md: 8, lg: 6 }}>
                            <Paper elevation={2} sx={{ p: 2, height: '100%' }}>
                                <Typography variant="subtitle1" gutterBottom>Análisis Dimensional (vs Facultad)</Typography>
                                <ResponsiveContainer width="100%" height={250}>
                                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                                        <PolarGrid />
                                        <PolarAngleAxis dataKey="subject" />
                                        <PolarRadiusAxis angle={30} domain={[0, 4]} />
                                        <Radar name="Docente" dataKey="A" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                                        <Radar name="Facultad" dataKey="B" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
                                        <Legend />
                                        <Tooltip />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </Paper>
                        </Grid>
                    </Grid>

                    <Grid container spacing={3}>
                        <Grid size={{ xs: 12, lg: 8 }}>
                            <Paper elevation={2} sx={{ p: 3 }}>
                                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                                    Sentimiento por Pregunta (Negativo vs Positivo)
                                </Typography>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart
                                        layout="vertical"
                                        data={divergingData}
                                        stackOffset="sign"
                                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" hide />
                                        <YAxis dataKey="pregunta" type="category" width={150} tick={{ fontSize: 12 }} />
                                        <Tooltip />
                                        <ReferenceLine x={0} stroke="#000" />
                                        <Bar dataKey="negativo" fill="#f44336" stackId="stack" name="Negativo" />
                                        <Bar dataKey="positivo" fill="#4caf50" stackId="stack" name="Positivo" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Paper>
                        </Grid>

                        <Grid size={{ xs: 12, lg: 4 }}>
                            <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
                                <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                                    Top Limitantes Reportadas
                                </Typography>
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart
                                        layout="vertical"
                                        data={limitationsData}
                                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" />
                                        <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
                                        <Tooltip />
                                        <Bar dataKey="value" fill="#ff9800">
                                            {limitationsData.map((entry: any, index: number) => (
                                                <Cell key={`cell-${index}`} fill={index === 0 ? '#d32f2f' : '#ff9800'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </Paper>
                        </Grid>
                    </Grid>
                </>
            )}
        </Box>
    );
};

export default TeacherDashboard;
