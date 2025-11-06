// frontend/src/components/DetallePaciente.jsx - VERSIÓN MEJORADA CON TIEMPOS REALES
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
    Tooltip,
    LinearProgress,
    Stepper,
    Step,
    StepLabel,
    styled,
    keyframes,
} from '@mui/material';
import {
    Person as PersonIcon,
    Phone as PhoneIcon,
    Home as HomeIcon,
    Security as SecurityIcon,
    History as HistoryIcon,
    Warning as WarningIcon,
    ArrowForward as ArrowForwardIcon,
    ArrowBack as ArrowBackIcon,
    Timeline as TimelineIcon,
    AccessTime as AccessTimeIcon,
    CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { pacientesService, rutasClinicasService } from '../services/api';
import Navbar from './Navbar';

// ⭐ Animación de titineo para la etapa actual
const pulseAnimation = keyframes`
    0% {
        box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7);
    }
    50% {
        box-shadow: 0 0 0 10px rgba(33, 150, 243, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(33, 150, 243, 0);
    }
`;

// ✅ NUEVA: Función para calcular tiempo transcurrido
const calcularTiempoTranscurrido = (fechaInicio, fechaFin = null) => {
    try {
        const inicio = new Date(fechaInicio);
        const fin = fechaFin ? new Date(fechaFin) : new Date();
        const diferenciaMs = fin - inicio;
        const minutos = Math.floor(diferenciaMs / 60000);
        
        if (minutos < 60) {
            return `${minutos} min`;
        }
        
        const horas = Math.floor(minutos / 60);
        if (horas < 24) {
            const mins = minutos % 60;
            return mins > 0 ? `${horas}h ${mins}min` : `${horas}h`;
        }
        
        const dias = Math.floor(horas / 24);
        const horasRestantes = horas % 24;
        return horasRestantes > 0 ? `${dias}d ${horasRestantes}h` : `${dias} día${dias !== 1 ? 's' : ''}`;
    } catch (error) {
        console.error('Error calculando tiempo:', error);
        return '0 min';
    }
};

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

    // ✅ NUEVO: Estado para actualizar el tiempo en vivo
    const [, forceUpdate] = useState(0);

    useEffect(() => {
        cargarDatos();
        const interval = setInterval(cargarDatos, 30000);
        return () => clearInterval(interval);
    }, [id]);

    // ✅ NUEVO: Actualizar tiempo cada minuto para las etapas en curso
    useEffect(() => {
        const timerInterval = setInterval(() => {
            forceUpdate(prev => prev + 1);
        }, 60000); // Cada 60 segundos

        return () => clearInterval(timerInterval);
    }, []);

    const cargarDatos = async () => {
        try {
            setError('');
            setLoading(true);

            const timestamp = new Date().getTime();
            const nocache = Math.random();

            const pacienteRes = await pacientesService.getById(id, { 
                _t: timestamp,
                _nocache: nocache 
            });
            setPaciente(pacienteRes.data);

            const rutasRes = await pacientesService.getRutasClinicas(id, {
                _t: timestamp,
                _nocache: nocache
            });

            if (rutasRes.data && rutasRes.data.length > 0) {
                const rutaActual = rutasRes.data[0];
                const timelineRes = await rutasClinicasService.getTimeline(rutaActual.id);
                
                console.log('✅ Timeline completo recibido:', timelineRes.data);
                
                setRutaClinica(timelineRes.data);

                const historialRes = await rutasClinicasService.getHistorial(rutaActual.id);
                setHistorial(historialRes.data.historial || []);
            } else {
                setRutaClinica(null);
                setHistorial([]);
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
        if (!paciente) {
            return {
                nombre: 'Paciente desconocido',
                rut: 'Sin RUT',
                edad: 0,
                tipoSangre: 'Desconocido',
                contacto: 'Sin contacto',
                direccion: 'Sin dirección',
                seguro: 'Sin seguro',
                alergias: 'Sin alergias',
                condiciones: 'Sin condiciones',
                medicamentos: 'Sin medicamentos',
            };
        }

        const metadatos = paciente.metadatos_adicionales || {};
        const identificador = paciente.identificador_hash || paciente.id || '';
        const identificadorCorto = identificador ? identificador.substring(0, 8) : 'SIN-ID';

        return {
            nombre: metadatos.nombre || 
                    paciente.nombre_completo || 
                    `Paciente ${identificadorCorto}`,
            rut: metadatos.rut_original || 
                paciente.rut || 
                (identificador ? identificador.substring(0, 12) : 'Sin RUT'),
            edad: paciente.edad || 0,
            tipoSangre: metadatos.tipo_sangre || paciente.tipo_sangre || 'O+',
            contacto: metadatos.contacto || paciente.telefono || '+56 9 0000 0000',
            direccion: metadatos.direccion || 
                    paciente.direccion_completa || 
                    'No especificada',
            seguro: metadatos.seguro || 
                    paciente.seguro_medico_display || 
                    'Sin seguro',
            alergias: paciente.alergias || metadatos.alergias || 'Sin alergias registradas',
            condiciones: paciente.condiciones_preexistentes || metadatos.condiciones || 'Sin condiciones',
            medicamentos: paciente.medicamentos_actuales || metadatos.medicamentos || 'Sin medicamentos',
        };
    };

    // Función para obtener el emoji según la etapa
    const getEmojiForEtapa = (etapaKey) => {
        const emojis = {
            'CONSULTA_MEDICA': '👨‍⚕️',
            'PROCESO_EXAMEN': '🔬',
            'REVISION_EXAMEN': '📋',
            'HOSPITALIZACION': '🏥',
            'OPERACION': '⚕️',
            'ALTA': '✅',
        };
        return emojis[etapaKey] || '📌';
    };

    // ⭐ Renderizar el icono de etapa con animación y emoji
    const renderStepIcon = (etapa, index) => {
        const { estado, es_actual, etapa_key } = etapa;
        const emoji = getEmojiForEtapa(etapa_key);

        if (estado === 'COMPLETADA') {
            return (
                <Box
                    sx={{
                        width: 50,
                        height: 50,
                        borderRadius: '50%',
                        backgroundColor: 'success.main',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 28,
                        border: '3px solid white',
                        boxShadow: '0 2px 8px rgba(76, 175, 80, 0.4)',
                    }}
                >
                    {emoji}
                </Box>
            );
        }

        if (es_actual) {
            return (
                <Box
                    sx={{
                        width: 50,
                        height: 50,
                        borderRadius: '50%',
                        backgroundColor: 'primary.main',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 28,
                        border: '3px solid white',
                        animation: `${pulseAnimation} 2s infinite`,
                        boxShadow: '0 4px 12px rgba(33, 150, 243, 0.6)',
                    }}
                >
                    {emoji}
                </Box>
            );
        }

        return (
            <Box
                sx={{
                    width: 50,
                    height: 50,
                    borderRadius: '50%',
                    backgroundColor: 'grey.300',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 28,
                    border: '3px solid white',
                    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
                    opacity: 0.6,
                }}
            >
                {emoji}
            </Box>
        );
    };

    // ⭐ Calcular posición de la barra alineada con la etapa actual
    const calcularPosicionBarra = () => {
        if (!rutaClinica || !rutaClinica.timeline) return 0;

        const timeline = rutaClinica.timeline;
        const etapaActualIndex = timeline.findIndex(e => e.es_actual);

        if (etapaActualIndex === -1) {
            const completadas = timeline.filter(e => e.estado === 'COMPLETADA').length;
            return (completadas / timeline.length) * 100;
        }

        const posicionEtapa = etapaActualIndex / timeline.length;
        const mitadEtapa = 0.5 / timeline.length;
        
        return (posicionEtapa + mitadEtapa) * 100;
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
                    <CircularProgress size={60} />
                </Container>
            </>
        );
    }

    const datos = obtenerDatosPaciente(paciente);

    return (
        <>
            <Navbar />
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                        {error}
                    </Alert>
                )}

                {/* Cabecera del Paciente */}
                <Paper elevation={3} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item>
                            <Avatar sx={{ width: 80, height: 80, bgcolor: 'white', color: 'primary.main' }}>
                                <PersonIcon sx={{ fontSize: 50 }} />
                            </Avatar>
                        </Grid>
                        <Grid item xs>
                            <Typography variant="h4" fontWeight="700" color="white" gutterBottom>
                                {datos.nombre}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                <Chip
                                    label={`RUT: ${datos.rut}`}
                                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                                />
                                <Chip
                                    label={`${datos.edad} años`}
                                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                                />
                                <Chip
                                    label={paciente?.genero_display || 'No especificado'}
                                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                                />
                                <Chip
                                    label={`Tipo: ${datos.tipoSangre}`}
                                    sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 600 }}
                                />
                                <Chip
                                    label={paciente?.estado_actual_display || 'Estado desconocido'}
                                    color={getColorUrgencia(paciente?.nivel_urgencia)}
                                />
                            </Box>
                        </Grid>
                    </Grid>
                </Paper>

                {/* Timeline de Ruta Clínica */}
                {rutaClinica && (
                    <Card elevation={3} sx={{ mb: 3 }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <TimelineIcon color="primary" sx={{ fontSize: 30 }} />
                                    <Typography variant="h5" fontWeight="600">
                                        Ruta Clínica
                                    </Typography>
                                </Box>
                                <Chip
                                    label={rutaClinica.estado_actual}
                                    color={rutaClinica.estado_actual === 'COMPLETADA' ? 'success' : 'primary'}
                                    sx={{ fontWeight: 600 }}
                                />
                            </Box>

                            {/* Barra de progreso */}
                            <Box sx={{ mb: 4 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Progreso General
                                    </Typography>
                                    <Typography variant="body2" fontWeight="600" color="primary">
                                        {rutaClinica.etapas_completadas}/{rutaClinica.etapas_totales} etapas
                                    </Typography>
                                </Box>
                                <LinearProgress
                                    variant="determinate"
                                    value={calcularPosicionBarra()}
                                    sx={{
                                        height: 12,
                                        borderRadius: 2,
                                        bgcolor: 'grey.200',
                                        '& .MuiLinearProgress-bar': {
                                            borderRadius: 2,
                                            background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                                        }
                                    }}
                                />
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                                    {rutaClinica.progreso_general.toFixed(1)}% completado
                                </Typography>
                            </Box>

                            {/* Timeline de Etapas */}
                            <Box sx={{ mb: 3 }}>
                                <Stepper 
                                    activeStep={-1} 
                                    alternativeLabel
                                    sx={{
                                        '& .MuiStepConnector-line': {
                                            borderTopWidth: 3,
                                        }
                                    }}
                                >
                                    {rutaClinica.timeline && rutaClinica.timeline.map((etapa, index) => (
                                        <Step 
                                            key={etapa.etapa_key} 
                                            completed={etapa.estado === 'COMPLETADA'}
                                        >
                                            <StepLabel
                                                StepIconComponent={() => renderStepIcon(etapa, index)}
                                                sx={{
                                                    '& .MuiStepLabel-label': {
                                                        fontWeight: etapa.es_actual ? 700 : 400,
                                                        color: etapa.es_actual 
                                                            ? 'primary.main' 
                                                            : etapa.estado === 'COMPLETADA' 
                                                            ? 'success.main' 
                                                            : 'text.secondary',
                                                    }
                                                }}
                                            >
                                                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
                                                    <Typography
                                                        variant="body2"
                                                        sx={{
                                                            fontWeight: etapa.es_actual ? 700 : 400,
                                                            color: etapa.es_actual 
                                                                ? 'primary.main' 
                                                                : etapa.estado === 'COMPLETADA' 
                                                                ? 'success.main' 
                                                                : 'text.secondary',
                                                        }}
                                                    >
                                                        {etapa.etapa_label}
                                                    </Typography>
                                                    
                                                    {/* ✅ MEJORADO: Calcular tiempo real para cada etapa */}
                                                    {etapa.fecha_inicio && (
                                                        <Tooltip title={
                                                            etapa.es_actual 
                                                                ? "Tiempo en esta etapa (en curso)" 
                                                                : etapa.estado === 'COMPLETADA'
                                                                ? "Duración de la etapa"
                                                                : "Tiempo en esta etapa"
                                                        }>
                                                            <Chip
                                                                icon={etapa.es_actual ? <AccessTimeIcon sx={{ fontSize: 14 }} /> : <CheckCircleIcon sx={{ fontSize: 14 }} />}
                                                                label={
                                                                    etapa.es_actual
                                                                        ? calcularTiempoTranscurrido(etapa.fecha_inicio)
                                                                        : etapa.duracion_real_legible || 
                                                                          calcularTiempoTranscurrido(etapa.fecha_inicio, etapa.fecha_fin)
                                                                }
                                                                size="small"
                                                                color={etapa.es_actual ? 'primary' : etapa.estado === 'COMPLETADA' ? 'success' : 'default'}
                                                                variant="outlined"
                                                                sx={{ 
                                                                    fontWeight: 600, 
                                                                    height: 24, 
                                                                    fontSize: '0.7rem', 
                                                                    mt: 0.5 
                                                                }}
                                                            />
                                                        </Tooltip>
                                                    )}
                                                    
                                                    {etapa.es_actual && (
                                                        <Chip
                                                            label="En Curso"
                                                            size="small"
                                                            color="primary"
                                                            sx={{ fontWeight: 600, height: 20, fontSize: '0.7rem', mt: 0.5 }}
                                                        />
                                                    )}
                                                </Box>
                                            </StepLabel>
                                        </Step>
                                    ))}
                                </Stepper>
                            </Box>

                            {/* Botones de Acción */}
                            {rutaClinica.estado_actual !== 'COMPLETADA' && (
                                <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                                    <Button
                                        variant="outlined"
                                        startIcon={<ArrowBackIcon />}
                                        onClick={handleRetrocederEtapa}
                                        disabled={actionLoading || rutaClinica.ruta_clinica?.indice_etapa_actual === 0}
                                    >
                                        Retroceder
                                    </Button>
                                    <Button
                                        variant="contained"
                                        endIcon={<ArrowForwardIcon />}
                                        onClick={handleAvanzarEtapa}
                                        disabled={actionLoading}
                                        sx={{ flexGrow: 1 }}
                                    >
                                        Avanzar Etapa
                                    </Button>
                                    <Button
                                        variant="outlined"
                                        startIcon={<HistoryIcon />}
                                        onClick={() => setDialogHistorial(true)}
                                    >
                                        Ver Historial
                                    </Button>
                                </Box>
                            )}

                            {/* ✅ ALERTAS DE RETRASOS MEJORADAS - MOSTRAR EN DÍAS */}
                            {rutaClinica.retrasos && rutaClinica.retrasos.length > 0 && (
                                <Alert severity="warning" icon={<WarningIcon />} sx={{ mt: 2 }}>
                                    <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                                        ⚠️ Retrasos Detectados:
                                    </Typography>
                                    <List dense>
                                        {rutaClinica.retrasos.map((retraso, idx) => {
                                            // ✅ Calcular días del retraso
                                            const diasRetraso = retraso.retraso_dias || Math.floor(retraso.retraso_minutos / 1440);
                                            const horasRetraso = retraso.retraso_horas ? retraso.retraso_horas % 24 : Math.floor((retraso.retraso_minutos % 1440) / 60);
                                            
                                            return (
                                                <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                                                    <ListItemText
                                                        primary={
                                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                                                                <Typography variant="body2" fontWeight="600" color="error">
                                                                    {retraso.etapa_label || retraso.etapa}:
                                                                </Typography>
                                                                <Chip
                                                                    label={`Lleva ${retraso.duracion_actual_legible || calcularTiempoTranscurrido(null, null)}`}
                                                                    size="small"
                                                                    color="warning"
                                                                    sx={{ fontWeight: 500 }}
                                                                />
                                                                {/* ✅ CHIP GRANDE CON DÍAS DE RETRASO */}
                                                                <Chip
                                                                    label={
                                                                        diasRetraso > 0 
                                                                            ? `⚠️ ${diasRetraso} día${diasRetraso !== 1 ? 's' : ''} ${horasRetraso > 0 ? `${horasRetraso}h` : ''} de retraso`
                                                                            : `⚠️ ${horasRetraso}h de retraso`
                                                                    }
                                                                    size="medium"
                                                                    color="error"
                                                                    sx={{ 
                                                                        fontWeight: 700,
                                                                        fontSize: '0.9rem',
                                                                        height: 32,
                                                                        px: 2
                                                                    }}
                                                                />
                                                            </Box>
                                                        }
                                                        secondary={
                                                            <Typography variant="caption" color="text.secondary">
                                                                Estimado: {retraso.duracion_estimada_legible || `${Math.floor(retraso.duracion_estimada_minutos / 1440)}d ${Math.floor((retraso.duracion_estimada_minutos % 1440) / 60)}h`} • 
                                                                Máximo permitido: {retraso.duracion_maxima_permitida_legible || `${Math.floor(retraso.duracion_maxima_permitida / 1440)}d ${Math.floor((retraso.duracion_maxima_permitida % 1440) / 60)}h`}
                                                                {retraso.margen_tolerancia && ` (${retraso.margen_tolerancia} margen)`}
                                                            </Typography>
                                                        }
                                                    />
                                                </ListItem>
                                            );
                                        })}
                                    </List>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Información del Paciente */}
                <Card elevation={3}>
                    <CardContent>
                        <Typography variant="h6" fontWeight="600" gutterBottom>
                            Información del Paciente
                        </Typography>

                        <Grid container spacing={2} sx={{ mt: 2 }}>
                            <Grid item xs={12} sm={4}>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                        <PhoneIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                                        <Box>
                                            <Typography variant="caption" color="text.secondary">
                                                Contacto
                                            </Typography>
                                            <Typography variant="body2" fontWeight="600">
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