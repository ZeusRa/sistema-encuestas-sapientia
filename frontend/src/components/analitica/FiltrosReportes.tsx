import React, { useEffect } from 'react';
import {
    Paper, Typography, FormControl, InputLabel, Select, MenuItem,
    Button, Stack, TextField, Autocomplete
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { useReportesStore } from '../../context/useReportesStore';

const FiltrosReportes: React.FC = () => {
    const {
        filtros, setFiltro, limpiarFiltros, loading,
        fetchEncuestas, encuestasDisponibles,
        fetchCatalogos, catalogs
    } = useReportesStore();

    useEffect(() => {
        fetchEncuestas();
        fetchCatalogos();
    }, [fetchEncuestas, fetchCatalogos]);

    const handleChange = (e: SelectChangeEvent<any> | React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFiltro(name as any, value);
    };

    return (
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom color="primary">
                Filtros Globales
            </Typography>
            <Stack spacing={2} sx={{ mt: 2 }}>

                <FormControl fullWidth size="small">
                    <InputLabel>Año</InputLabel>
                    <Select
                        name="anho"
                        value={filtros.anho}
                        label="Año"
                        onChange={handleChange}
                    >
                        <MenuItem value={2024}>2024</MenuItem>
                        <MenuItem value={2025}>2025</MenuItem>
                        <MenuItem value={2026}>2026</MenuItem>
                    </Select>
                </FormControl>

                <FormControl fullWidth size="small">
                    <InputLabel>Semestre</InputLabel>
                    <Select
                        name="semestre"
                        value={filtros.semestre}
                        label="Semestre"
                        onChange={handleChange}
                    >
                        <MenuItem value="">Todos</MenuItem>
                        <MenuItem value={1}>1er Semestre</MenuItem>
                        <MenuItem value={2}>2do Semestre</MenuItem>
                    </Select>
                </FormControl>

                <Autocomplete
                    options={encuestasDisponibles}
                    getOptionLabel={(option) => option.nombre}
                    value={encuestasDisponibles.find(e => e.nombre === filtros.nombre_encuesta) || null}
                    onChange={(_, newValue) => {
                        setFiltro('nombre_encuesta', newValue ? newValue.nombre : '');
                    }}
                    renderInput={(params) => (
                        <TextField
                            {...params}
                            label="Encuesta"
                            size="small"
                            placeholder="Buscar encuesta..."
                        />
                    )}
                />

                <Autocomplete
                    options={['Todos', ...catalogs.facultades]}
                    value={filtros.facultad}
                    onChange={(_, newValue) => setFiltro('facultad', newValue || 'Todos')}
                    renderInput={(params) => <TextField {...params} label="Facultad" size="small" />}
                />

                <Autocomplete
                    options={['Todos', ...catalogs.carreras]}
                    value={filtros.carrera}
                    onChange={(_, newValue) => setFiltro('carrera', newValue || 'Todos')}
                    renderInput={(params) => <TextField {...params} label="Carrera" size="small" />}
                />

                <TextField
                    name="docente"
                    label="Docente"
                    value={filtros.docente}
                    onChange={handleChange}
                    size="small"
                    placeholder="Nombre del docente"
                />

                <TextField
                    name="asignatura"
                    label="Asignatura"
                    value={filtros.asignatura}
                    onChange={handleChange}
                    size="small"
                    placeholder="Nombre o código"
                />

                <Button
                    variant="outlined"
                    color="secondary"
                    onClick={limpiarFiltros}
                    disabled={loading}
                >
                    Limpiar Filtros
                </Button>
            </Stack>
        </Paper>
    );
};

export default FiltrosReportes;
