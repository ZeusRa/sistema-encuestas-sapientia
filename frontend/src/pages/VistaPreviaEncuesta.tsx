
import { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box, Typography, Container, Paper, Button, MobileStepper, LinearProgress,
    FormControl, RadioGroup, FormControlLabel, Radio, TextField, FormGroup, Checkbox,
    Alert, CircularProgress, Divider
} from '@mui/material';
import KeyboardArrowLeft from '@mui/icons-material/KeyboardArrowLeft';
import KeyboardArrowRight from '@mui/icons-material/KeyboardArrowRight';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import api from '../api/axios';

// Interfaces simplificadas para el renderizado
interface Pregunta {
    id: number;
    texto: string;
    tipo: string;
    orden: number;
    opciones: { id: number; texto: string; orden: number }[];
    obligatoria: boolean;
    mensaje_error?: string;
    // Matriz
    filas?: { texto: string; orden: number }[];
    columnas?: { texto: string; orden: number }[];
    seleccion_multiple_matriz?: boolean;
}

interface Seccion {
    id_virtual: number; // Orden de la sección
    titulo: string;
    preguntas: Pregunta[];
}

interface EncuestaConfig {
    titulo: string;
    descripcion: string;
    paginacion: 'por_pregunta' | 'por_seccion' | 'todas';
    mostrar_progreso: 'porcentaje' | 'numero';
    permitir_saltar: boolean;
}

