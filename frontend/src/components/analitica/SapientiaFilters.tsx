import React, { useEffect, useState } from 'react';
import {
    Grid, Paper, Typography, Box, Autocomplete, TextField, Button
} from '@mui/material';
import FilterAltOffIcon from '@mui/icons-material/FilterAltOff';
import { useReportesStore } from '../../context/useReportesStore';
import api from '../../api/axios';

const SapientiaFilters: React.FC = () => {
    const { filtros, setFiltro, limpiarFiltros } = useReportesStore();

    // Estados locales para las opciones de los filtros
    const [opcionesCampus, setOpcionesCampus] = useState<string[]>([]);
    const [opcionesFacultad, setOpcionesFacultad] = useState<string[]>([]);
    const [opcionesDepartamento, setOpcionesDepartamento] = useState<string[]>([]);
    const [opcionesDocente, setOpcionesDocente] = useState<string[]>([]);
    const [opcionesAsignatura, setOpcionesAsignatura] = useState<{ codigo: string, nombre: string, seccion: string }[]>([]);

    // Cargar Campuses (Root level)
    useEffect(() => {
        const fetchCampus = async () => {
            try {
                const res = await api.get('/sapientia/campus');
                setOpcionesCampus(res.data);
            } catch (err) {
                console.error("Error cargando campus", err);
            }
        };
        fetchCampus();
    }, []);

    // Cargar Facultades (Depende de Campus)
    useEffect(() => {
        const fetchFacultades = async () => {
            try {
                const params = filtros.campus !== 'Todos' ? { campus: filtros.campus } : {};
                const res = await api.get('/sapientia/facultades', { params });
                setOpcionesFacultad(res.data);
            } catch (err) {
                console.error("Error cargando facultades", err);
            }
        };
        fetchFacultades();
    }, [filtros.campus]);

    // Cargar Departamentos (Depende de Campus, Facultad)
    useEffect(() => {
        const fetchDepartamentos = async () => {
            try {
                const params: any = {};
                if (filtros.campus !== 'Todos') params.campus = filtros.campus;
                if (filtros.facultad !== 'Todos') params.facultad = filtros.facultad;

                const res = await api.get('/sapientia/departamentos', { params });
                setOpcionesDepartamento(res.data);
            } catch (err) {
                console.error("Error cargando departamentos", err);
            }
        };
        fetchDepartamentos();
    }, [filtros.campus, filtros.facultad]);

    // Cargar Docentes (Depende de todo lo anterior)
    useEffect(() => {
        const fetchDocentes = async () => {
            try {
                const params: any = {};
                if (filtros.campus !== 'Todos') params.campus = filtros.campus;
                if (filtros.facultad !== 'Todos') params.facultad = filtros.facultad;
                if (filtros.departamento !== 'Todos') params.departamento = filtros.departamento;

                const res = await api.get('/sapientia/docentes', { params });
                setOpcionesDocente(res.data);
            } catch (err) {
                console.error("Error cargando docentes", err);
            }
        };
        fetchDocentes();
    }, [filtros.campus, filtros.facultad, filtros.departamento]);

    // Cargar Asignaturas (Depende de todo)
    useEffect(() => {
        const fetchAsignaturas = async () => {
            try {
                const params: any = {};
                if (filtros.campus !== 'Todos') params.campus = filtros.campus;
                if (filtros.facultad !== 'Todos') params.facultad = filtros.facultad;
                if (filtros.departamento !== 'Todos') params.departamento = filtros.departamento;
                if (filtros.docente !== 'Todos') params.docente = filtros.docente;

                const res = await api.get('/sapientia/asignaturas', { params });
                setOpcionesAsignatura(res.data);
            } catch (err) {
                console.error("Error cargando asignaturas", err);
            }
        };
        fetchAsignaturas();
    }, [filtros.campus, filtros.facultad, filtros.departamento, filtros.docente]);


    const handleFilterChange = (key: any, value: any) => {
        if (key === 'campus') {
            setFiltro('facultad', 'Todos');
            setFiltro('departamento', 'Todos');
            setFiltro('docente', 'Todos');
            setFiltro('asignatura', 'Todos');
        } else if (key === 'facultad') {
            setFiltro('departamento', 'Todos');
            setFiltro('docente', 'Todos');
            setFiltro('asignatura', 'Todos');
        } else if (key === 'departamento') {
            setFiltro('docente', 'Todos');
            setFiltro('asignatura', 'Todos');
        }

        setFiltro(key, value || 'Todos');
    };

    return (
        <Paper elevation={3} sx={{ p: 3, mb: 3, borderLeft: '5px solid #1976d2' }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight="bold" color="primary">
                    Filtros Globales (Sapientia)
                </Typography>
                <Button
                    variant="outlined"
                    color="secondary"
                    size="small"
                    startIcon={<FilterAltOffIcon />}
                    onClick={limpiarFiltros}
                >
                    Limpiar
                </Button>
            </Box>

            <Grid container spacing={2}>
                {/* CAMPUS */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Autocomplete
                        options={opcionesCampus}
                        value={filtros.campus !== 'Todos' ? filtros.campus : null}
                        onChange={(_, newValue) => handleFilterChange('campus', newValue)}
                        renderInput={(params) => <TextField {...params} label="Campus" variant="outlined" size="small" />}
                        noOptionsText="Sin opciones"
                    />
                </Grid>

                {/* FACULTAD */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Autocomplete
                        options={opcionesFacultad}
                        value={filtros.facultad !== 'Todos' ? filtros.facultad : null}
                        onChange={(_, newValue) => handleFilterChange('facultad', newValue)}
                        renderInput={(params) => <TextField {...params} label="Facultad" variant="outlined" size="small" />}
                        disabled={opcionesFacultad.length === 0}
                        noOptionsText="Sin opciones"
                    />
                </Grid>

                {/* DEPARTAMENTO */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Autocomplete
                        options={opcionesDepartamento}
                        value={filtros.departamento !== 'Todos' ? filtros.departamento : null}
                        onChange={(_, newValue) => handleFilterChange('departamento', newValue)}
                        renderInput={(params) => <TextField {...params} label="Departamento" variant="outlined" size="small" />}
                        disabled={opcionesDepartamento.length === 0}
                        noOptionsText="Sin opciones"
                    />
                </Grid>

                {/* DOCENTE */}
                <Grid size={{ xs: 12, md: 3 }}>
                    <Autocomplete
                        options={opcionesDocente}
                        value={filtros.docente !== 'Todos' ? filtros.docente : null}
                        onChange={(_, newValue) => handleFilterChange('docente', newValue)}
                        renderInput={(params) => <TextField {...params} label="Docente" variant="outlined" size="small" />}
                        disabled={opcionesDocente.length === 0}
                        noOptionsText="Sin opciones"
                    />
                </Grid>

                {/* ASIGNATURA */}
                <Grid size={{ xs: 12, md: 6 }}>
                    <Autocomplete
                        options={opcionesAsignatura}
                        getOptionLabel={(option) => typeof option === 'string' ? option : `${option.nombre} (Sec. ${option.seccion})`}
                        value={filtros.asignatura !== 'Todos' ? (opcionesAsignatura.find(a => a.nombre === filtros.asignatura) || null) : null}
                        onChange={(_, newValue: any) => handleFilterChange('asignatura', newValue?.nombre || 'Todos')}
                        renderInput={(params) => <TextField {...params} label="Asignatura" variant="outlined" size="small" />}
                        disabled={opcionesAsignatura.length === 0}
                        noOptionsText="Sin opciones"
                    />
                </Grid>

                {/* AÑO Y SEMESTRE (MANUAL) */}
                <Grid size={{ xs: 6, md: 3 }}>
                    <TextField
                        label="Año"
                        type="number"
                        fullWidth
                        size="small"
                        value={filtros.anho}
                        onChange={(e) => setFiltro('anho', parseInt(e.target.value) || '')}
                    />
                </Grid>
                <Grid size={{ xs: 6, md: 3 }}>
                    <Autocomplete
                        options={[1, 2]}
                        value={filtros.semestre || null}
                        onChange={(_, newValue) => setFiltro('semestre', newValue || '')}
                        renderInput={(params) => <TextField {...params} label="Semestre" variant="outlined" size="small" />}
                    />
                </Grid>

            </Grid>
        </Paper>
    );
};

export default SapientiaFilters;
