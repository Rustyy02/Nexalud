// frontend/src/components/MedicoConsultas.jsx - VERSIÓN CORREGIDA
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Snackbar,
  Stack,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Cancel as CancelIcon,
  AccessTime as ClockIcon,
  Person as PersonIcon,
  MeetingRoom as BoxIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Timer as TimerIcon,
  EventNote as EventIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { medicoAtencionesService } from '../services/api';
import Navbar from './Navbar';

const MedicoConsultas = () => {
  // Estados principales
  const [atencionActual, setAtencionActual] = useState(null);
  const [tipoAtencion, setTipoAtencion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [atencionesHoy, setAtencionesHoy] = useState([]);
  const [estadisticasHoy, setEstadisticasHoy] = useState(null);
  
  // Estados de cronómetro
  const [tiempoRestante, setTiempoRestante] = useState(0);
  const [tiempoTranscurrido, setTiempoTranscurrido] = useState(0);
  
  // Estados de diálogos
  const [dialogFinalizar, setDialogFinalizar] = useState(false);
  const [dialogNoPresentado, setDialogNoPresentado] = useState(false);
  const [dialogAtraso, setDialogAtraso] = useState(false);
  const [observaciones, setObservaciones] = useState('');
  const [motivoAtraso, setMotivoAtraso] = useState('');
  
  // Snackbar
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'success' 
  });

  // ==================== FUNCIONES DE CARGA ====================
  
  const cargarAtencionActual = useCallback(async () => {
    try {
      const response = await medicoAtencionesService.getActual();
      console.log('Atención actual:', response.data); // Debug
      setAtencionActual(response.data.atencion);
      setTipoAtencion(response.data.tipo);
      setLoading(false);
    } catch (error) {
      console.error('Error al cargar atención actual:', error);
      showSnackbar('Error al cargar la atención actual', 'error');
      setLoading(false);
    }
  }, []);

  const cargarAtencionesHoy = useCallback(async () => {
    try {
      const response = await medicoAtencionesService.getHoy();
      console.log('Respuesta de atenciones hoy:', response.data); // Debug
      
      // Asegurarse de que sea un array
      const atenciones = Array.isArray(response.data.atenciones) 
        ? response.data.atenciones 
        : [];
      
      console.log('Atenciones procesadas:', atenciones); // Debug
      
      setAtencionesHoy(atenciones);
      setEstadisticasHoy({
        total: response.data.total || atenciones.length,
        completadas: response.data.completadas || 0,
        pendientes: response.data.pendientes || 0,
      });
    } catch (error) {
      console.error('Error al cargar atenciones del día:', error);
      setAtencionesHoy([]);
    }
  }, []);

  // ==================== EFECTOS ====================
  
  // Cargar datos iniciales y actualizar periódicamente
  useEffect(() => {
    console.log('Componente montado, cargando datos...'); // Debug
    cargarAtencionActual();
    cargarAtencionesHoy();
    
    const interval = setInterval(() => {
      console.log('Actualizando datos automáticamente...'); // Debug
      cargarAtencionActual();
      cargarAtencionesHoy();
    }, 10000); // Cada 10 segundos (más frecuente para testing)
    
    return () => {
      console.log('Limpiando intervalo...'); // Debug
      clearInterval(interval);
    };
  }, []); // Array vacío para que solo se ejecute al montar

  // Cronómetro automático
  useEffect(() => {
    let interval = null;
    
    if (tipoAtencion === 'en_curso' && atencionActual?.inicio_cronometro) {
      interval = setInterval(() => {
        const inicio = new Date(atencionActual.inicio_cronometro);
        const ahora = new Date();
        const transcurrido = Math.floor((ahora - inicio) / 1000);
        const duracionTotal = atencionActual.duracion_planificada * 60;
        const restante = Math.max(0, duracionTotal - transcurrido);
        
        setTiempoTranscurrido(transcurrido);
        setTiempoRestante(restante);
      }, 1000);
    } else if (tipoAtencion === 'proxima' && atencionActual?.fecha_hora_inicio) {
      interval = setInterval(() => {
        const ahora = new Date();
        const inicio = new Date(atencionActual.fecha_hora_inicio);
        const diferencia = Math.floor((inicio - ahora) / 1000);
        
        if (diferencia <= 0) {
          setTiempoRestante(atencionActual.duracion_planificada * 60);
          cargarAtencionActual();
        } else {
          setTiempoRestante(atencionActual.duracion_planificada * 60);
        }
        setTiempoTranscurrido(0);
      }, 1000);
    } else {
      setTiempoTranscurrido(0);
      setTiempoRestante(0);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [tipoAtencion, atencionActual, cargarAtencionActual]);

  // ==================== FUNCIONES AUXILIARES ====================
  
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const formatearTiempo = (segundos) => {
    const horas = Math.floor(segundos / 3600);
    const minutos = Math.floor((segundos % 3600) / 60);
    const segs = segundos % 60;
    
    if (horas > 0) {
      return `${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
    }
    return `${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
  };

  const formatearHora = (fechaStr) => {
    if (!fechaStr) return '--:--';
    const fecha = new Date(fechaStr);
    return fecha.toLocaleTimeString('es-CL', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calcularProgreso = () => {
    if (!atencionActual?.duracion_planificada || tipoAtencion !== 'en_curso') return 0;
    const duracionTotal = atencionActual.duracion_planificada * 60;
    const progreso = (tiempoTranscurrido / duracionTotal) * 100;
    return Math.min(progreso, 100);
  };

  const getColorProgreso = () => {
    const progreso = calcularProgreso();
    if (progreso < 80) return 'success';
    if (progreso < 100) return 'warning';
    return 'error';
  };

  const estaRetrasada = () => {
    if (tipoAtencion !== 'en_curso') return false;
    return tiempoRestante <= 0;
  };

  const calcularMinutosHastaInicio = () => {
    if (!atencionActual?.fecha_hora_inicio) return 0;
    const ahora = new Date();
    const inicio = new Date(atencionActual.fecha_hora_inicio);
    const diferencia = Math.floor((inicio - ahora) / (1000 * 60));
    return Math.max(0, diferencia);
  };

  // ==================== ACCIONES ====================
  
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

  const handleReportarAtraso = () => {
    setDialogAtraso(true);
  };

  const confirmarReporteAtraso = () => {
    showSnackbar(`Atraso reportado: ${motivoAtraso}`, 'warning');
    setDialogAtraso(false);
    setMotivoAtraso('');
  };

  const handleRefrescar = async () => {
    console.log('Refrescando datos manualmente...'); // Debug
    setLoading(true);
    await Promise.all([cargarAtencionActual(), cargarAtencionesHoy()]);
    setLoading(false);
    showSnackbar('Datos actualizados', 'info');
  };

  // ==================== RENDER ====================
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Header con botón refrescar */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" fontWeight="700" gutterBottom>
              Mis Consultas
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Gestiona tus atenciones médicas en tiempo real
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefrescar}
          >
            Actualizar
          </Button>
        </Box>

        {/* Debug info - REMOVER EN PRODUCCIÓN */}
        {process.env.NODE_ENV === 'development' && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Debug: {atencionesHoy.length} atenciones cargadas. 
            Última actualización: {new Date().toLocaleTimeString()}
          </Alert>
        )}

        {/* Estadísticas del día */}
        {estadisticasHoy && (
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={4}>
              <Card sx={{ 
                bgcolor: 'primary.main', 
                color: 'white',
                height: '100%'
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <EventIcon sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h3" fontWeight="700">
                        {estadisticasHoy.total}
                      </Typography>
                      <Typography variant="body2">
                        Atenciones Hoy
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card sx={{ 
                bgcolor: 'success.main', 
                color: 'white',
                height: '100%'
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <CheckIcon sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h3" fontWeight="700">
                        {estadisticasHoy.completadas}
                      </Typography>
                      <Typography variant="body2">
                        Completadas
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card sx={{ 
                bgcolor: 'warning.main', 
                color: 'white',
                height: '100%'
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <ClockIcon sx={{ fontSize: 40 }} />
                    <Box>
                      <Typography variant="h3" fontWeight="700">
                        {estadisticasHoy.pendientes}
                      </Typography>
                      <Typography variant="body2">
                        Pendientes
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Grid container spacing={3}>
          {/* PANEL PRINCIPAL - CRONÓMETRO Y ATENCIÓN ACTUAL */}
          <Grid item xs={12} lg={6}>
            <Card 
              elevation={4} 
              sx={{ 
                minHeight: 500,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
              }}
            >
              <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                
                {/* SIN ATENCIONES */}
                {tipoAtencion === 'ninguna' && (
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column',
                    alignItems: 'center', 
                    justifyContent: 'center',
                    flex: 1,
                    textAlign: 'center',
                    py: 8 
                  }}>
                    <ClockIcon sx={{ fontSize: 100, mb: 3, opacity: 0.7 }} />
                    <Typography variant="h4" fontWeight="600" gutterBottom>
                      Sin Atenciones Programadas
                    </Typography>
                    <Typography variant="body1" sx={{ opacity: 0.9 }}>
                      No tienes consultas pendientes para hoy
                    </Typography>
                  </Box>
                )}

                {/* ATENCIÓN PRÓXIMA */}
                {tipoAtencion === 'proxima' && atencionActual && (
                  <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ mb: 3 }}>
                      <Chip 
                        label="PRÓXIMA ATENCIÓN" 
                        sx={{ 
                          bgcolor: 'rgba(255,255,255,0.3)',
                          color: 'white',
                          fontWeight: 600,
                          mb: 2
                        }}
                      />
                      <Typography variant="h5" fontWeight="600">
                        Consulta Programada
                      </Typography>
                    </Box>

                    <Paper sx={{ 
                      p: 3, 
                      bgcolor: 'rgba(255,255,255,0.15)',
                      backdropFilter: 'blur(10px)',
                      mb: 3,
                      textAlign: 'center'
                    }}>
                      <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                        Inicia en
                      </Typography>
                      <Typography variant="h3" fontWeight="700">
                        {calcularMinutosHastaInicio()} min
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1, opacity: 0.9 }}>
                        Hora programada: {formatearHora(atencionActual.fecha_hora_inicio)}
                      </Typography>
                    </Paper>

                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6}>
                        <Paper sx={{ 
                          p: 2, 
                          bgcolor: 'rgba(255,255,255,0.15)',
                          backdropFilter: 'blur(10px)',
                        }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <PersonIcon />
                            <Typography variant="caption">PACIENTE</Typography>
                          </Box>
                          <Typography variant="h6" fontWeight="600">
                            {atencionActual.paciente_info?.identificador_hash?.substring(0, 12) || 'Paciente'}
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6}>
                        <Paper sx={{ 
                          p: 2, 
                          bgcolor: 'rgba(255,255,255,0.15)',
                          backdropFilter: 'blur(10px)',
                        }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <BoxIcon />
                            <Typography variant="caption">BOX</Typography>
                          </Box>
                          <Typography variant="h6" fontWeight="600">
                            {atencionActual.box_info?.numero || 'Sin box'}
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>

                    <Paper sx={{ 
                      p: 2, 
                      bgcolor: 'rgba(255,255,255,0.15)',
                      backdropFilter: 'blur(10px)',
                      mb: 3,
                      textAlign: 'center'
                    }}>
                      <TimerIcon sx={{ fontSize: 30, mb: 1 }} />
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Duración Planificada
                      </Typography>
                      <Typography variant="h5" fontWeight="600">
                        {atencionActual.duracion_planificada} minutos
                      </Typography>
                    </Paper>

                    <Box sx={{ mt: 'auto' }}>
                      <Stack spacing={2}>
                        <Button
                          variant="contained"
                          size="large"
                          fullWidth
                          startIcon={<PlayIcon />}
                          onClick={handleIniciarAtencion}
                          disabled={calcularMinutosHastaInicio() > 15}
                          sx={{ 
                            py: 2,
                            bgcolor: 'white',
                            color: 'primary.main',
                            '&:hover': {
                              bgcolor: 'rgba(255,255,255,0.9)',
                            }
                          }}
                        >
                          {calcularMinutosHastaInicio() > 15 
                            ? `Disponible en ${calcularMinutosHastaInicio()} min`
                            : 'INICIAR CONSULTA'
                          }
                        </Button>
                        <Button
                          variant="outlined"
                          size="large"
                          fullWidth
                          startIcon={<CancelIcon />}
                          onClick={() => setDialogNoPresentado(true)}
                          sx={{ 
                            color: 'white',
                            borderColor: 'white',
                            '&:hover': {
                              borderColor: 'white',
                              bgcolor: 'rgba(255,255,255,0.1)',
                            }
                          }}
                        >
                          NO SE PRESENTÓ
                        </Button>
                      </Stack>
                    </Box>
                  </Box>
                )}

                {/* ATENCIÓN EN CURSO */}
                {tipoAtencion === 'en_curso' && atencionActual && (
                  <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ mb: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Chip 
                          label="EN CURSO" 
                          icon={<ClockIcon />}
                          sx={{ 
                            bgcolor: estaRetrasada() ? 'error.main' : 'success.main',
                            color: 'white',
                            fontWeight: 600,
                          }}
                        />
                        {estaRetrasada() && (
                          <Chip 
                            icon={<WarningIcon />}
                            label="RETRASADA"
                            color="error"
                          />
                        )}
                      </Box>
                      <Typography variant="h5" fontWeight="600">
                        Consulta Activa
                      </Typography>
                    </Box>

                    <Paper sx={{ 
                      p: 4, 
                      bgcolor: estaRetrasada() ? 'rgba(244,67,54,0.2)' : 'rgba(76,175,80,0.2)',
                      backdropFilter: 'blur(10px)',
                      mb: 3,
                      textAlign: 'center',
                      border: estaRetrasada() ? '2px solid rgba(244,67,54,0.5)' : '2px solid rgba(76,175,80,0.5)',
                    }}>
                      <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                        {estaRetrasada() ? 'TIEMPO EXCEDIDO' : 'TIEMPO RESTANTE'}
                      </Typography>
                      <Typography 
                        variant="h1" 
                        fontWeight="700" 
                        sx={{ 
                          fontFamily: 'monospace',
                          fontSize: '4rem',
                          mb: 1,
                          color: estaRetrasada() ? 'error.light' : 'success.light'
                        }}
                      >
                        {estaRetrasada() 
                          ? `+${formatearTiempo(Math.abs(tiempoRestante))}`
                          : formatearTiempo(tiempoRestante)
                        }
                      </Typography>
                      
                      <Box sx={{ mt: 2, mb: 2 }}>
                        <LinearProgress
                          variant="determinate"
                          value={calcularProgreso()}
                          color={getColorProgreso()}
                          sx={{
                            height: 12,
                            borderRadius: 2,
                            bgcolor: 'rgba(255, 255, 255, 0.3)',
                          }}
                        />
                      </Box>
                      
                      <Typography variant="caption" sx={{ opacity: 0.8 }}>
                        Tiempo transcurrido: {formatearTiempo(tiempoTranscurrido)} / {atencionActual.duracion_planificada} min
                      </Typography>
                    </Paper>

                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid item xs={6}>
                        <Paper sx={{ 
                          p: 2, 
                          bgcolor: 'rgba(255,255,255,0.15)',
                          backdropFilter: 'blur(10px)',
                        }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <PersonIcon />
                            <Typography variant="caption">PACIENTE</Typography>
                          </Box>
                          <Typography variant="h6" fontWeight="600">
                            {atencionActual.paciente_info?.identificador_hash?.substring(0, 12) || 'Paciente'}
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={6}>
                        <Paper sx={{ 
                          p: 2, 
                          bgcolor: 'rgba(255,255,255,0.15)',
                          backdropFilter: 'blur(10px)',
                        }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <BoxIcon />
                            <Typography variant="caption">BOX</Typography>
                          </Box>
                          <Typography variant="h6" fontWeight="600">
                            {atencionActual.box_info?.numero || 'Sin box'}
                          </Typography>
                        </Paper>
                      </Grid>
                    </Grid>

                    <Box sx={{ mt: 'auto' }}>
                      <Stack spacing={2}>
                        <Button
                          variant="contained"
                          size="large"
                          fullWidth
                          startIcon={<StopIcon />}
                          onClick={() => setDialogFinalizar(true)}
                          sx={{ 
                            py: 2,
                            bgcolor: 'white',
                            color: 'error.main',
                            '&:hover': {
                              bgcolor: 'rgba(255,255,255,0.9)',
                            }
                          }}
                        >
                          FINALIZAR CONSULTA
                        </Button>
                        {estaRetrasada() && (
                          <Button
                            variant="outlined"
                            size="large"
                            fullWidth
                            startIcon={<WarningIcon />}
                            onClick={handleReportarAtraso}
                            sx={{ 
                              color: 'white',
                              borderColor: 'white',
                              '&:hover': {
                                borderColor: 'white',
                                bgcolor: 'rgba(255,255,255,0.1)',
                              }
                            }}
                          >
                            REPORTAR ATRASO
                          </Button>
                        )}
                      </Stack>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* PANEL DERECHO - LISTADO DE ATENCIONES */}
          <Grid item xs={12} lg={6}>
            <Card elevation={3} sx={{ minHeight: 500 }}>
              <CardContent>
                <Typography variant="h5" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                  Atenciones de Hoy ({atencionesHoy.length})
                </Typography>
                
                {atencionesHoy.length === 0 ? (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    No hay atenciones programadas para hoy
                  </Alert>
                ) : (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ bgcolor: 'grey.100' }}>
                          <TableCell><strong>Hora</strong></TableCell>
                          <TableCell><strong>Paciente</strong></TableCell>
                          <TableCell><strong>Box</strong></TableCell>
                          <TableCell><strong>Duración</strong></TableCell>
                          <TableCell><strong>Estado</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {atencionesHoy.map((atencion) => (
                          <TableRow 
                            key={atencion.id}
                            sx={{ 
                              '&:hover': { bgcolor: 'grey.50' },
                              bgcolor: atencion.estado === 'EN_CURSO' ? 'success.lighter' : 'inherit'
                            }}
                          >
                            <TableCell>
                              <Typography variant="body2" fontWeight="600">
                                {formatearHora(atencion.fecha_hora_inicio)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {atencion.paciente_hash?.substring(0, 12) || 
                                 atencion.paciente_info?.identificador_hash?.substring(0, 12) || 
                                 'Sin paciente'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip 
                                label={atencion.box_numero || atencion.box_info?.numero || 'Sin box'} 
                                size="small" 
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {atencion.duracion_planificada} min
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={atencion.estado_display}
                                size="small"
                                color={
                                  atencion.estado === 'COMPLETADA' ? 'success' :
                                  atencion.estado === 'EN_CURSO' ? 'primary' :
                                  atencion.estado === 'CANCELADA' ? 'error' :
                                  'default'
                                }
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* DIÁLOGOS */}
        
        {/* Diálogo Finalizar */}
        <Dialog 
          open={dialogFinalizar} 
          onClose={() => setDialogFinalizar(false)} 
          maxWidth="sm" 
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <StopIcon color="error" />
              Finalizar Consulta
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="info" sx={{ mb: 2 }}>
              La atención será marcada como completada y el box será liberado.
            </Alert>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Observaciones finales (opcional)"
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              placeholder="Diagnóstico, tratamiento, indicaciones..."
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogFinalizar(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleFinalizarAtencion} 
              variant="contained"
              color="error"
            >
              Finalizar Consulta
            </Button>
          </DialogActions>
        </Dialog>

        {/* Diálogo No Presentado */}
        <Dialog 
          open={dialogNoPresentado} 
          onClose={() => setDialogNoPresentado(false)} 
          maxWidth="sm" 
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CancelIcon color="warning" />
              Paciente No se Presentó
            </Box>
          </DialogTitle>
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
              placeholder="Motivo o detalles adicionales..."
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogNoPresentado(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleNoPresentado} 
              variant="contained" 
              color="warning"
            >
              Confirmar
            </Button>
          </DialogActions>
        </Dialog>

        {/* Diálogo Reportar Atraso */}
        <Dialog 
          open={dialogAtraso} 
          onClose={() => setDialogAtraso(false)} 
          maxWidth="sm" 
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color="error" />
              Reportar Atraso
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="error" sx={{ mb: 2 }}>
              La consulta ha excedido el tiempo planificado. Por favor, especifica el motivo del atraso.
            </Alert>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Motivo del atraso *"
              value={motivoAtraso}
              onChange={(e) => setMotivoAtraso(e.target.value)}
              placeholder="Ej: Complicaciones en el procedimiento, paciente requirió atención adicional..."
              required
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogAtraso(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={confirmarReporteAtraso} 
              variant="contained" 
              color="error"
              disabled={!motivoAtraso.trim()}
            >
              Reportar
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert 
            onClose={() => setSnackbar({ ...snackbar, open: false })} 
            severity={snackbar.severity}
            variant="filled"
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
};

export default MedicoConsultas;
