// frontend/src/components/DetallePaciente.jsx - VERSIÓN MEJORADA CON RETRASOS
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
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
  Warning as WarningIcon,
  AccessTime as TimeIcon,
  History as HistoryIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { pacientesService, rutasClinicasService } from '../services/api';
import Navbar from './Navbar';

const DetallePaciente = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [paciente, setPaciente] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  
  // Estados para diálogos
  const [dialogObservaciones, setDialogObservaciones] = useState(false);
  const [observaciones, setObservaciones] = useState('');
  const [dialogHistorial, setDialogHistorial] = useState(false);
  const [expandedEtapa, setExpandedEtapa] = useState(null);

  useEffect(() => {
    cargarDatos();
    // Actualizar cada 30 segundos para detectar retrasos en tiempo real
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
        // Usar el nuevo endpoint de timeline que incluye retrasos
        const timelineRes = await rutasClinicasService.getTimeline(rutaActual.id);
        setRutaClinica(timelineRes.data);
        
        // Cargar historial
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
    // Abrir diálogo para agregar observaciones
    setDialogObservaciones(true);
  };

  const handleAvanzarConObservaciones = async () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return;

    try {
      setActionLoading(true);
      setError('');
      setSuccess('');
      
      // Llamar al endpoint mejorado que acepta observaciones
      const response = await rutasClinicasService.avanzar(
        rutaClinica.ruta_clinica.id, 
        { observaciones: observaciones }
      );
      
      if (response.success) {
        setSuccess(response.mensaje);
        setDialogObservaciones(false);
        setObservaciones('');
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
      
      const motivo = prompt('¿Motivo del retroceso?');
      if (!motivo) return;
      
      const response = await rutasClinicasService.retroceder(
        rutaClinica.ruta_clinica.id,
        { motivo }
      );
      
      if (response.success) {
        setSuccess(response.mensaje);
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

  const getEtapaColor = (estado, retrasada) => {
    // Priorizar el color rojo si está retrasada
    if (retrasada) return { bg: '#ff5252', color: 'white' };
    if (estado === 'COMPLETADA') return { bg: '#4caf50', color: 'white' };
    if (estado === 'EN_PROCESO') return { bg: '#2196f3', color: 'white' };
    return { bg: '#e0e0e0', color: '#666' };
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
    return rutaClinica.ruta_clinica.estado !== 'COMPLETADA';
  };

  const puedeRetroceder = () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return false;
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

        {/* NUEVO: Alertas de Retraso */}
        {rutaClinica?.alertas && rutaClinica.alertas.length > 0 && (
          <Box sx={{ mb: 3 }}>
            {rutaClinica.alertas.map((alerta, index) => (
              <Alert 
                key={index} 
                severity={alerta.severidad}
                icon={alerta.tipo === 'retraso' ? <WarningIcon /> : undefined}
                sx={{ mb: 1 }}
              >
                <strong>{alerta.tipo.toUpperCase()}:</strong> {alerta.mensaje}
              </Alert>
            ))}
          </Box>
        )}

        {/* Card Principal del Paciente */}
        <Card elevation={3} sx={{ mb: 3 }}>
          <CardContent>
            {/* Header con información básica */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 4 }}>
              <Box sx={{ display: 'flex', gap: 3 }}>
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
              
              {/* NUEVO: Botón de Historial */}
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

            {/* Proceso de Atención - Etapas MEJORADAS */}
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

                {/* Grid de etapas con indicadores de retraso */}
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  {rutaClinica.timeline.map((etapa) => {
                    const colors = getEtapaColor(etapa.estado, etapa.retrasada);
                    const isExpanded = expandedEtapa === etapa.orden;
                    
                    return (
                      <Grid item xs={12} sm={6} md={2} key={etapa.orden}>
                        <Card
                          variant="outlined"
                          sx={{
                            bgcolor: colors.bg,
                            color: colors.color,
                            borderWidth: etapa.es_actual ? 3 : 1,
                            borderColor: etapa.es_actual ? 'primary.dark' : 
                                        etapa.retrasada ? 'error.main' : 'divider',
                            transition: 'all 0.3s',
                            height: '100%',
                            minHeight: '220px',
                            display: 'flex',
                            flexDirection: 'column',
                            position: 'relative',
                            '&:hover': {
                              transform: etapa.observaciones ? 'translateY(-4px)' : 'none',
                              boxShadow: etapa.observaciones ? 3 : 'none',
                            },
                          }}
                        >
                          {/* NUEVO: Badge de RETRASADA */}
                          {etapa.retrasada && (
                            <Box sx={{ 
                              position: 'absolute', 
                              top: 8, 
                              right: 8,
                              bgcolor: 'error.main',
                              color: 'white',
                              borderRadius: 1,
                              px: 1,
                              py: 0.5,
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              boxShadow: 2,
                            }}>
                              RETRASADA
                            </Box>
                          )}
                          
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
                            
                            {/* Nombre de etapa */}
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
                            
                            {/* Información inferior MEJORADA */}
                            <Box sx={{ width: '100%', mt: 1 }}>
                              {/* Hora de inicio */}
                              {etapa.fecha_inicio && (
                                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, mb: 0.5 }}>
                                  <TimeIcon sx={{ fontSize: 14 }} />
                                  <Typography variant="caption">
                                    {new Date(etapa.fecha_inicio).toLocaleTimeString('es-CL', { 
                                      hour: '2-digit', 
                                      minute: '2-digit' 
                                    })}
                                  </Typography>
                                </Box>
                              )}
                              
                              {/* NUEVO: Duración con indicador de retraso */}
                              {etapa.duracion_real && (
                                <Typography variant="caption" display="block" sx={{ 
                                  fontWeight: etapa.retrasada ? 700 : 400,
                                  color: etapa.retrasada ? 'error.light' : 'inherit'
                                }}>
                                  Duración: {etapa.duracion_real} min
                                  {etapa.retrasada && ` (+${etapa.duracion_real - etapa.duracion_estimada})`}
                                </Typography>
                              )}
                              
                              {/* Duración estimada para etapas pendientes */}
                              {!etapa.duracion_real && etapa.duracion_estimada && (
                                <Typography variant="caption" display="block" sx={{ opacity: 0.8 }}>
                                  Estimado: {etapa.duracion_estimada} min
                                </Typography>
                              )}
                              
                              {/* Estado actual */}
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
                              {etapa.estado === 'COMPLETADA' && (
                                <Typography variant="caption" display="block" sx={{ mt: 0.5, fontSize: '0.7rem' }}>
                                  ✓ Completada
                                </Typography>
                              )}
                              {etapa.estado === 'PENDIENTE' && (
                                <Typography variant="caption" display="block" sx={{ mt: 0.5, opacity: 0.7, fontSize: '0.7rem' }}>
                                  Pendiente
                                </Typography>
                              )}
                              
                              {/* NUEVO: Botón para ver observaciones */}
                              {etapa.observaciones && (
                                <IconButton
                                  size="small"
                                  onClick={() => setExpandedEtapa(isExpanded ? null : etapa.orden)}
                                  sx={{ mt: 0.5, color: 'inherit' }}
                                >
                                  <ExpandMoreIcon sx={{ 
                                    fontSize: 18,
                                    transform: isExpanded ? 'rotate(180deg)' : 'rotate(0)',
                                    transition: '0.3s' 
                                  }} />
                                </IconButton>
                              )}
                            </Box>
                            
                            {/* NUEVO: Observaciones expandibles */}
                            {etapa.observaciones && (
                              <Collapse in={isExpanded} sx={{ width: '100%' }}>
                                <Box sx={{ 
                                  mt: 1, 
                                  p: 1, 
                                  bgcolor: 'rgba(0,0,0,0.1)', 
                                  borderRadius: 1,
                                  textAlign: 'left'
                                }}>
                                  <Typography variant="caption" fontWeight="600" display="block">
                                    Observaciones:
                                  </Typography>
                                  <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                    {etapa.observaciones}
                                  </Typography>
                                </Box>
                              </Collapse>
                            )}
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

                {/* Información adicional MEJORADA */}
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
                  {/* NUEVO: Indicador de retrasos */}
                  {rutaClinica.retrasos && rutaClinica.retrasos.length > 0 && (
                    <Chip
                      icon={<WarningIcon />}
                      label={`${rutaClinica.retrasos.length} ${rutaClinica.retrasos.length === 1 ? 'retraso' : 'retrasos'} detectado${rutaClinica.retrasos.length === 1 ? '' : 's'}`}
                      color="error"
                      size="small"
                    />
                  )}
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

        {/* NUEVO: Diálogo de Observaciones */}
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
                placeholder="Ej: Paciente presenta mejoría, derivado a laboratorio para exámenes complementarios"
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
              {actionLoading ? 'Procesando...' : 'Avanzar con Observaciones'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* NUEVO: Diálogo de Historial */}
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