// frontend/src/components/DetallePaciente.jsx
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
  LinearProgress,
  Stack,
} from '@mui/material';
import {
  Person as PersonIcon,
  Phone as PhoneIcon,
  Home as HomeIcon,
  Security as SecurityIcon,
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as PendingIcon,
  PlayArrow as InProgressIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import { pacientesService, rutasClinicasService } from '../services/api';
import Navbar from './Navbar';

const DetallePaciente = () => {
  const { id } = useParams();
  
  const [paciente, setPaciente] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    cargarDatos();
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
      }

      setLoading(false);
    } catch (err) {
      setError('Error al cargar los datos del paciente');
      setLoading(false);
      console.error(err);
    }
  };

  const handleAvanzarEtapa = async () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return;

    try {
      setActionLoading(true);
      setError('');
      setSuccess('');
      
      const response = await rutasClinicasService.avanzar(rutaClinica.ruta_clinica.id);
      
      if (response.data.success) {
        setSuccess(response.data.mensaje);
        await cargarDatos();
      }
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
      setError('');
      setSuccess('');
      
      const response = await rutasClinicasService.retroceder(rutaClinica.ruta_clinica.id);
      
      if (response.data.success) {
        setSuccess(response.data.mensaje);
        await cargarDatos();
      }
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

  const getEtapaColor = (estado) => {
    if (estado === 'COMPLETADA') return { bg: '#4caf50', color: 'white' }; // Verde
    if (estado === 'EN_PROCESO') return { bg: '#2196f3', color: 'white' }; // Azul
    return { bg: '#e0e0e0', color: '#666' }; // Gris
  };

  const getEtapaIcon = (estado) => {
    if (estado === 'COMPLETADA') return <CheckCircleIcon sx={{ fontSize: 32 }} />;
    if (estado === 'EN_PROCESO') return <InProgressIcon sx={{ fontSize: 32 }} />;
    return <PendingIcon sx={{ fontSize: 32 }} />;
  };

  const obtenerDatosPaciente = (paciente) => {
    return {
      nombre: paciente.metadatos_adicionales?.nombre || `Paciente ${paciente.identificador_hash.substring(0, 8)}`,
      rut: paciente.metadatos_adicionales?.rut || paciente.identificador_hash.substring(0, 12),
      edad: paciente.edad,
      tipoSangre: paciente.metadatos_adicionales?.tipo_sangre || 'N/A',
      contacto: paciente.metadatos_adicionales?.contacto || 'N/A',
      direccion: paciente.metadatos_adicionales?.direccion || 'N/A',
      seguro: paciente.metadatos_adicionales?.seguro || 'N/A',
    };
  };

  const puedeAvanzar = () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return false;
    // Puede avanzar si NO está completada
    return rutaClinica.ruta_clinica.estado !== 'COMPLETADA';
  };

  const puedeRetroceder = () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return false;
    // Puede retroceder si tiene al menos 1 etapa completada y no está completada
    return rutaClinica.etapas_completadas > 0;
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

        {success && (
          <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
            {success}
          </Alert>
        )}

        {/* Card Principal del Paciente */}
        <Card elevation={3} sx={{ mb: 3 }}>
          <CardContent>
            {/* Header con información básica */}
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
                    <strong>Edad:</strong> {datos.edad} años
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    <strong>Tipo de Sangre:</strong> {datos.tipoSangre}
                  </Typography>
                  <Chip
                    label={paciente.nivel_urgencia_display}
                    color={getColorUrgencia(paciente.nivel_urgencia)}
                    size="small"
                  />
                </Box>
              </Box>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Proceso de Atención - Etapas */}
            {rutaClinica && rutaClinica.timeline && (
              <Box sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6" fontWeight="600">
                    Proceso de Atención
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Progreso: {Math.round(rutaClinica.progreso_general)}%
                    </Typography>
                    <Box sx={{ width: 150 }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={rutaClinica.progreso_general} 
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </Box>
                  </Box>
                </Box>

                {/* Grid de etapas con diseño uniforme */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  {rutaClinica.timeline.map((etapa) => {
                    const colors = getEtapaColor(etapa.estado);
                    return (
                      <Grid item xs={6} sm={4} md={2} key={etapa.orden}>
                        <Card
                          variant="outlined"
                          sx={{
                            bgcolor: colors.bg,
                            color: colors.color,
                            borderWidth: etapa.es_actual ? 3 : 1,
                            borderColor: etapa.es_actual ? 'primary.dark' : 'divider',
                            transition: 'all 0.3s',
                            height: '100%',
                            minHeight: '200px',
                            display: 'flex',
                            flexDirection: 'column',
                            '&:hover': {
                              transform: 'translateY(-4px)',
                              boxShadow: 3,
                            },
                          }}
                        >
                          <CardContent sx={{ 
                            p: 2, 
                            textAlign: 'center', 
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            '&:last-child': { pb: 2 } 
                          }}>
                            {/* Icono */}
                            <Box sx={{ mb: 1 }}>
                              {getEtapaIcon(etapa.estado)}
                            </Box>
                            
                            {/* Nombre de etapa - ocupa el espacio central */}
                            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <Typography 
                                variant="body2" 
                                fontWeight="600" 
                                sx={{ 
                                  textAlign: 'center',
                                  wordBreak: 'break-word',
                                  px: 1,
                                }}
                              >
                                {etapa.etapa_label}
                              </Typography>
                            </Box>
                            
                            {/* Información inferior */}
                            <Box sx={{ width: '100%', mt: 1 }}>
                              {etapa.fecha_inicio && (
                                <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                  {new Date(etapa.fecha_inicio).toLocaleTimeString('es-CL', { 
                                    hour: '2-digit', 
                                    minute: '2-digit' 
                                  })}
                                </Typography>
                              )}
                              {etapa.es_actual && (
                                <Chip
                                  label="En curso"
                                  size="small"
                                  sx={{ 
                                    mt: 1, 
                                    bgcolor: 'white', 
                                    color: 'primary.main',
                                    fontWeight: 600,
                                    fontSize: '0.65rem',
                                    height: '20px',
                                  }}
                                />
                              )}
                              {etapa.estado === 'COMPLETADA' && etapa.fecha_fin && (
                                <Typography variant="caption" display="block" sx={{ mt: 0.5, fontSize: '0.7rem' }}>
                                  ✓ Completada
                                </Typography>
                              )}
                              {etapa.estado === 'PENDIENTE' && (
                                <Typography variant="caption" display="block" sx={{ mt: 0.5, opacity: 0.7, fontSize: '0.7rem' }}>
                                  Pendiente
                                </Typography>
                              )}
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>

                {/* Botones de control */}
                <Stack direction="row" spacing={2} justifyContent="center">
                  <Button
                    variant="outlined"
                    startIcon={<ArrowBackIcon />}
                    onClick={handleRetrocederEtapa}
                    disabled={!puedeRetroceder() || actionLoading}
                    sx={{ minWidth: 150 }}
                  >
                    Retroceder
                  </Button>
                  <Button
                    variant="contained"
                    endIcon={<ArrowForwardIcon />}
                    onClick={handleAvanzarEtapa}
                    disabled={!puedeAvanzar() || actionLoading}
                    sx={{ minWidth: 150 }}
                  >
                    {actionLoading ? 'Procesando...' : 'Avanzar Etapa'}
                  </Button>
                </Stack>

                {/* Información adicional */}
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 4, flexWrap: 'wrap' }}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Etapas completadas:</strong> {rutaClinica.etapas_completadas} de {rutaClinica.etapas_totales}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Tiempo transcurrido:</strong> {Math.floor(rutaClinica.tiempo_transcurrido_minutos / 60)}h {rutaClinica.tiempo_transcurrido_minutos % 60}m
                  </Typography>
                  <Chip
                    label={rutaClinica.ruta_clinica.estado_display}
                    color={rutaClinica.ruta_clinica.estado === 'COMPLETADA' ? 'success' : 'primary'}
                    size="small"
                  />
                </Box>
              </Box>
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
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default DetallePaciente;