const VistaPreviaEncuesta = () => {
    const { id } = useParams();
    const [cargando, setCargando] = useState(true);
    const [config, setConfig] = useState<EncuestaConfig | null>(null);

    // Estado del motor
    const [paginas, setPaginas] = useState<Seccion[]>([]); // "Páginas" lógicas
    const [paginaActual, setPaginaActual] = useState(0);
    const [respuestas, setRespuestas] = useState<Record<number, any>>({}); // id_pregunta -> valor
    const [errores, setErrores] = useState<Record<number, string>>({}); // id_pregunta -> mensaje error
    const [completado, setCompletado] = useState(false);

    useEffect(() => {
        if (id) cargarEncuesta(Number(id));
    }, [id]);

    const cargarEncuesta = async (idEncuesta: number) => {
        try {
            const { data } = await api.get(`/admin/encuestas/${idEncuesta}`);

            // 1. Procesar Configuración
            const configuracion: EncuestaConfig = {
                titulo: data.nombre,
                descripcion: data.descripcion,
                paginacion: data.configuracion?.paginacion || 'por_pregunta',
                mostrar_progreso: data.configuracion?.mostrar_progreso || 'porcentaje',
                permitir_saltar: data.configuracion?.permitir_saltar ?? true
            };
            setConfig(configuracion);

            // 2. Procesar Preguntas y Estructura
            // Convertimos la lista plana de backend en estructura paginada según configuración
            const listaPreguntas = data.preguntas
                .sort((a: any, b: any) => a.orden - b.orden)
                .map((p: any) => ({
                    id: p.id,
                    texto: p.texto_pregunta,
                    tipo: p.tipo,
                    orden: p.orden,
                    opciones: p.opciones.sort((a: any, b: any) => a.orden - b.orden).map((o: any) => ({
                        id: o.id,
                        texto: o.texto_opcion,
                        orden: o.orden
                    })),
                    obligatoria: p.configuracion_json?.obligatoria || false,
                    mensaje_error: p.configuracion_json?.mensaje_error || 'Esta pregunta es obligatoria',
                    // Matriz
                    filas: p.configuracion_json?.filas || [],
                    columnas: p.configuracion_json?.columnas || [],
                    seleccion_multiple_matriz: p.configuracion_json?.seleccion_multiple_matriz || false
                }));

            let estructuraPaginada: Seccion[] = [];

            if (configuracion.paginacion === 'todas') {
                // Una sola página con todo
                estructuraPaginada.push({
                    id_virtual: 1,
                    titulo: '',
                    preguntas: listaPreguntas.filter((p: any) => p.tipo !== 'seccion')
                });
            } else if (configuracion.paginacion === 'por_seccion') {
                // Agrupar por secciones
                let seccionActual: Seccion = { id_virtual: 1, titulo: '', preguntas: [] };
                let contadorSecciones = 1;

                listaPreguntas.forEach((p: any) => {
                    if (p.tipo === 'seccion') {
                        // Si ya hay preguntas en la sección anterior, guardarla
                        if (seccionActual.preguntas.length > 0) {
                            estructuraPaginada.push(seccionActual);
                            contadorSecciones++;
                        }
                        // Iniciar nueva sección
                        seccionActual = { id_virtual: contadorSecciones, titulo: p.texto, preguntas: [] };
                    } else {
                        seccionActual.preguntas.push(p);
                    }
                });
                if (seccionActual.preguntas.length > 0) estructuraPaginada.push(seccionActual);

            } else { // 'por_pregunta'
                // Cada pregunta es una página (ignoramos las de tipo 'seccion' como separadores visuales, o las usamos como título de página)
                let tituloActual = '';
                let contadorPaginas = 1;

                listaPreguntas.forEach((p: any) => {
                    if (p.tipo === 'seccion') {
                        tituloActual = p.texto;
                    } else {
                        estructuraPaginada.push({
                            id_virtual: contadorPaginas++,
                            titulo: tituloActual,
                            preguntas: [p]
                        });
                    }
                });
            }

            setPaginas(estructuraPaginada);

        } catch (error) {
            console.error("Error cargando preview", error);
        } finally {
            setCargando(false);
        }
    };

    // --- LÓGICA DE RESPUESTA ---
    const handleRespuestaChange = (idPregunta: number, valor: any) => {
        setRespuestas(prev => ({ ...prev, [idPregunta]: valor }));
        // Limpiar error si existe
        if (errores[idPregunta]) {
            setErrores(prev => {
                const nuevos = { ...prev };
                delete nuevos[idPregunta];
                return nuevos;
            });
        }
    };

    // --- VALIDACIÓN ---
    const validarPaginaActual = () => {
        const pagina = paginas[paginaActual];
        const nuevosErrores: Record<number, string> = {};
        let esValido = true;

        pagina.preguntas.forEach(p => {
            if (p.obligatoria) {
                const valor = respuestas[p.id];
                // Validación simple: null, undefined, string vacío o array vacío
                if (valor === null || valor === undefined || valor === '' || (Array.isArray(valor) && valor.length === 0)) {
                    nuevosErrores[p.id] = p.mensaje_error || 'Campo requerido';
                    esValido = false;
                }
            }
        });

        setErrores(nuevosErrores);
        return esValido;
    };

    // --- NAVEGACIÓN Y ENVÍO ---
    const [enviando, setEnviando] = useState(false);

    // Función de envío real (QA Fix ID 06)
    const enviarRespuestas = async () => {
        setEnviando(true);
        try {
            // Transformar respuestas al formato del backend
            const listaRespuestas: any[] = [];

            // Aplanamos todas las preguntas de todas las páginas para buscar tipos
            const todalLasPreguntas = paginas.flatMap(s => s.preguntas);

            Object.entries(respuestas).forEach(([key, valor]) => {
                const idPregunta = Number(key);
                const pregunta = todalLasPreguntas.find(p => p.id === idPregunta);

                if (!pregunta) return;

                if (pregunta.tipo === 'texto_libre') {
                    listaRespuestas.push({ id_pregunta: idPregunta, valor_respuesta: String(valor) });
                } else if (pregunta.tipo === 'opcion_multiple') {
                    // Array de IDs
                    if (Array.isArray(valor)) {
                        valor.forEach(v => listaRespuestas.push({ id_pregunta: idPregunta, id_opcion: Number(v) }));
                    }
                } else if (pregunta.tipo === 'matriz') {
                    // Objeto { fila: col }
                    if (typeof valor === 'object' && valor) {
                        Object.entries(valor).forEach(([fila, col]) => {
                            // Simplificación para visualización: Guardamos como texto "Fila X: Col Y"
                            // Idealmente backend soportaría matriz nativa.
                            if (Array.isArray(col)) {
                                col.forEach(c => listaRespuestas.push({
                                    id_pregunta: idPregunta,
                                    valor_respuesta: `Fila ${fila} - Columna ${c}`
                                }));
                            } else {
                                listaRespuestas.push({
                                    id_pregunta: idPregunta,
                                    valor_respuesta: `Fila ${fila} - Columna ${col}`
                                });
                            }
                        });
                    }
                } else {
                    // Opcion unica / Radio (valor es ID)
                    listaRespuestas.push({ id_pregunta: idPregunta, id_opcion: Number(valor) });
                }
            });

            // Payload
            const payload = {
                id_usuario: 9999, // Simulación o Usuario Real si existe context
                id_encuesta: Number(id),
                id_referencia_contexto: `SIMULACION-PREVIEW-${Date.now()}`,
                metadatos_contexto: { mod: 'vista_previa' },
                respuestas: listaRespuestas
            };

            await api.post('/sapientia/recepcionar-respuestas', payload);
            setCompletado(true);

        } catch (error) {
            console.error("Error enviando encuesta:", error);
            // Si hay error de validación (Fix ID 07), se mostrará
            alert("Error al enviar respuestas. Revise que la encuesta esté activa y validada.");
        } finally {
            setEnviando(false);
        }
    };

    const handleSiguiente = () => {
        // Validar si no se permite saltar
        if (!config?.permitir_saltar) {
            if (!validarPaginaActual()) return;
        }

        if (paginaActual < paginas.length - 1) {
            setPaginaActual(prev => prev + 1);
            window.scrollTo(0, 0);
        } else {
            // Intento de envío final (siempre valida al final)
            if (validarPaginaActual()) {
                enviarRespuestas();
            }
        }
    };

    const handleAnterior = () => {
        if (paginaActual > 0) {
            setPaginaActual(prev => prev - 1);
            window.scrollTo(0, 0);
        }
    };

    // --- CÁLCULO PROGRESO ---
    const progreso = useMemo(() => {
        if (!paginas.length) return 0;

        // Total de preguntas reales (no secciones)
        const totalPreguntas = paginas.reduce((acc, p) => acc + p.preguntas.length, 0);
        if (totalPreguntas === 0) return 0;

        // Preguntas respondidas
        const respondidas = Object.keys(respuestas).length;
        // Ojo: esto cuenta keys, habría que verificar que pertenezcan a preguntas válidas si se borraran

        if (config?.mostrar_progreso === 'numero') {
            return `${respondidas} / ${totalPreguntas}`;
        } else {
            return Math.min(100, Math.round((respondidas / totalPreguntas) * 100));
        }
    }, [respuestas, paginas, config]);


    if (cargando) return <Box display="flex" justifyContent="center" height="100vh" alignItems="center"><CircularProgress /></Box>;
    if (completado) return (
        <Container maxWidth="sm" sx={{ mt: 8, textAlign: 'center' }}>
            <CheckCircleIcon color="success" sx={{ fontSize: 80, mb: 2 }} />
            <Typography variant="h4" gutterBottom>¡Gracias!</Typography>
            <Typography color="text.secondary">La simulación de la encuesta ha finalizado correctamente.</Typography>
            <Button variant="contained" sx={{ mt: 4 }} onClick={() => window.close()}>Cerrar Ventana</Button>
        </Container>
    );

    const seccionActual = paginas[paginaActual];

    return (
        <Box sx={{ bgcolor: '#f5f5f5', minHeight: '100vh', pb: 8 }}>
            {/* CABECERA */}
            <Paper elevation={0} sx={{ p: 3, mb: 3, borderBottom: '1px solid #ddd', borderRadius: 0 }}>
                <Container maxWidth="md">
                    <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                        {config?.titulo}
                    </Typography>
                    {config?.descripcion && (
                        <Typography variant="body1" color="text.secondary" paragraph>
                            {config.descripcion}
                        </Typography>
                    )}

                    <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Box sx={{ flexGrow: 1 }}>
                            {config?.mostrar_progreso === 'porcentaje' ? (
                                <Box display="flex" alignItems="center">
                                    <Box width="100%" mr={1}>
                                        <LinearProgress variant="determinate" value={progreso as number} sx={{ height: 10, borderRadius: 5 }} />
                                    </Box>
                                    <Box minWidth={35}>
                                        <Typography variant="body2" color="text.secondary">{`${progreso}%`}</Typography>
                                    </Box>
                                </Box>
                            ) : (
                                <Typography variant="body2" fontWeight="bold" color="primary">
                                    Preguntas contestadas: {progreso}
                                </Typography>
                            )}
                        </Box>
                    </Box>
                </Container>
            </Paper>

            {/* CUERPO FORMULARIO */}
            <Container maxWidth="md">
                {seccionActual.titulo && (
                    <Typography variant="h5" sx={{ mb: 2, fontWeight: 'medium' }}>
                        {seccionActual.titulo}
                    </Typography>
                )}

                {seccionActual.preguntas.map((pregunta) => (
                    <Paper key={pregunta.id} sx={{ p: 3, mb: 3, borderRadius: 2, borderLeft: errores[pregunta.id] ? '4px solid #d32f2f' : '4px solid transparent' }}>
                        <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                            {pregunta.texto} {pregunta.obligatoria && <span style={{ color: 'red' }}>*</span>}
                        </Typography>

                        <Box sx={{ mt: 2 }}>
                            {/* RENDERIZADO SEGÚN TIPO */}
                            {pregunta.tipo === 'texto_libre' && (
                                <TextField
                                    fullWidth
                                    multiline
                                    rows={3}
                                    placeholder="Escribe tu respuesta aquí..."
                                    value={respuestas[pregunta.id] || ''}
                                    onChange={(e) => handleRespuestaChange(pregunta.id, e.target.value)}
                                    error={!!errores[pregunta.id]}
                                />
                            )}

                            {pregunta.tipo === 'opcion_unica' && (
                                <FormControl error={!!errores[pregunta.id]}>
                                    <RadioGroup
                                        value={respuestas[pregunta.id] || ''}
                                        onChange={(e) => handleRespuestaChange(pregunta.id, e.target.value)}
                                    >
                                        {pregunta.opciones.map(op => (
                                            <FormControlLabel
                                                key={op.id}
                                                value={String(op.id)} // Guardamos ID como valor
                                                control={<Radio />}
                                                label={op.texto}
                                            />
                                        ))}
                                    </RadioGroup>
                                </FormControl>
                            )}

                            {pregunta.tipo === 'opcion_multiple' && (
                                <FormGroup>
                                    {pregunta.opciones.map(op => {
                                        const seleccionados = (respuestas[pregunta.id] || []) as string[];
                                        const isChecked = seleccionados.includes(String(op.id));
                                        return (
                                            <FormControlLabel
                                                key={op.id}
                                                control={
                                                    <Checkbox
                                                        checked={isChecked}
                                                        onChange={(e) => {
                                                            const val = String(op.id);
                                                            const nuevoArr = e.target.checked
                                                                ? [...seleccionados, val]
                                                                : seleccionados.filter(v => v !== val);
                                                            handleRespuestaChange(pregunta.id, nuevoArr);
                                                        }}
                                                    />
                                                }
                                                label={op.texto}
                                            />
                                        );
                                    })}
                                </FormGroup>
                            )}

                            {pregunta.tipo === 'matriz' && (
                                <Box sx={{ overflowX: 'auto' }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead>
                                            <tr>
                                                <th style={{ padding: 8 }}></th>
                                                {pregunta.columnas?.map((col, idx) => (
                                                    <th key={idx} style={{ padding: 8, textAlign: 'center', borderBottom: '1px solid #ddd' }}>
                                                        <Typography variant="body2" fontWeight="bold">{col.texto}</Typography>
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {pregunta.filas?.map((fila, idxFila) => (
                                                <tr key={idxFila} style={{ borderBottom: '1px solid #eee' }}>
                                                    <td style={{ padding: 8 }}>
                                                        <Typography variant="body2">{fila.texto}</Typography>
                                                    </td>
                                                    {pregunta.columnas?.map((col, idxCol) => {
                                                        const key = `${idxFila}-${idxCol}`; // Identificador celda (fila-col)
                                                        // Guardamos respuesta como objeto: { [filaIndex]: colIndex } o { [filaIndex]: [colIndex1, colIndex2] }
                                                        const respFila = respuestas[pregunta.id]?.[idxFila];

                                                        const isChecked = pregunta.seleccion_multiple_matriz
                                                            ? (Array.isArray(respFila) && respFila.includes(idxCol))
                                                            : respFila === idxCol;

                                                        return (
                                                            <td key={idxCol} style={{ padding: 8, textAlign: 'center' }}>
                                                                {pregunta.seleccion_multiple_matriz ? (
                                                                    <Checkbox
                                                                        checked={isChecked}
                                                                        onChange={(e) => {
                                                                            const current = (respuestas[pregunta.id] || {});
                                                                            const filaVals = current[idxFila] || [];
                                                                            const newFilaVals = e.target.checked
                                                                                ? [...filaVals, idxCol]
                                                                                : filaVals.filter((v: number) => v !== idxCol);

                                                                            handleRespuestaChange(pregunta.id, { ...current, [idxFila]: newFilaVals });
                                                                        }}
                                                                    />
                                                                ) : (
                                                                    <Radio
                                                                        checked={isChecked}
                                                                        onChange={() => {
                                                                            const current = (respuestas[pregunta.id] || {});
                                                                            handleRespuestaChange(pregunta.id, { ...current, [idxFila]: idxCol });
                                                                        }}
                                                                    />
                                                                )}
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </Box>
                            )}
                        </Box>

                        {/* Mensaje de Error */}
                        {errores[pregunta.id] && (
                            <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                                {errores[pregunta.id]}
                            </Typography>
                        )}
                    </Paper>
                ))}

                {/* FOOTER NAVEGACIÓN */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
                    <Button
                        variant="outlined"
                        onClick={handleAnterior}
                        disabled={paginaActual === 0 || enviando}
                        startIcon={<KeyboardArrowLeft />}
                    >
                        Anterior
                    </Button>

                    <Button
                        variant="contained"
                        onClick={handleSiguiente}
                        disabled={enviando}
                        endIcon={enviando ? <CircularProgress size={20} color="inherit" /> : (paginaActual === paginas.length - 1 ? <CheckCircleIcon /> : <KeyboardArrowRight />)}
                        color={paginaActual === paginas.length - 1 ? 'success' : 'primary'}
                    >
                        {paginaActual === paginas.length - 1 ? (enviando ? 'Enviando...' : 'Enviar Formulario') : 'Siguiente'}
                    </Button>
                </Box>
            </Container>
        </Box>
    );
};

export default VistaPreviaEncuesta;
