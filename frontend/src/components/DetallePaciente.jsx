// frontend/src/components/DetallePaciente.jsx - CON BARRA DE PROGRESO CONTINUA
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
                    'Sin dirección registrada',
            seguro: metadatos.seguro || 
                    paciente.seguro_medico_display || 
                    'Sin seguro',
            alergias: paciente.alergias || metadatos.alergias || 'Sin alergias registradas',
            condiciones: paciente.condiciones_preexistentes || metadatos.condiciones || 'Sin condiciones',
            medicamentos: paciente.medicamentos_actuales || metadatos.medicamentos || 'Sin medicamentos',
        };
    };

    // Función para obtener el icono según la etapa
    const getStageIcon = (etapaKey) => {
        const icons = {
            'CONSULTA_MEDICA': '🩺',
            'PROCESO_EXAMEN': '🧪',
            'REVISION_EXAMEN': '📋',
            'HOSPITALIZACION': '🏥',
            'OPERACION': '⚕️',
            'ALTA': '✅',
        };
        return icons[etapaKey] || '📌';
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
                                        <strong>RUT:</strong> {datos.rut}
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary">
                                        <strong>Edad:</strong> {datos.edad}
                                    </Typography>
                                    <Typography variant="body1" color="text.secondary">
                                        <strong>Tipo de Sangre:</strong> {datos.tipoSangre}
                                    </Typography>
                                </Box>
                                
                                {/* Estado y Etapa Sincronizados */}
                                <Alert 
                                    severity="info" 
                                    sx={{ 
                                        mb: 2,
                                        bgcolor: 'primary.50',
                                        '& .MuiAlert-message': {
                                            width: '100%'
                                        }
                                    }}
                                >
                                    <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                                        Estado Actual del Paciente
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
                                        <Box>
                                            <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                                                Estado del Sistema:
                                            </Typography>
                                            <Chip
                                                label={paciente.estado_actual_display}
                                                color={getColorUrgencia(paciente.estado_actual)}
                                                size="small"
                                                sx={{ fontWeight: 600 }}
                                            />
                                        </Box>
                                        
                                        {paciente.etapa_actual ? (
                                            <Box>
                                                <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                                                    Etapa del Flujo Clínico:
                                                </Typography>
                                                <Chip
                                                    icon={<TimelineIcon sx={{ fontSize: 14 }} />}
                                                    label={paciente.etapa_actual_display}
                                                    size="small"
                                                    sx={{ 
                                                        fontWeight: 600,
                                                        bgcolor: '#2196F3',
                                                        color: 'white',
                                                        '& .MuiChip-icon': {
                                                            color: 'white',
                                                        }
                                                    }}
                                                />
                                            </Box>
                                        ) : (
                                            <Box>
                                                <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                                                    Etapa del Flujo Clínico:
                                                </Typography>
                                                <Chip
                                                    label="Sin etapa asignada"
                                                    size="small"
                                                    variant="outlined"
                                                    sx={{ fontWeight: 500 }}
                                                />
                                            </Box>
                                        )}
                                        
                                        <Box>
                                            <Typography variant="caption" display="block" sx={{ mb: 0.5 }}>
                                                Urgencia:
                                            </Typography>
                                            <Chip
                                                label={paciente.nivel_urgencia_display}
                                                color={getColorUrgencia(paciente.nivel_urgencia)}
                                                size="small"
                                                sx={{ fontWeight: 600 }}
                                            />
                                        </Box>
                                    </Box>
                                </Alert>
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

                        {/* ============================================
                            NUEVA BARRA DE PROGRESO CONTINUA
                            ============================================ */}
                        {rutaClinica && rutaClinica.timeline && rutaClinica.timeline.length > 0 ? (
                            <Box sx={{ mb: 4 }}>
                                {/* Header */}
                                <Box sx={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    mb: 3,
                                    pb: 2,
                                    borderBottom: '2px solid',
                                    borderColor: 'primary.main',
                                }}>
                                    <Box>
                                        <Typography variant="h5" fontWeight="700" color="primary.main">
                                            Proceso de Atención Completo
                                        </Typography>
                                        <Typography variant="caption" color="text.secondary">
                                            Seguimiento del flujo clínico • Sincronización automática
                                        </Typography>
                                    </Box>

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
                                                    '&:hover': { borderWidth: 2 }
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
                                                sx={{ px: 3, fontWeight: 600 }}
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

                                {/* BARRA DE PROGRESO CONTINUA */}
                                <Box sx={{ position: 'relative', width: '100%', mb: 4, px: 2 }}>
                                    {/* Barra base de fondo */}
                                    <Box sx={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: 20,
                                        right: 20,
                                        height: 8,
                                        bgcolor: '#E0E0E0',
                                        borderRadius: 10,
                                        transform: 'translateY(-50%)',
                                        zIndex: 0
                                    }} />

                                    {/* Barra de progreso activa */}
                                    <Box sx={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: 20,
                                        height: 8,
                                        width: `calc((100% - 40px) * ${rutaClinica.progreso_general / 100})`,
                                        bgcolor: '#4CAF50',
                                        borderRadius: 10,
                                        transform: 'translateY(-50%)',
                                        transition: 'width 0.5s ease-in-out',
                                        zIndex: 1,
                                        boxShadow: '0 0 10px rgba(76, 175, 80, 0.5)'
                                    }} />

                                    {/* Etapas sobre la barra */}
                                    <Box sx={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        position: 'relative',
                                        zIndex: 2,
                                    }}>
                                        {rutaClinica.timeline.map((etapa, index) => {
                                            const isCompleted = etapa.estado === 'COMPLETADA';
                                            const isCurrent = etapa.es_actual;
                                            const isPending = etapa.estado === 'PENDIENTE';

                                            const getStageColor = () => {
                                                if (isCompleted) return '#2196F3';
                                                if (isCurrent) return '#4CAF50';
                                                return '#E0E0E0';
                                            };

                                            const getTextColor = () => {
                                                if (isCompleted || isCurrent) return 'white';
                                                return '#757575';
                                            };

                                            return (
                                                <Tooltip 
                                                    key={etapa.orden}
                                                    title={
                                                        <Box sx={{ p: 1 }}>
                                                            <Typography variant="subtitle2" fontWeight="600">
                                                                {etapa.etapa_label}
                                                            </Typography>
                                                            {etapa.fecha_inicio && (
                                                                <Typography variant="caption" display="block">
                                                                    Inicio: {new Date(etapa.fecha_inicio).toLocaleString('es-CL')}
                                                                </Typography>
                                                            )}
                                                            {etapa.fecha_fin && (
                                                                <Typography variant="caption" display="block">
                                                                    Fin: {new Date(etapa.fecha_fin).toLocaleString('es-CL')}
                                                                </Typography>
                                                            )}
                                                            {etapa.duracion_real && (
                                                                <Typography variant="caption" display="block">
                                                                    Duración: {etapa.duracion_real} min
                                                                </Typography>
                                                            )}
                                                            <Typography variant="caption" display="block" sx={{ mt: 0.5, fontWeight: 600 }}>
                                                                Estado: {isCompleted ? 'Completada' : isCurrent ? 'En Curso' : 'Pendiente'}
                                                            </Typography>
                                                            {etapa.observaciones && (
                                                                <Typography variant="caption" display="block" sx={{ mt: 0.5, fontStyle: 'italic' }}>
                                                                    "{etapa.observaciones}"
                                                                </Typography>
                                                            )}
                                                        </Box>
                                                    }
                                                    arrow
                                                    placement="top"
                                                >
                                                    <Box sx={{
                                                        display: 'flex',
                                                        flexDirection: 'column',
                                                        alignItems: 'center',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.3s ease',
                                                        '&:hover': {
                                                            transform: 'translateY(-6px)',
                                                        }
                                                    }}>
                                                        {/* Círculo con ícono */}
                                                        <Box sx={{
                                                            width: isCurrent ? 70 : 60,
                                                            height: isCurrent ? 70 : 60,
                                                            borderRadius: '50%',
                                                            bgcolor: getStageColor(),
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            border: isCurrent ? '4px solid #388E3C' : '3px solid white',
                                                            boxShadow: isCurrent 
                                                                ? '0 4px 12px rgba(76, 175, 80, 0.6)' 
                                                                : isCompleted 
                                                                ? '0 2px 8px rgba(33, 150, 243, 0.4)'
                                                                : '0 2px 8px rgba(0,0,0,0.1)',
                                                            transition: 'all 0.3s ease',
                                                            fontSize: isCurrent ? '32px' : '28px',
                                                            mb: 1.5,
                                                            ...(isCurrent && {
                                                                animation: 'pulse 2s ease-in-out infinite',
                                                                '@keyframes pulse': {
                                                                    '0%, 100%': {
                                                                        boxShadow: '0 4px 12px rgba(76, 175, 80, 0.6)',
                                                                    },
                                                                    '50%': {
                                                                        boxShadow: '0 4px 20px rgba(76, 175, 80, 0.9)',
                                                                    },
                                                                },
                                                            }),
                                                        }}>
                                                            {getStageIcon(etapa.etapa_key)}
                                                        </Box>

                                                        {/* Número de orden */}
                                                        <Box sx={{
                                                            bgcolor: getStageColor(),
                                                            color: getTextColor(),
                                                            borderRadius: '50%',
                                                            width: 24,
                                                            height: 24,
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontWeight: 'bold',
                                                            fontSize: '0.75rem',
                                                            mb: 0.5,
                                                            border: '2px solid white',
                                                            boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                                                        }}>
                                                            {etapa.orden}
                                                        </Box>

                                                        {/* Nombre de la etapa */}
                                                        <Typography
                                                            variant="body2"
                                                            fontWeight={isCurrent ? 700 : 600}
                                                            sx={{
                                                                color: isCompleted || isCurrent ? 'text.primary' : 'text.secondary',
                                                                textAlign: 'center',
                                                                maxWidth: 100,
                                                                lineHeight: 1.3,
                                                                mb: 0.5,
                                                                fontSize: isCurrent ? '0.875rem' : '0.8rem'
                                                            }}
                                                        >
                                                            {etapa.etapa_label}
                                                        </Typography>

                                                        {/* Badge de estado */}
                                                        <Chip
                                                            label={
                                                                isCompleted ? 'Completada' : 
                                                                isCurrent ? 'En Curso' : 
                                                                'Pendiente'
                                                            }
                                                            size="small"
                                                            sx={{
                                                                height: 22,
                                                                fontSize: '0.65rem',
                                                                fontWeight: 600,
                                                                bgcolor: isCompleted ? '#E3F2FD' : 
                                                                        isCurrent ? '#E8F5E9' : 
                                                                        '#F5F5F5',
                                                                color: isCompleted ? '#1976D2' : 
                                                                       isCurrent ? '#388E3C' : 
                                                                       '#757575',
                                                            }}
                                                        />

                                                        {/* Alerta de retraso */}
                                                        {etapa.retrasada && (
                                                            <Chip
                                                                icon={<WarningIcon sx={{ fontSize: 14 }} />}
                                                                label="Retrasada"
                                                                size="small"
                                                                color="error"
                                                                sx={{
                                                                    mt: 0.5,
                                                                    height: 20,
                                                                    fontSize: '0.6rem',
                                                                    fontWeight: 600,
                                                                }}
                                                            />
                                                        )}
                                                    </Box>
                                                </Tooltip>
                                            );
                                        })}
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
                                            width: 16,
                                            height: 16,
                                            bgcolor: '#2196F3',
                                            borderRadius: '50%',
                                        }} />
                                        <Typography variant="body2" fontWeight="500">
                                            Completada
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            width: 16,
                                            height: 16,
                                            bgcolor: '#4CAF50',
                                            borderRadius: '50%',
                                        }} />
                                        <Typography variant="body2" fontWeight="500">
                                            En Curso
                                        </Typography>
                                    </Box>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Box sx={{
                                            width: 16,
                                            height: 16,
                                            bgcolor: '#E0E0E0',
                                            borderRadius: '50%',
                                        }} />
                                        <Typography variant="body2" fontWeight="500">
                                            Pendiente
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
                                                Contacto</Typography>
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