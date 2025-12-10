import React from 'react';
// Re-trigger TS

import { Paper, Box, Typography, Chip } from '@mui/material';
import { useReportesStore } from '../../context/useReportesStore';

const NubeDePalabras: React.FC = () => {
    const { nubePalabras } = useReportesStore();

    if (nubePalabras.length === 0) {
        return (
            <Paper elevation={2} sx={{ p: 4, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="text.secondary">No hay suficientes datos de texto.</Typography>
            </Paper>
        );
    }

    // Normalizar tamaños
    const maxVal = Math.max(...nubePalabras.map(n => n.value));

    return (
        <Paper elevation={2} sx={{ p: 2, borderRadius: 2, minHeight: 300 }}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
                {nubePalabras.map((item) => {
                    // Cálculo simple de tamaño relativo
                    const size = 0.8 + (item.value / maxVal) * 1.5; // Entre 0.8rem y 2.3rem
                    const opacity = 0.5 + (item.value / maxVal) * 0.5;

                    return (
                        <Chip
                            key={item.text}
                            label={`${item.text} (${item.value})`}
                            sx={{
                                fontSize: `${size}rem`,
                                height: 'auto',
                                py: 1,
                                opacity: opacity,
                                fontWeight: item.value > (maxVal / 2) ? 'bold' : 'normal',
                                color: item.value > (maxVal / 2) ? 'primary.main' : 'text.primary',
                                border: 'none',
                                bgcolor: 'transparent'
                            }}
                        />
                    );
                })}
            </Box>
        </Paper>
    );
};

export default NubeDePalabras;
