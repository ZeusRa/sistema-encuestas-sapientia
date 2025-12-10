import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { Paper, Typography } from '@mui/material';
import { useReportesStore } from '../../context/useReportesStore';

// Colores modernos
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042', '#a4de6c', '#d0ed57'];

const GraficoDistribucion: React.FC = () => {
    const { distribucion } = useReportesStore();

    if (distribucion.length === 0) {
        return (
            <Paper elevation={2} sx={{ p: 4, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="text.secondary">No hay datos de distribución.</Typography>
            </Paper>
        );
    }

    // Necesitamos transformar los datos para Recharts
    // Entrada: { pregunta: "P1", opciones: { "Si": 20, "No": 80 } }
    // Salida:  { name: "P1", "Si": 20, "No": 80 }
    // Y necesitamos saber todas las posibles keys para crear las <Bar />

    // 1. Extraer todas las keys posibles de opciones
    const allOptions = new Set<string>();
    distribucion.forEach(d => {
        Object.keys(d.opciones).forEach(op => allOptions.add(op));
    });
    const keys = Array.from(allOptions);

    // 2. Transformar data
    const data = distribucion.map(d => ({
        name: d.pregunta.substring(0, 30) + (d.pregunta.length > 30 ? '...' : ''), // Acortar nombre
        full_name: d.pregunta,
        ...d.opciones
    }));

    return (
        <Paper elevation={2} sx={{ p: 2, borderRadius: 2, height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={data}
                    layout="vertical"
                    margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis
                        dataKey="name"
                        type="category"
                        width={90}
                        tick={{ fontSize: 11 }}
                    />
                    <Tooltip
                        contentStyle={{ borderRadius: 8 }}
                        formatter={(value: number) => [`${value}%`]}
                    />
                    <Legend />
                    {keys.map((key, index) => (
                        <Bar
                            key={key}
                            dataKey={key}
                            stackId="a"
                            fill={COLORS[index % COLORS.length]}
                        />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </Paper>
    );
};

export default GraficoDistribucion;
