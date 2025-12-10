import React from 'react';
import {
    Paper, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, Typography, CircularProgress, Box
} from '@mui/material';
import { useReportesStore } from '../../context/useReportesStore';

const TablaRespuestas: React.FC = () => {
    const { tablaRespuestas, loading } = useReportesStore();

    if (loading && tablaRespuestas.length === 0) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (tablaRespuestas.length === 0) {
        return (
            <Typography variant="body1" color="text.secondary" align="center" sx={{ p: 4 }}>
                No hay datos disponibles con los filtros actuales.
            </Typography>
        );
    }

    return (
        <TableContainer component={Paper} elevation={2} sx={{ borderRadius: 2, maxHeight: 400 }}>
            <Table stickyHeader size="small">
                <TableHead>
                    <TableRow>
                        <TableCell>Fecha</TableCell>
                        <TableCell>Facultad</TableCell>
                        <TableCell>Carrera</TableCell>
                        <TableCell>Asignatura</TableCell>
                        <TableCell>Encuesta</TableCell>
                        <TableCell>Pregunta</TableCell>
                        <TableCell>Respuesta</TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {tablaRespuestas.map((row) => (
                        <TableRow key={row.id_hecho} hover>
                            <TableCell>{row.fecha}</TableCell>
                            <TableCell>{row.facultad}</TableCell>
                            <TableCell>{row.carrera}</TableCell>
                            <TableCell>{row.asignatura || '-'}</TableCell>
                            <TableCell>{row.nombre_encuesta}</TableCell>
                            <TableCell sx={{ maxWidth: 300, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {row.texto_pregunta}
                            </TableCell>
                            <TableCell sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                {row.respuesta_texto}
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

export default TablaRespuestas;
