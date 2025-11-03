// frontend/src/components/MedicoConsultas.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Grid,
  Chip,
  Divider,
  Alert,
  CircularProgress,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Cancel as CancelIcon,
  AccessTime as ClockIcon,
  Person as PersonIcon,
  MeetingRoom as BoxIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { medicoAtencionesService } from '../services/api';
import Navbar from './Navbar';

const MedicoConsultas = () => {
  // Estados
  const [atencionActual, setAtencionActual] = useState(null);
  const [tipoAtencion, setTipoAtencion] = useState(null); // 'en_curso', 'proxima', 'ninguna'
  const [loading, setLoading] = useState(true);
  const [tiempoTranscurrido, setTiempoTranscurrido] = useState(0);
  const [atencionesHoy, setAtencionesHoy] = useState([]);
  const [estadisticasHoy, setEstadisticasHoy] = useState(null);
  
  // Diálogos
  const [dialogFinalizar, setDialogFinalizar] = useState(false);
  const [dialogNoPresentado, setDialogNoPresentado] = useState(false);
  const [observaciones, setObservaciones] = useState('');
  
  // Snackbar
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Cargar atención actual
  const cargarAtencionActual = useCallback(async () => {
    try {
      const response = await medicoAtencionesService.getActual();
      setAtencionActual(response.data.atencion);
      setTipoAtencion(response.data.tipo);
      setLoading(false);
    } catch (error) {
      console.error('Error al cargar atención actual:', error);
      showSnackbar('Error al cargar la atención actual', 'error');
      setLoading(false);
    }
  }, []);

  // Cargar atenciones del día
  const cargarAtencionesHoy = useCallback(async () => {
    try {
      const response = await medicoAtencionesService.getHoy();
      setAtencionesHoy(response.data.atenciones);
      setEstadisticasHoy({
        total: response.data.total,
        completadas: response.data.completadas,
        pendientes: response.data.pendientes,
      });
    } catch (error) {
      console.error('Error al cargar atenciones del día:', error);
    }
  }, []);

  // Efecto para cargar datos iniciales
  useEffect(() => {
    cargarAtencionActual();
    cargarAtencionesHoy();
    
    // Recargar cada 30 segundos
    const interval = setInterval(() => {
      cargarAtencionActual();
      cargarAtencionesHoy();
    }, 30000);
    
    return () => clearInterval(interval);
  }, [cargarAtencionActual, cargarAtencionesHoy]);

  // Cronómetro automático
  useEffect(() => {
    let interval = null;
    
    if (tipoAtencion === 'en_curso' && atencionActual?.inicio_cronometro) {
      interval = setInterval(() => {
        const inicio = new Date(atencionActual.inicio_cronometro);
        const ahora = new Date();
        const diff = Math.floor((ahora - inicio) / 1000);
        setTiempoTranscurrido(diff);
      }, 1000);
    } else {
      setTiempoTranscurrido(0);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [tipoAtencion, atencionActual]);

  // Funciones auxiliares
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const formatearTiempo = (segundos) => {
    const horas = Math.floor(segundos / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const segs = segundos % 60;
    return `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
  };

  const calcularProgreso = () => {
    if (!atencionActual?.duracion_planificada) return 0;
    const minutos = tiempoTranscurrido / 60;
    return Math.min((minutos / atencionActual.duracion_planificada) * 100, 100);
  };

  const getColorProgreso = () => {
    const progreso = calcularProgreso();
    if (progreso < 70) return 'success';
    if (progreso < 90) return 'warning';
    return 'error';
  };

  // Acciones
  const handleIniciarAtencion = async () => {
    if (!atencionActual) return;
    
    try {
      const response = await medicoAtencionesService.iniciar(atencionActual.id);
      if (response.data.success) {
        showSnackbar('Atención iniciada correctamente', 'success');
        await cargarAtencionActual();
        await cargarAtencionesHoy();
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al iniciar la atención';
      showSnackbar(errorMsg, 'error');
    }
  };

  const handleFinalizarAtencion = async () => {
    if (!atencionActual) return;
    
    try {
      const response = await medicoAtencionesService.finalizar(
        atencionActual.id,
        observaciones ? { observaciones } : {}
      );
      
      if (response.data.success) {
        showSnackbar('Atención finalizada correctamente', 'success');
        setDialogFinalizar(false);
        setObservaciones('');
        await cargarAtencionActual();
        await cargarAtencionesHoy();
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al finalizar la atención';
      showSnackbar(errorMsg, 'error');
    }
  };

  const handleNoPresentado = async () => {
    if (!atencionActual) return;
    
    try {
      const response = await medicoAtencionesService.noPresentado(
        atencionActual.id,
        observaciones ? { observaciones } : {}
      );
      
      if (response.data.success) {
        showSnackbar('Paciente marcado como no presentado', 'info');
        setDialogNoPresentado(false);
        setObservaciones('');
        await cargarAtencionActual();
        await cargarAtencionesHoy();
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al marcar no presentado';
      showSnackbar(errorMsg, 'error');
    }
  };

  // Render
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" fontWeight="700" gutterBottom>
            Mis Consultas
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Gestiona tus atenciones médicas en tiempo real
          </Typography>
        </Box>

        {/* Estadísticas del día */}
        {estadisticasHoy && (
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Hoy
                  </Typography>
                  <Typography variant="h4" fontWeight="600">
                    {estadisticasHoy.total}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Completadas
                  </Typography>
                  <Typography variant="h4" fontWeight="600" color="success.main">
                    {estadisticasHoy.completadas}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Pendientes
                  </Typography>
                  <Typography variant="h4" fontWeight="600" color="warning.main">
                    {estadisticasHoy.pendientes}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Grid container spacing={3}>
          {/* Panel Principal - Atención Actual */}
          <Grid item xs={12} lg={8}>
            <Card elevation={3} sx={{ minHeight: 500 }}>
              <CardContent>
                {tipoAtencion === 'ninguna' && (
                  <Box sx={{ textAlign: 'center', py: 8 }}>
                    <ScheduleIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h5" gutterBottom>
                      No hay atenciones programadas
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      No tienes atenciones pendientes para hoy
                    </Typography>
                  </Box>
                )}

                {tipoAtencion === 'proxima' && atencionActual && (
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                      <Typography variant="h5" fontWeight="600">
                        Próxima Atención
                      </Typography>
                      <Chip label="Programada" color="primary" />
                    </Box>

                    <Paper sx={{ p: 3, bgcolor: 'grey.50', mb: 3 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <PersonIcon color="primary" />
                            <Typography variant="subtitle2" color="text.secondary">
                              Paciente
                            </Typography>
                          </Box>
                          <Typography variant="h6">
                            {atencionActual.paciente_info?.identificador_hash || 'Paciente'}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <BoxIcon color="primary" />
                            <Typography variant="subtitle2" color="text.secondary">
                              Box
                            </Typography>
                          </Box>
                          <Typography variant="h6">
                            {atencionActual.box_info?.numero || 'Sin box'}
                          </Typography>
                        </Grid>
                      </Grid>
                      <Divider sx={{ my: 2 }} />
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">
                            Hora programada
                          </Typography>
                          <Typography variant="h6">
                            {new Date(atencionActual.fecha_hora_inicio).toLocaleTimeString('es-CL', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" color="text.secondary">
                            Duración planificada
                          </Typography>
                          <Typography variant="h6">
                            {atencionActual.duracion_planificada} minutos
                          </Typography>
                        </Grid>
                      </Grid>
                    </Paper>

                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Button
                        variant="contained"
                        size="large"
                        fullWidth
                        startIcon={<PlayIcon />}
                        onClick={handleIniciarAtencion}
                        sx={{ py: 2 }}
                      >
                        Iniciar Consulta
                      </Button>
                      <Button
                        variant="outlined"
                        size="large"
                        startIcon={<CancelIcon />}
                        onClick={() => setDialogNoPresentado(true)}
                        sx={{ py: 2 }}
                      >
                        No se presentó
                      </Button>
                    </Box>
                  </Box>
                )}

                {tipoAtencion === 'en_curso' && atencionActual && (
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                      <Typography variant="h5" fontWeight="600">
                        Atención en Curso
                      </Typography>
                      <Chip label="En Curso" color="success" icon={<ClockIcon />} />
                    </Box>

                    {/* Cronómetro */}
                    <Paper
                      elevation={0}
                      sx={{
                        p: 4,
                        bgcolor: 'primary.main',
                        color: 'white',
                        textAlign: 'center',
                        mb: 3,
                        borderRadius: 2,
                      }}
                    >
                      <Typography variant="h2" fontWeight="700" sx={{ fontFamily: 'monospace', mb: 2 }}>
                        {formatearTiempo(tiempoTranscurrido)}
                      </Typography>
                      <Typography variant="body1">
                        Duración planificada: {atencionActual.duracion_planificada} minutos
                      </Typography>
                      <Box sx={{ mt: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={calcularProgreso()}
                          color={getColorProgreso()}
                          sx={{
                            height: 8,
                            borderRadius: 1,
                            bgcolor: 'rgba(255, 255, 255, 0.3)',
                          }}
                        />
                      </Box>
                    </Paper>

                    {/* Información del paciente */}
                    <Paper sx={{ p: 3, bgcolor: 'grey.50', mb: 3 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <PersonIcon color="primary" />
                            <Typography variant="subtitle2" color="text.secondary">
                              Paciente
                            </Typography>
                          </Box>
                          <Typography variant="h6">
                            {atencionActual.paciente_info?.identificador_hash || 'Paciente'}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <BoxIcon color="primary" />
                            <Typography variant="subtitle2" color="text.secondary">
                              Box
                            </Typography>
                          </Box>
                          <Typography variant="h6">
                            {atencionActual.box_info?.numero || 'Sin box'}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Paper>

                    {/* Botón finalizar */}
                    <Button
                      variant="contained"
                      color="error"
                      size="large"
                      fullWidth
                      startIcon={<StopIcon />}
                      onClick={() => setDialogFinalizar(true)}
                      sx={{ py: 2 }}
                    >
                      Finalizar Consulta
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Panel Lateral - Lista de Atenciones */}
          <Grid item xs={12} lg={4}>
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  Atenciones de Hoy
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {atencionesHoy.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                    No hay atenciones programadas
                  </Typography>
                ) : (
                  <Box sx={{ maxHeight: 600, overflowY: 'auto' }}>
                    {atencionesHoy.map((atencion) => (
                      <Paper
                        key={atencion.id}
                        sx={{
                          p: 2,
                          mb: 2,
                          borderLeft: '4px solid',
                          borderLeftColor:
                            atencion.estado === 'COMPLETADA'
                              ? 'success.main'
                              : atencion.estado === 'EN_CURSO'
                              ? 'primary.main'
                              : 'warning.main',
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle2" fontWeight="600">
                            {new Date(atencion.fecha_hora_inicio).toLocaleTimeString('es-CL', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </Typography>
                          <Chip
                            label={atencion.estado_display}
                            size="small"
                            color={
                              atencion.estado === 'COMPLETADA'
                                ? 'success'
                                : atencion.estado === 'EN_CURSO'
                                ? 'primary'
                                : 'default'
                            }
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {atencion.paciente_hash}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {atencion.box_numero} • {atencion.duracion_planificada} min
                        </Typography>
                      </Paper>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Diálogo Finalizar */}
        <Dialog open={dialogFinalizar} onClose={() => setDialogFinalizar(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Finalizar Consulta</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Observaciones finales (opcional)"
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogFinalizar(false)}>Cancelar</Button>
            <Button onClick={handleFinalizarAtencion} variant="contained">
              Finalizar
            </Button>
          </DialogActions>
        </Dialog>

        {/* Diálogo No Presentado */}
        <Dialog open={dialogNoPresentado} onClose={() => setDialogNoPresentado(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Paciente No se Presentó</DialogTitle>
          <DialogContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Esta acción marcará la atención como "No se presentó" y liberará el box.
            </Alert>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Observaciones (opcional)"
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogNoPresentado(false)}>Cancelar</Button>
            <Button onClick={handleNoPresentado} variant="contained" color="warning">
              Confirmar
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </>
  );
};

export default MedicoConsultas;