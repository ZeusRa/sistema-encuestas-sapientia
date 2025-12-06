
import { useState, useEffect } from 'react';
import {
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
    Paper, IconButton, Select, MenuItem, FormControl, InputLabel,
    Autocomplete, TextField, Chip, Box, Typography
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import api from '../api/axios';

export interface ReglaRestriccion {
    id: number;
    campo: string;
    regla: 'es' | 'no es' | 'contiene' | 'no contiene';
    valores: string[]; // Siempre array, si es single solo usa el [0]
}

interface Props {
    reglas: ReglaRestriccion[];
    onChange: (nuevasReglas: ReglaRestriccion[]) => void;
}

const CAMPOS = [
    { value: 'campus', label: 'Campus' },
    { value: 'facultad', label: 'Facultad' },
    { value: 'departamento', label: 'Departamento' },
    { value: 'carrera', label: 'Carrera' },
    { value: 'asignatura', label: 'Asignatura' },
    { value: 'docente', label: 'Docente' }
];

const REGLAS = [
    { value: 'es', label: 'es', multiple: false },
    { value: 'no es', label: 'no es', multiple: false },
    { value: 'contiene', label: 'contiene', multiple: true },
    { value: 'no contiene', label: 'no contiene', multiple: true }
];

const ConstructorReglas = ({ reglas, onChange }: Props) => {
    // Cache de opciones para no recargar siempre
    const [opcionesCache, setOpcionesCache] = useState<Record<string, string[]>>({});
    const [cargandoCampo, setCargandoCampo] = useState<string | null>(null);

    const cargarOpciones = async (campo: string) => {
        if (opcionesCache[campo]) return;

        setCargandoCampo(campo);
        try {
            const res = await api.get(`/sapientia/catalogos/${campo}`);
            setOpcionesCache(prev => ({ ...prev, [campo]: res.data }));
        } catch (error) {
            console.error(`Error cargando catalogo ${campo}`, error);
        } finally {
            setCargandoCampo(null);
        }
    };

    const handleAddRow = () => {
        const nueva: ReglaRestriccion = {
            id: Date.now(),
            campo: 'campus',
            regla: 'es',
            valores: []
        };
        onChange([...reglas, nueva]);
        // Cargar opciones por defecto del nuevo campo
        cargarOpciones('campus');
    };

    const handleDeleteRow = (id: number) => {
        onChange(reglas.filter(r => r.id !== id));
    };

    const handleChangeRow = (id: number, field: keyof ReglaRestriccion, value: any) => {
        const nuevas = reglas.map(r => {
            if (r.id === id) {
                const updated = { ...r, [field]: value };

                // Resetear valores si cambia el campo
                if (field === 'campo') {
                    updated.valores = [];
                    // Cargar opciones del nuevo campo
                    cargarOpciones(value as string);
                }

                // Validar consistencia regla-valores si cambia regla
                if (field === 'regla') {
                    const esMultiple = REGLAS.find(x => x.value === value)?.multiple;
                    if (!esMultiple && updated.valores.length > 1) {
                        updated.valores = [updated.valores[0]]; // Quedarse solo con el primero
                    }
                }

                return updated;
            }
            return r;
        });
        onChange(nuevas);
    };

    // Cargar opciones iniciales para filas existentes
    useEffect(() => {
        reglas.forEach(r => cargarOpciones(r.campo));
    }, []);

    return (
        <TableContainer component={Paper} variant="outlined">
            <Table size="small">
                <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                    <TableRow>
                        <TableCell width="20%"><strong>Campo</strong></TableCell>
                        <TableCell width="20%"><strong>Regla</strong></TableCell>
                        <TableCell width="50%"><strong>Valor</strong></TableCell>
                        <TableCell width="10%" align="center">
                            <IconButton color="success" onClick={handleAddRow} size="small">
                                <AddCircleOutlineIcon />
                            </IconButton>
                        </TableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {reglas.length === 0 && (
                        <TableRow>
                            <TableCell colSpan={4} align="center" sx={{ color: 'text.secondary', fontStyle: 'italic', py: 2 }}>
                                No hay reglas definidas. Haz clic en (+) para añadir una restricción.
                            </TableCell>
                        </TableRow>
                    )}
                    {reglas.map((fila) => {
                        const esMultiple = REGLAS.find(r => r.value === fila.regla)?.multiple;
                        const listaOpciones = opcionesCache[fila.campo] || [];
                        const cargando = cargandoCampo === fila.campo;

                        return (
                            <TableRow key={fila.id}>
                                <TableCell>
                                    <FormControl fullWidth size="small" variant="standard">
                                        <Select
                                            value={fila.campo}
                                            onChange={(e) => handleChangeRow(fila.id, 'campo', e.target.value)}
                                            disableUnderline
                                        >
                                            {CAMPOS.map(opt => (
                                                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </TableCell>
                                <TableCell>
                                    <FormControl fullWidth size="small" variant="standard">
                                        <Select
                                            value={fila.regla}
                                            onChange={(e) => handleChangeRow(fila.id, 'regla', e.target.value)}
                                            disableUnderline
                                        >
                                            {REGLAS.map(opt => (
                                                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                                            ))}
                                        </Select>
                                    </FormControl>
                                </TableCell>
                                <TableCell>
                                    <Autocomplete
                                        multiple={esMultiple}
                                        options={listaOpciones}
                                        loading={cargando}
                                        value={esMultiple ? fila.valores : (fila.valores[0] || null)}
                                        onChange={(_, newValue) => {
                                            const val = esMultiple
                                                ? (newValue as string[])
                                                : (newValue ? [newValue as string] : []);
                                            handleChangeRow(fila.id, 'valores', val);
                                        }}
                                        renderTags={(value: readonly string[], getTagProps) =>
                                            value.map((option: string, index: number) => {
                                                const { key, ...tagProps } = getTagProps({ index });
                                                return (
                                                    <Chip variant="outlined" label={option} size="small" key={key} {...tagProps} />
                                                );
                                            })
                                        }
                                        renderInput={(params) => (
                                            <TextField
                                                {...params}
                                                variant="standard"
                                                placeholder={cargando ? "Cargando..." : "Seleccionar..."}
                                            />
                                        )}
                                        sx={{ minWidth: 150 }}
                                    />
                                </TableCell>
                                <TableCell align="center">
                                    <IconButton color="error" onClick={() => handleDeleteRow(fila.id)} size="small">
                                        <DeleteIcon fontSize="small" />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        );
                    })}
                </TableBody>
            </Table>
        </TableContainer>
    );
};

export default ConstructorReglas;
