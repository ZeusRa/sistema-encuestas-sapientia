import React, { useEffect } from 'react';
import { Grid, Paper, Typography, Box, CircularProgress, Card, CardContent } from '@mui/material';
import { useReportesStore } from '../../context/useReportesStore';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const DashboardInsights: React.FC = () => {
    const { dashboardMetrics, fetchDashboardMetrics, loading } = useReportesStore();

    useEffect(() => {
        fetchDashboardMetrics();
    }, [fetchDashboardMetrics]);

    if (loading && !dashboardMetrics) {
        return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }

    if (!dashboardMetrics) {
        return (
            <Typography color="text.secondary" align="center">
                Selecciona una encuesta y filtros para ver los insights.
            </Typography>
        );
    }

    const avanceData = [
        { name: 'Realizadas', value: dashboardMetrics.asignaciones_realizadas },
        { name: 'Pendientes', value: dashboardMetrics.asignaciones_pendientes },
    ];

    // Colores: Verde (Exito) para realizadas, Rojo/Naranja para pendientes
    const COLORS = ['#4caf50', '#ff9800'];

    return (
        <Box sx={{ mb: 4 }}>
            <Typography variant="h5" gutterBottom color="primary.dark" fontWeight="bold">
                Resumen Ejecutivo
            </Typography>

            <Grid container spacing={3}>
                {/* KPI: Encuestas Activas */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Card elevation={2} sx={{ height: '100%', borderTop: '4px solid #2196f3' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Encuestas en Curso
                            </Typography>
                            <Typography variant="h3" color="primary">
                                {dashboardMetrics.encuestas_activas}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Activas actualmente
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* KPI: Avance Global */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Card elevation={2} sx={{
                        height: '100%',
                        borderTop: dashboardMetrics.avance_global_pct > 80 ? '4px solid #4caf50'
                            : dashboardMetrics.avance_global_pct < 50 ? '4px solid #f44336' : '4px solid #ff9800'
                    }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Avance Global
                            </Typography>
                            <Typography variant="h3">
                                {dashboardMetrics.avance_global_pct}%
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                {dashboardMetrics.asignaciones_realizadas} de {dashboardMetrics.total_asignaciones} asignaciones
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* KPI: Pendientes */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Card elevation={2} sx={{ borderTop: '4px solid #f44336', height: '100%' }}>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                Pendientes
                            </Typography>
                            <Typography variant="h3" color="error">
                                {dashboardMetrics.asignaciones_pendientes}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                                Usuarios aún por responder
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Gráfico de Participación */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Paper elevation={2} sx={{ p: 2, height: '100%', minHeight: 200, display: 'flex', flexDirection: 'column' }}>
                        <Typography variant="subtitle1" gutterBottom align="center">Participación</Typography>
                        <Box sx={{ flexGrow: 1, minHeight: 150 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={avanceData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={30}
                                        outerRadius={50}
                                        fill="#8884d8"
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {avanceData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                    <Legend verticalAlign="bottom" height={36} />
                                </PieChart>
                            </ResponsiveContainer>
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default DashboardInsights;
