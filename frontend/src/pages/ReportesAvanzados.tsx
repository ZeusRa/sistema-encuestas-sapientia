import React from 'react';
import { Box, Container, Grid, Typography, Divider } from '@mui/material';
import DashboardInsights from '../components/analitica/DashboardInsights';
import FiltrosReportes from '../components/analitica/FiltrosReportes';
import GraficoDistribucion from '../components/analitica/GraficoDistribucion';
import NubeDePalabras from '../components/analitica/NubeDePalabras';
import TablaRespuestas from '../components/analitica/TablaRespuestas';
import { Button } from '@mui/material';
import { useReportesStore } from '../context/useReportesStore';

const ReportesAvanzados: React.FC = () => {
    return (
        <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary">
                        Reportes Avanzados
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary">
                        Análisis detallado de encuestas, tendencias y distribución de respuestas.
                    </Typography>
                </Box>
                <Box>
                    <Button
                        variant="contained"
                        color="success"
                        onClick={() => useReportesStore.getState().exportarExcel()}
                        sx={{ ml: 2 }}
                    >
                        Exportar Excel
                    </Button>
                </Box>
            </Box>

            <Grid container spacing={3}>
                {/* Panel de Filtros (Izquierda en pantallas grandes) */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Box sx={{ position: 'sticky', top: 20 }}>
                        <FiltrosReportes />
                    </Box>
                </Grid>

                {/* Área Principal de Reportes */}
                <Grid size={{ xs: 12, md: 9 }}>

                    {/* 1. Insights / KPIs Principales */}
                    <DashboardInsights />

                    <Divider sx={{ my: 4 }} />

                    <Typography variant="h5" gutterBottom fontWeight="bold" color="primary.dark">
                        Análisis Detallado
                    </Typography>

                    <Grid container spacing={3}>
                        {/* Gráfico de Distribución */}
                        <Grid size={{ xs: 12, lg: 8 }}>
                            <Typography variant="h6" gutterBottom>
                                Distribución de Respuestas
                            </Typography>
                            <GraficoDistribucion />
                        </Grid>

                        {/* Nube de Palabras */}
                        <Grid size={{ xs: 12, lg: 4 }}>
                            <Typography variant="h6" gutterBottom>
                                Palabras Clave (Texto Abierto)
                            </Typography>
                            <NubeDePalabras />
                        </Grid>

                        {/* Tabla de Respuestas Detallada */}
                        <Grid size={{ xs: 12 }}>
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="h6" gutterBottom>
                                    Registro de Respuestas
                                </Typography>
                                <TablaRespuestas />
                            </Box>
                        </Grid>
                    </Grid>
                </Grid>
            </Grid>
        </Container>
    );
};

export default ReportesAvanzados;
