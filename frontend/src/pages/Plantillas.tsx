
import { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Button, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  List, ListItem, ListItemText, ListItemIcon, Tooltip
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import DragHandleIcon from '@mui/icons-material/DragHandle';
import { useForm, useFieldArray, type Control } from 'react-hook-form';
import api from '../api/axios';
import { toast } from 'react-toastify';
import { DragDropContext, Droppable, Draggable, type DropResult } from '@hello-pangea/dnd';

interface OpcionPlantilla {
    texto_opcion: string;
    orden: number;
}

interface Plantilla {
    id: number;
    nombre: string;
    descripcion: string;
    detalles: OpcionPlantilla[];
}

interface FormularioPlantilla {
    nombre: string;
    descripcion: string;
    detalles: OpcionPlantilla[];
}

const Plantillas = () => {
    const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [editandoId, setEditandoId] = useState<number | null>(null);

    const { register, control, handleSubmit, reset, setValue } = useForm<FormularioPlantilla>({
        defaultValues: { detalles: [] }
    });

    const { fields, append, remove, move } = useFieldArray({
        control,
        name: "detalles"
    });

    useEffect(() => {
        cargarPlantillas();
    }, []);

    const cargarPlantillas = async () => {
        try {
            const res = await api.get('/plantillas/');
            setPlantillas(res.data);
        } catch (error) {
            console.error(error);
        }
    };

    const handleAbrirNuevo = () => {
        setEditandoId(null);
        reset({ nombre: '', descripcion: '', detalles: [{ texto_opcion: '', orden: 1 }] });
        setModalOpen(true);
    };

    const handleEditar = (plantilla: Plantilla) => {
        setEditandoId(plantilla.id);
        reset({
            nombre: plantilla.nombre,
            descripcion: plantilla.descripcion,
            detalles: plantilla.detalles.sort((a, b) => a.orden - b.orden)
        });
        setModalOpen(true);
    };

    const handleEliminar = async (id: number) => {
        if (!confirm("¿Eliminar plantilla?")) return;
        try {
            await api.delete(`/plantillas/${id}`);
            cargarPlantillas();
            toast.success("Plantilla eliminada");
        } catch (error) {
            toast.error("Error al eliminar");
        }
    };

    const onGuardar = async (data: FormularioPlantilla) => {
        // Reasignar orden basado en índice actual
        const payload = {
            ...data,
            detalles: data.detalles.map((d, i) => ({ ...d, orden: i + 1 }))
        };

        try {
            if (editandoId) {
                await api.put(`/plantillas/${editandoId}`, payload);
                toast.success("Plantilla actualizada");
            } else {
                await api.post('/plantillas/', payload);
                toast.success("Plantilla creada");
            }
            setModalOpen(false);
            cargarPlantillas();
        } catch (error) {
            toast.error("Error al guardar");
        }
    };

    const onDragEnd = (result: DropResult) => {
        if (!result.destination) return;
        move(result.source.index, result.destination.index);
    };

    return (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" color="primary" fontWeight="bold">Plantillas de Opciones</Typography>
                <Button variant="contained" startIcon={<AddIcon />} onClick={handleAbrirNuevo}>
                    Nueva Plantilla
                </Button>
            </Box>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead sx={{ bgcolor: 'grey.100' }}>
                        <TableRow>
                            <TableCell>Nombre</TableCell>
                            <TableCell>Descripción</TableCell>
                            <TableCell align="center">Opciones</TableCell>
                            <TableCell align="center">Acciones</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {plantillas.map((p) => (
                            <TableRow key={p.id}>
                                <TableCell sx={{ fontWeight: 'bold' }}>{p.nombre}</TableCell>
                                <TableCell>{p.descripcion}</TableCell>
                                <TableCell align="center">{p.detalles.length}</TableCell>
                                <TableCell align="center">
                                    <IconButton onClick={() => handleEditar(p)} color="primary"><EditIcon /></IconButton>
                                    <IconButton onClick={() => handleEliminar(p.id)} color="error"><DeleteIcon /></IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* MODAL CREAR/EDITAR */}
            <Dialog open={modalOpen} onClose={() => setModalOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>{editandoId ? "Editar Plantilla" : "Nueva Plantilla"}</DialogTitle>
                <form onSubmit={handleSubmit(onGuardar)}>
                    <DialogContent>
                        <TextField
                            autoFocus // UX Requirement
                            margin="dense"
                            label="Nombre de la Plantilla"
                            fullWidth
                            {...register("nombre", { required: true })}
                        />
                        <TextField
                            margin="dense"
                            label="Descripción"
                            fullWidth
                            multiline
                            rows={2}
                            {...register("descripcion")}
                        />

                        <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>Opciones de Respuesta</Typography>
                        <DragDropContext onDragEnd={onDragEnd}>
                            <Droppable droppableId="lista-opciones-plantilla">
                                {(provided) => (
                                    <List dense {...provided.droppableProps} ref={provided.innerRef}>
                                        {fields.map((field, index) => (
                                            <Draggable key={field.id} draggableId={field.id} index={index}>
                                                {(provided) => (
                                                    <ListItem
                                                        ref={provided.innerRef}
                                                        {...provided.draggableProps}
                                                        secondaryAction={
                                                            <IconButton edge="end" onClick={() => remove(index)}>
                                                                <DeleteIcon fontSize="small" />
                                                            </IconButton>
                                                        }
                                                    >
                                                        <ListItemIcon {...provided.dragHandleProps} sx={{ cursor: 'grab' }}>
                                                            <DragHandleIcon />
                                                        </ListItemIcon>
                                                        <TextField
                                                            fullWidth
                                                            size="small"
                                                            placeholder={`Opción ${index + 1}`}
                                                            {...register(`detalles.${index}.texto_opcion` as const, { required: true })}
                                                        />
                                                    </ListItem>
                                                )}
                                            </Draggable>
                                        ))}
                                        {provided.placeholder}
                                    </List>
                                )}
                            </Droppable>
                        </DragDropContext>
                        <Button startIcon={<AddIcon />} onClick={() => append({ texto_opcion: '', orden: fields.length + 1 })}>
                            Agregar Opción
                        </Button>

                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setModalOpen(false)}>Cancelar</Button>
                        <Button type="submit" variant="contained">Guardar</Button>
                    </DialogActions>
                </form>
            </Dialog>
        </Box>
    );
};

export default Plantillas;
