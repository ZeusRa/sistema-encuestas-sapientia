import React, { useMemo } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useReportesStore } from '../../context/useReportesStore';

// Estilos para simular hoja A4 en pantalla
const a4Style: React.CSSProperties = {
    width: '210mm',
    minHeight: '297mm',
    padding: '20mm',
    margin: '10mm auto',
    backgroundColor: 'white',
    boxShadow: '0 0 10px rgba(0,0,0,0.1)',
    overflow: 'hidden',
    pageBreakAfter: 'always',
    fontFamily: 'Times New Roman, serif' // Más formal para reportes
};

const ReportePreview: React.FC = () => {
    const { tablaRespuestas, filtros } = useReportesStore();

    // Agrupación: Facultad -> Carrera -> Docente -> Asignatura
    // Esto es complejo de hacer en frontend con una lista plana si faltan datos, pero intentaremos.

    const agrupado = useMemo(() => {
        const groups: Record<string, Record<string, Record<string, any[]>>> = {};

        tablaRespuestas.forEach(row => {
            const fac = row.facultad || 'Sin Facultad';
            const car = row.carrera || 'Sin Carrera';
            const doc = row.nombre_encuesta; // Usando nombre encuesta como agrupación final temporal (o asignatura)
            // Nota: La tablaRespuestas actual tiene campos limitados. Asumimos que tiene lo basico.

            if (!groups[fac]) groups[fac] = {};
            if (!groups[fac][car]) groups[fac][car] = {};
            if (!groups[fac][car][doc]) groups[fac][car][doc] = [];

            groups[fac][car][doc].push(row);
        });
        return groups;
    }, [tablaRespuestas]);

    // Renderizar solo la primera facultad/carrera para demo si es muy grande, 
    // o paginar visualmente (1 pagina = 1 facultad?)
    // Por ahora renderizamos todo en un flujo continuo con saltos de pagina CSS.

    return (
        <Box sx={{ backgroundColor: '#525659', p: 4, height: '100%', overflow: 'auto' }}>
            <Typography variant="h6" sx={{ color: 'white', mb: 2, textAlign: 'center' }}>
                Vista Previa de Impresión (Estilo A4)
            </Typography>

            {Object.entries(agrupado).map(([facultad, carreras]) => (
                <div key={facultad} style={a4Style} className="page-a4">
                    {/* Encabezado */}
                    <Box sx={{ borderBottom: '2px solid #000', mb: 4, pb: 2, display: 'flex', justifyContent: 'space-between' }}>
                        <div>
                            <Typography variant="h5" fontWeight="bold">SAPIENTIA</Typography>
                            <Typography variant="subtitle2">Reporte de Evaluación Docente</Typography>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <Typography variant="body2">Semestre: {filtros.semestre || 'Todos'} - {filtros.anho}</Typography>
                            <Typography variant="body2">{facultad}</Typography>
                            <Typography variant="caption">{new Date().toLocaleDateString()}</Typography>
                        </div>
                    </Box>

                    {Object.entries(carreras).map(([carrera, docentes]) => (
                        <Box key={carrera} sx={{ mb: 4 }}>
                            <Typography variant="h6" sx={{ backgroundColor: '#f0f0f0', p: 1, mb: 2, borderLeft: '4px solid #1976d2' }}>
                                Departamento: {carrera}
                            </Typography>

                            {Object.entries(docentes).map(([docente, respuestas]) => (
                                <Box key={docente} sx={{ ml: 2, mb: 3 }}>
                                    <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>
                                        {docente}
                                    </Typography>

                                    <Table size="small" sx={{ mb: 2 }}>
                                        <TableHead>
                                            <TableRow>
                                                <TableCell><strong>Pregunta</strong></TableCell>
                                                <TableCell align="right"><strong>Respuesta</strong></TableCell>
                                            </TableRow>
                                        </TableHead>
                                        <TableBody>
                                            {respuestas.slice(0, 10).map((resp) => (
                                                <TableRow key={resp.id_hecho}>
                                                    <TableCell>{resp.texto_pregunta}</TableCell>
                                                    <TableCell align="right">{resp.respuesta_texto}</TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                    {respuestas.length > 10 && (
                                        <Typography variant="caption" display="block" align="center" fontStyle="italic">
                                            ... y {respuestas.length - 10} respuestas más ...
                                        </Typography>
                                    )}
                                </Box>
                            ))}
                        </Box>
                    ))}

                    {/* Pie de Pagina */}
                    <Box sx={{ position: 'absolute', bottom: '20mm', left: '20mm', right: '20mm', borderTop: '1px solid #ccc', pt: 1, textAlign: 'center' }}>
                        <Typography variant="caption">Generado por Sistema Sapientia - Página 1</Typography>
                    </Box>
                </div>
            ))}
        </Box>
    );
};

export default ReportePreview;
