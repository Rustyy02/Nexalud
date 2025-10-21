// frontend/src/components/DetallePaciente.jsx - VERSIÓN CORREGIDA COMPLETA
import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Grid,
    Card,
    CardContent,
    Typography,
    Button,
    Chip,
    Paper,
    Avatar,
    Divider,
    CircularProgress,
    Alert,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    List,
    ListItem,
    ListItemText,
} from '@mui/material';
import {
    Person as PersonIcon,
    Phone as PhoneIcon,
    Home as HomeIcon,
    Security as SecurityIcon,
    MedicalServices as MedicalIcon,
    History as HistoryIcon,
    Warning as WarningIcon,
    CheckCircle as CheckCircleIcon,
    Schedule as ScheduleIcon,
    ArrowForward as ArrowForwardIcon,
    ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { pacientesService, rutasClinicasService } from '../services/api';
import Navbar from './Navbar';

const DetallePaciente = () => {
    const { id } = useParams();
    const navigate = useNavigate();

    // Estados principales
    const [paciente, setPaciente] = useState(null);
    const [rutaClinica, setRutaClinica] = useState(null);
    const [historial, setHistorial] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Estados de diálogos
    const [dialogObservaciones, setDialogObservaciones] = useState(false);
    const [dialogHistorial, setDialogHistorial] = useState(false);
    const [observaciones, setObservaciones] = useState('');
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        cargarDatos();
        const interval = setInterval(cargarDatos, 30000);
        return () => clearInterval(interval);
    }, [id]);

    const cargarDatos = async () => {
        try {
            setError('');
            setLoading(true);

            const pacienteRes = await pacientesService.getById(id);
            setPaciente(pacienteRes.data);

            const rutasRes = await pacientesService.getRutasClinicas(id);

            if (rutasRes.data && rutasRes.data.length > 0) {
                const rutaActual = rutasRes.data[0];
                const timelineRes = await rutasClinicasService.getTimeline(rutaActual.id);
                setRutaClinica(timelineRes.data);

                const historialRes = await rutasClinicasService.getHistorial(rutaActual.id);
                setHistorial(historialRes.data.historial || []);
            }

            setLoading(false);
        } catch (err) {
            setError('Error al cargar los datos del paciente');
            setLoading(false);
            console.error(err);
        }
    };

    const handleAvanzarEtapa = () => {
        setDialogObservaciones(true);
    };

    const handleAvanzarConObservaciones = async () => {
        if (!rutaClinica || !rutaClinica.ruta_clinica) return;

        try {
            setActionLoading(true);
            await rutasClinicasService.avanzar(
                rutaClinica.ruta_clinica.id,
                { observaciones }
            );
            setDialogObservaciones(false);
            setObservaciones('');
            await cargarDatos();
        } catch (err) {
            setError(err.response?.data?.mensaje || 'Error al avanzar la etapa');
            console.error(err);
        } finally {
            setActionLoading(false);
        }
    };

    const handleRetrocederEtapa = async () => {
        if (!rutaClinica || !rutaClinica.ruta_clinica) return;

        try {
            setActionLoading(true);
            await rutasClinicasService.retroceder(rutaClinica.ruta_clinica.id);
            await cargarDatos();
        } catch (err) {
            setError(err.response?.data?.mensaje || 'Error al retroceder la etapa');
            console.error(err);
        } finally {
            setActionLoading(false);
        }
    };

    const getColorUrgencia = (urgencia) => {
        const colores = {
            'CRITICA': 'error',
            'ALTA': 'warning',
            'MEDIA': 'info',
            'BAJA': 'success',
        };
        return colores[urgencia] || 'default';
    };

    const obtenerDatosPaciente = (paciente) => {
        const metadatos = paciente.metadatos_adicionales || {};

        return {
            nombre: metadatos.nombre || `Paciente ${paciente.identificador_hash.substring(0, 8)}`,
            rut: metadatos.rut_original || paciente.identificador_hash.substring(0, 12),
            edad: paciente.edad,
            tipoSangre: metadatos.tipo_sangre || paciente.tipo_sangre || 'O+',
            contacto: metadatos.contacto || '+56 9 7846 1789',
            direccion: metadatos.direccion || 'Sin dirección registrada',
            seguro: metadatos.seguro || 'Sin seguro',
            alergias: paciente.alergias || metadatos.alergias || 'Sin alergias registradas',
            condiciones: paciente.condiciones_preexistentes || metadatos.condiciones || 'Sin condiciones',
            medicamentos: paciente.medicamentos_actuales || metadatos.medicamentos || 'Sin medicamentos',
        };
    };

    // Función para obtener el color y estilo de cada etapa
    const obtenerEstiloEtapa = (etapa) => {
        if (etapa.estado === 'COMPLETADA') {
            return {
                bgcolor: '#2196F3', // Azul para completadas
                color: 'white',
                borderColor: '#2196F3',
                icon: <CheckCircleIcon sx={{ fontSize: 32 }} />,
                statusLabel: 'Completada',
                statusColor: '#1976D2',
            };
        } else if (etapa.es_actual) {
            return {
                bgcolor: '#4CAF50', // Verde para actual
                color: 'white',
                borderColor: '#4CAF50',
                icon: <MedicalIcon sx={{ fontSize: 32 }} />,
                statusLabel: 'En Curso',
                statusColor: '#388E3C',
            };
        } else {
            return {
                bgcolor: '#E0E0E0', // Gris para pendientes
                color: '#757575',
                borderColor: '#BDBDBD',
                icon: <ScheduleIcon sx={{ fontSize: 32, color: '#757575' }} />,
                statusLabel: 'Pendiente',
                statusColor: '#9E9E9E',
            };
        }
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 'calc(100vh - 64px)' }}>
                    <CircularProgress />
                </Box>
            </>
        );
    }

    if (!paciente) {
        return (
            <>
                <Navbar />
                <Container maxWidth="xl" sx={{ py: 4 }}>
                    <Alert severity="error">Paciente no encontrado</Alert>
                </Container>
            </>
        );
    }

    const datos = obtenerDatosPaciente(paciente);

    return (
        <>
            <Navbar />
            <Container maxWidth="xl" sx={{ py: 4 }}>
                {error && (
                    <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
                        {error}
                    </Alert>
                )}

                {/* Alertas de Retrasos */}
                {rutaClinica?.retrasos && rutaClinica.retrasos.length > 0 && (
                    <Alert severity="error" icon={<WarningIcon />} sx={{ mb: 3 }}>
                        <Typography variant="subtitle2" fontWeight="600">
                            ⚠️ Se detectaron {rutaClinica.retrasos.length} etapa(s) con retraso
                        </Typography>
                        {rutaClinica.retrasos.map((retraso, index) => (
                            <Typography key={index} variant="body2" sx={{ mt: 0.5 }}>
                                • {retraso.etapa_label}: {retraso.retraso_minutos} minutos de retraso
                            </Typography>
                        ))}
                    </Alert>
                )}

                {/* Card Principal del Paciente */}
                <Card elevation={3} sx={{ mb: 3 }}>
                    <CardContent>
                        <Box sx={{ display: 'flex', gap: 3, mb: 4 }}>
                            <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}>
                                <PersonIcon sx={{ fontSize: 40 }} />
                            </Avatar>
                            <Box sx={{ flex: 1 }}>
                                <Typography variant="h4" fontWeight="bold" gutterBottom>
                                    {datos.nombre}
                                </Typography>
                                <Box sx={{ display: 'flex', gap: 3, mb: 2, flexWrap: 'wrap' }}>
                                    <Typography variant="body1" color="text.secondary">
                                        <strong>Rut:</strong> {datos.rut}
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary">
                                        <strong>Edad:</strong> {datos.edad}
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary">
                                        <strong>Tipo de Sangre:</strong> {datos.tipoSangre}
                                    </Typography>
                                </Box>
                            </Box>

                            <Button
                                variant="outlined"
                                startIcon={<HistoryIcon />}
                                onClick={() => setDialogHistorial(true)}
                                size="small"
                            >
                                Ver Historial
                            </Button>
                        </Box>

                        <Divider sx={{ my: 3 }} />

                        {/* SECCIÓN: Timeline de Etapas - TODAS VISIBLES */}
                        {rutaClinica && rutaClinica.timeline && rutaClinica.timeline.length > 0 ? (
                            <Box sx={{ mb: 4 }}>
                                {/* Header con título y botones de control */}
                                <Box sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    mb: 3,
                                    pb: 2,
                                    borderBottom: '2px solid',
                                    borderColor: 'primary.main',
                                }}>
                                    <Typography variant="h5" fontWeight="700" color="primary.main">
                                        Proceso de Atención
                                    </Typography>

                                    {/* Botones de Control */}
                                    {rutaClinica.ruta_clinica.estado === 'EN_PROGRESO' && (
                                        <Box sx={{ display: 'flex', gap: 2 }}>
                                            <Button
                                                variant="outlined"
                                                startIcon={<ArrowBackIcon />}
                                                onClick={handleRetrocederEtapa}
                                                disabled={actionLoading || rutaClinica.ruta_clinica.indice_etapa_actual === 0}
                                                sx={{
                                                    borderWidth: 2,
                                                    '&:hover': {
                                                        borderWidth: 2,
                                                    }
                                                }}
                                            >
                                                Retroceder
                                            </Button>
                                            <Button
                                                variant="contained"
                                                endIcon={<ArrowForwardIcon />}
                                                onClick={handleAvanzarEtapa}
                                                disabled={actionLoading}
                                                size="large"
                                                sx={{
                                                    px: 3,
                                                    fontWeight: 600,
                                                }}
                                            >
                                                Avanzar Etapa
                                            </Button>
                                        </Box>
                                    )}

                                    {rutaClinica.ruta_clinica.estado === 'COMPLETADA' && (
                                        <Chip
                                            label="✓ Proceso Completado"
                                            color="success"
                                            size="medium"
                                            sx={{ fontWeight: 600, fontSize: '0.9rem' }}
                                        />
                                    )}
                                </Box>

                                {/* Timeline Visual Horizontal - TODAS LAS ETAPAS */}
                                <Box sx={{
                                    display: 'flex',
                                    gap: 2,
                                    overflowX: 'auto',
                                    pb: 3,
                                    px: 1,
                                    '&::-webkit-scrollbar': {
                                        height: 10,
                                    },
                                    '&::-webkit-scrollbar-track': {
                                        bgcolor: 'grey.200',
                                        borderRadius: 5,
                                    },
                                    '&::-webkit-scrollbar-thumb': {
                                        bgcolor: 'primary.main',
                                        borderRadius: 5,
                                        '&:hover': {
                                            bgcolor: 'primary.dark',
                                        }
                                    },
                                }}>
                                    {rutaClinica.timeline.map((etapa, index) => {
                                        const estilo = obtenerEstiloEtapa(etapa);

                                        return (
                                            <Box
                                                key={etapa.orden}
                                                sx={{
                                                    minWidth: 200,
                                                    flex: '0 0 auto',
                                                }}
                                            >
                                                <Card
                                                    elevation={etapa.es_actual ? 8 : 3}
                                                    sx={{
                                                        bgcolor: estilo.bgcolor,
                                                        color: estilo.color,
                                                        borderWidth: etapa.es_actual ? 4 : 2,
                                                        borderStyle: 'solid',
                                                        borderColor: estilo.borderColor,
                                                        transition: 'all 0.3s ease',
                                                        height: '100%',
                                                        position: 'relative',
                                                        '&:hover': {
                                                            transform: 'translateY(-6px)',
                                                            boxShadow: 8,
                                                        },
                                                        // Animación para la etapa actual
                                                        ...(etapa.es_actual && {
                                                            animation: 'pulse 2s ease-in-out infinite',
                                                            '@keyframes pulse': {
                                                                '0%, 100%': {
                                                                    boxShadow: '0 0 0 0 rgba(76, 175, 80, 0.7)',
                                                                },
                                                                '50%': {
                                                                    boxShadow: '0 0 0 10px rgba(76, 175, 80, 0)',
                                                                },
                                                            },
                                                        }),
                                                    }}
                                                >
                                                    <CardContent sx={{
                                                        textAlign: 'center',
                                                        py: 3,
                                                        px: 2,
                                                    }}>
                                                        {/* Número de orden */}
                                                        <Box sx={{
                                                            position: 'absolute',
                                                            top: 10,
                                                            left: 10,
                                                            bgcolor: 'rgba(255, 255, 255, 0.9)',
                                                            color: estilo.statusColor,
                                                            borderRadius: '50%',
                                                            width: 28,
                                                            height: 28,
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontWeight: 'bold',
                                                            fontSize: '0.875rem',
                                                        }}>
                                                            {etapa.orden}
                                                        </Box>

                                                        {/* Icono de la etapa */}
                                                        <Box sx={{ mb: 2, mt: 1 }}>
                                                            {estilo.icon}
                                                        </Box>

                                                        {/* Nombre de la etapa */}
                                                        <Typography
                                                            variant="body1"
                                                            fontWeight="700"
                                                            sx={{
                                                                mb: 1.5,
                                                                lineHeight: 1.3,
                                                                minHeight: 40,
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                            }}
                                                        >
                                                            {etapa.etapa_label}
                                                        </Typography>

                                                        {/* Chip de estado */}
                                                        <Chip
                                                            label={estilo.statusLabel}
                                                            size="small"
                                                            sx={{
                                                                bgcolor: 'white',
                                                                color: estilo.statusColor,
                                                                fontWeight: 600,
                                                                fontSize: '0.75rem',
                                                                height: 26,
                                                                mb: 2,
                                                            }}
                                                        />

                                                        {/* Información de tiempo */}
                                                        {etapa.fecha_inicio && (
                                                            <Box sx={{
                                                                mt: 2,
                                                                pt: 2,
                                                                borderTop: etapa.estado === 'PENDIENTE'
                                                                    ? '1px solid rgba(0,0,0,0.12)'
                                                                    : '1px solid rgba(255,255,255,0.3)'
                                                            }}>
                                                                <Typography
                                                                    variant="caption"
                                                                    display="block"
                                                                    sx={{
                                                                        fontWeight: 600,
                                                                        opacity: etapa.estado === 'PENDIENTE' ? 0.7 : 1,
                                                                        mb: 0.5,
                                                                    }}
                                                                >
                                                                    Inicio: {new Date(etapa.fecha_inicio).toLocaleTimeString('es-CL', {
                                                                        hour: '2-digit',
                                                                        minute: '2-digit'
                                                                    })}
                                                                </Typography>
                                                                {etapa.fecha_fin && (
                                                                    <Typography
                                                                        variant="caption"
                                                                        display="block"
                                                                        sx={{ fontWeight: 600 }}
                                                                    >
                                                                        Fin: {new Date(etapa.fecha_fin).toLocaleTimeString('es-CL', {
                                                                            hour: '2-digit',
                                                                            minute: '2-digit'
                                                                        })}
                                                                    </Typography>
                                                                )}
                                                            </Box>
                                                        )}

                                                        {/* Alerta de retraso */}
                                                        {etapa.retrasada && (
                                                            <Alert
                                                                severity="error"
                                                                icon={<WarningIcon fontSize="small" />}
                                                                sx={{
                                                                    mt: 2,
                                                                    py: 0.5,
                                                                    '& .MuiAlert-message': {
                                                                        fontSize: '0.7rem',
                                                                        fontWeight: 600,
                                                                    }
                                                                }}
                                                            >
                                                                Retrasada
                                                            </Alert>
                                                        )}

                                                        {/* Duración */}
                                                        {etapa.duracion_real && (
                                                            <Typography
                                                                variant="caption"
                                                                display="block"
                                                                sx={{
                                                                    mt: 1.5,
                                                                    fontWeight: 700,
                                                                    opacity: 0.9,
                                                                    fontSize: '0.75rem',
                                                                }}
                                                            >
                                                                Duración: {etapa.duracion_real} min
                                                            </Typography>
                                                        )}

                                                        {/* Observaciones si existen */}
                                                        {etapa.observaciones && (
                                                            <Typography
                                                                variant="caption"
                                                                display="block"
                                                                sx={{
                                                                    mt: 1,
                                                                    fontStyle: 'italic',
                                                                    opacity: 0.8,
                                                                    fontSize: '0.7rem',
                                                                }}
                                                            >
                                                                "{etapa.observaciones}"
                                                            </Typography>
                                                        )}
                                                    </CardContent>
                                                </Card>
                                            </Box>
                                        );
                                    })}
                                </Box>

                                {/* Leyenda de colores */}
                                <Box sx={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    gap: 4,
                                    mt: 3,
                                    pt: 2,
                                    borderTop: '1px solid',
                                    borderColor: 'divider',
                                }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            width: 20,
                                            height: 20,
                                            bgcolor: '#2196F3',
                                            borderRadius: 1,
                                            border: '2px solid #1976D2',
                                        }} />
                                        <Typography variant="body2" fontWeight="500">
                                            Completada
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            width: 20,
                                            height: 20,
                                            bgcolor: '#4CAF50',
                                            borderRadius: 1,
                                            border: '2px solid #388E3C',
                                        }} />
                                        <Typography variant="body2" fontWeight="500">
                                            En Curso
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            width: 20,
                                            height: 20,
                                            bgcolor: '#E0E0E0',
                                            borderRadius: 1,
                                            border: '2px solid #BDBDBD',
                                        }} />
                                        <Typography variant="body2" fontWeight="500">
                                            Pendiente
                                        </Typography>
                                    </Box>
                                </Box>

                                {/* Información de progreso */}
                                <Box sx={{
                                    mt: 3,
                                    p: 2,
                                    bgcolor: 'grey.50',
                                    borderRadius: 2,
                                    display: 'flex',
                                    justifyContent: 'space-around',
                                    flexWrap: 'wrap',
                                    gap: 2,
                                }}>
                                    <Box sx={{ textAlign: 'center' }}>
                                        <Typography variant="h4" fontWeight="700" color="primary.main">
                                            {rutaClinica.etapas_completadas}
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Etapas Completadas
                                        </Typography>
                                    </Box>
                                    <Box sx={{ textAlign: 'center' }}>
                                        <Typography variant="h4" fontWeight="700" color="success.main">
                                            {Math.round(rutaClinica.progreso_general)}%
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Progreso Total
                                        </Typography>
                                    </Box>
                                    <Box sx={{ textAlign: 'center' }}>
                                        <Typography variant="h4" fontWeight="700" color="info.main">
                                            {Math.floor(rutaClinica.tiempo_transcurrido_minutos / 60)}h {rutaClinica.tiempo_transcurrido_minutos % 60}m
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Tiempo Transcurrido
                                        </Typography>
                                    </Box>
                                </Box>
                            </Box>
                        ) : (
                            <Alert severity="info" sx={{ mb: 3 }}>
                                No hay ruta clínica registrada para este paciente
                            </Alert>
                        )}

                        <Divider sx={{ my: 3 }} />

                        {/* Datos del Paciente */}
                        <Typography variant="h6" fontWeight="600" gutterBottom>
                            Datos del paciente
                        </Typography>

                        <Grid container spacing={3} sx={{ mt: 1 }}>
                            <Grid item xs={12} sm={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <PhoneIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">
                                                Contacto
                                            </Typography>
                                            <Typography variant="body1" fontWeight="600">
                                                {datos.contacto}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Paper>
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <HomeIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">
                                                Dirección
                                            </Typography>
                                            <Typography variant="body2" fontWeight="600">
                                                {datos.direccion}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Paper>
                            </Grid>

                            <Grid item xs={12} sm={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <SecurityIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">
                                                Seguro
                                            </Typography>
                                            <Typography variant="body1" fontWeight="600">
                                                {datos.seguro}
                                            </Typography>
                                        </Box>
                                    </Box>
                                </Paper>
                            </Grid>
                        </Grid>

                        {/* Información Médica Adicional */}
                        <Divider sx={{ my: 3 }} />
                        <Typography variant="h6" fontWeight="600" gutterBottom>
                            Información Médica
                        </Typography>

                        <Grid container spacing={2} sx={{ mt: 1 }}>
                            <Grid item xs={12} md={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                                    <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                                        ⚠️ Alergias
                                    </Typography>
                                    <Typography variant="body2">
                                        {datos.alergias}
                                    </Typography>
                                </Paper>
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
                                    <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                                        📋 Condiciones Preexistentes
                                    </Typography>
                                    <Typography variant="body2">
                                        {datos.condiciones}
                                    </Typography>
                                </Paper>
                            </Grid>

                            <Grid item xs={12} md={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                                    <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                                        💊 Medicamentos Actuales
                                    </Typography>
                                    <Typography variant="body2">
                                        {datos.medicamentos}
                                    </Typography>
                                </Paper>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>

                {/* Diálogo de Observaciones */}
                <Dialog
                    open={dialogObservaciones}
                    onClose={() => !actionLoading && setDialogObservaciones(false)}
                    maxWidth="sm"
                    fullWidth
                >
                    <DialogTitle>
                        Agregar Observaciones al Avanzar
                    </DialogTitle>
                    <DialogContent>
                        <Box sx={{ pt: 2 }}>
                            <TextField
                                fullWidth
                                multiline
                                rows={4}
                                label="Observaciones sobre esta etapa"
                                value={observaciones}
                                onChange={(e) => setObservaciones(e.target.value)}
                                placeholder="Ej: Paciente presenta mejoría, derivado a laboratorio"
                                helperText="Opcional: Agregue notas sobre esta etapa antes de avanzar"
                            />
                        </Box>
                    </DialogContent>
                    <DialogActions>
                        <Button
                            onClick={() => setDialogObservaciones(false)}
                            disabled={actionLoading}
                        >
                            Cancelar
                        </Button>
                        <Button
                            onClick={handleAvanzarConObservaciones}
                            variant="contained"
                            disabled={actionLoading}
                        >
                            {actionLoading ? 'Procesando...' : 'Avanzar'}
                        </Button>
                    </DialogActions>
                </Dialog>

                {/* Diálogo de Historial */}
                <Dialog
                    open={dialogHistorial}
                    onClose={() => setDialogHistorial(false)}
                    maxWidth="md"
                    fullWidth
                >
                    <DialogTitle>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <HistoryIcon />
                            Historial de Cambios
                        </Box>
                    </DialogTitle>
                    <DialogContent dividers>
                        {historial.length === 0 ? (
                            <Alert severity="info">
                                No hay registros en el historial
                            </Alert>
                        ) : (
                            <List>
                                {historial.map((entrada, index) => (
                                    <React.Fragment key={index}>
                                        <ListItem>
                                            <ListItemText
                                                primary={
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <Chip
                                                            label={entrada.accion}
                                                            size="small"
                                                            color="primary"
                                                        />
                                                        {entrada.desde && entrada.hacia && (
                                                            <Typography variant="body2">
                                                                {entrada.desde} → {entrada.hacia}
                                                            </Typography>
                                                        )}
                                                    </Box>
                                                }
                                                secondary={
                                                    <>
                                                        <Typography variant="caption" display="block">
                                                            {new Date(entrada.timestamp).toLocaleString('es-CL')}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            Usuario: {entrada.usuario}
                                                        </Typography>
                                                        {entrada.motivo && (
                                                            <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                                                Motivo: {entrada.motivo}
                                                            </Typography>
                                                        )}
                                                    </>
                                                }
                                            />
                                        </ListItem>
                                        {index < historial.length - 1 && <Divider />}
                                    </React.Fragment>
                                ))}
                            </List>
                        )}
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setDialogHistorial(false)}>
                            Cerrar
                        </Button>
                    </DialogActions>
                </Dialog>
            </Container>
        </>
    );
};

export default DetallePaciente;