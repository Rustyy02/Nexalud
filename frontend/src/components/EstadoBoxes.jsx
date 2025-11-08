// frontend/src/components/EstadoBoxes.jsx - ACTUALIZACIÓN SOLO SECCIÓN ATRASOS
import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  CircularProgress,
  Container,
  Paper,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Tooltip,
  IconButton,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  AccessTime as AccessTimeIcon,
  Person as PersonIcon,
  Sync as SyncIcon,
  Info as InfoIcon,
  MedicalServices as MedicalIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import { boxesService, atencionesService } from '../services/api';
import Navbar from './Navbar';

const EstadoBoxes = () => {
  const [boxes, setBoxes] = useState([]);
  const [atrasosReales, setAtrasosReales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sincronizando, setSincronizando] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  
  const [dialogOcupar, setDialogOcupar] = useState(false);
  const [dialogInfoAtencion, setDialogInfoAtencion] = useState(false);
  const [boxSeleccionado, setBoxSeleccionado] = useState(null);
  const [duracionEstimada, setDuracionEstimada] = useState(30);
  const [motivoOcupacion, setMotivoOcupacion] = useState('');

  // Opciones de duración disponibles
  const duracionesDisponibles = [15, 30, 45, 60, 75, 90, 105, 120];

  useEffect(() => {
    cargarDatos();
    sincronizarEstados();
    
    // Sincronizar cada 30 segundos (ahora incluye liberación de atenciones)
    const intervalSync = setInterval(sincronizarEstados, 30000);
    
    // Recargar datos cada 15 segundos
    const intervalData = setInterval(cargarDatos, 15000);
    
    // Liberar ocupaciones manuales cada 60 segundos
    const intervalLiberar = setInterval(liberarOcupacionesManuales, 60000);
    
    return () => {
      clearInterval(intervalSync);
      clearInterval(intervalData);
      clearInterval(intervalLiberar);
    };
  }, []);

  const sincronizarEstados = async () => {
    try {
      setSincronizando(true);
      const response = await boxesService.sincronizarEstados();
      
      // Log para debugging (puedes comentar esto en producción)
      if (response.data.boxes_actualizados > 0 || response.data.atenciones_finalizadas > 0) {
        console.log('Sincronización:', {
          boxes_actualizados: response.data.boxes_actualizados,
          atenciones_finalizadas: response.data.atenciones_finalizadas,
          timestamp: response.data.timestamp
        });
      }
      
      // Si se finalizaron atenciones, recargar datos inmediatamente
      if (response.data.atenciones_finalizadas > 0) {
        await cargarDatos();
      }
    } catch (err) {
      console.error('Error en sincronización automática:', err);
    } finally {
      setSincronizando(false);
    }
  };

  const liberarOcupacionesManuales = async () => {
    try {
      const response = await boxesService.liberarOcupacionesManuales();
      if (response.data.boxes_liberados > 0) {
        console.log('Ocupaciones manuales liberadas:', response.data.boxes_liberados);
        showSnackbar(
          `${response.data.boxes_liberados} box(es) liberados automáticamente`,
          'info'
        );
        await cargarDatos();
      }
    } catch (err) {
      console.error('Error al liberar ocupaciones manuales:', err);
    }
  };

  const sincronizarManual = async () => {
    try {
      setSincronizando(true);
      const response = await boxesService.sincronizarEstados();
      
      const mensaje = `Sincronización completa: ${response.data.boxes_actualizados} boxes actualizados`;
      const mensajeAtenciones = response.data.atenciones_finalizadas > 0 
        ? `, ${response.data.atenciones_finalizadas} atenciones finalizadas`
        : '';
      
      showSnackbar(mensaje + mensajeAtenciones, 'success');
      await cargarDatos();
    } catch (err) {
      showSnackbar('Error al sincronizar estados', 'error');
      console.error(err);
    } finally {
      setSincronizando(false);
    }
  };

  const cargarDatos = async () => {
    try {
      const [boxesRes, atrasosReportadosRes] = await Promise.all([
        boxesService.getAll(),
        atencionesService.getConAtrasoReportado() // ✅ NUEVO: Usar el endpoint correcto
      ]);
      
      setBoxes(boxesRes.data);
      
      // ✅ NUEVO: Procesar atrasos reportados
      if (atrasosReportadosRes.data && atrasosReportadosRes.data.atenciones) {
        const atrasosFormateados = atrasosReportadosRes.data.atenciones.map(atencion => {
          // Calcular minutos desde el reporte
          const minutosDesdeReporte = atencion.minutos_desde_reporte_atraso || 0;
          
          return {
            id: atencion.id,
            paciente: obtenerNombrePaciente(atencion),
            box: atencion.box_numero || atencion.box_info?.numero || 'Sin box',
            minutosDesdeReporte: minutosDesdeReporte,
            motivoAtraso: atencion.motivo_atraso,
            fechaReporte: atencion.fecha_reporte_atraso,
            atencionId: atencion.id,
            horaInicioProgramada: atencion.fecha_hora_inicio,
            duracionPlanificada: atencion.duracion_planificada,
            // ✅ Calcular tiempo restante hasta marcado automático (5 min)
            tiempoRestanteAutoMarcar: Math.max(0, 5 - minutosDesdeReporte),
          };
        });
        
        setAtrasosReales(atrasosFormateados);
      } else {
        setAtrasosReales([]);
      }
      
      setLoading(false);
    } catch (err) {
      showSnackbar('Error al cargar los datos', 'error');
      setLoading(false);
      console.error(err);
    }
  };

  // ✅ HELPER para obtener nombre del paciente
  const obtenerNombrePaciente = (atencion) => {
    if (!atencion) return 'Sin paciente';
    
    if (atencion.paciente_nombre) {
      return atencion.paciente_nombre;
    }
    
    if (atencion.paciente_info?.nombre_completo) {
      return atencion.paciente_info.nombre_completo;
    }
    
    const pacienteInfo = atencion.paciente_info;
    if (pacienteInfo) {
      const nombre = pacienteInfo.nombres || pacienteInfo.nombre;
      if (nombre) {
        let nombreCompleto = nombre;
        if (pacienteInfo.apellido_paterno) {
          nombreCompleto += ` ${pacienteInfo.apellido_paterno}`;
        }
        if (pacienteInfo.apellido_materno) {
          nombreCompleto += ` ${pacienteInfo.apellido_materno}`;
        }
        return nombreCompleto.trim();
      }
    }
    
    const hash = atencion.paciente_hash || 
                 atencion.paciente_info?.identificador_hash ||
                 atencion.paciente;
    
    if (typeof hash === 'string') {
      return `Paciente ${hash.substring(0, 8)}...`;
    }
    
    return 'Sin identificar';
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const handleAbrirDialogoOcupar = (box) => {
    setBoxSeleccionado(box);
    setDuracionEstimada(30);
    setMotivoOcupacion('');
    setDialogOcupar(true);
  };

  const handleCerrarDialogoOcupar = () => {
    setDialogOcupar(false);
    setBoxSeleccionado(null);
    setMotivoOcupacion('');
  };

  const handleVerInfoAtencion = (box) => {
    setBoxSeleccionado(box);
    setDialogInfoAtencion(true);
  };

  const handleCerrarInfoAtencion = () => {
    setDialogInfoAtencion(false);
    setBoxSeleccionado(null);
  };

  const cambiarEstadoBox = async (box, nuevoEstado) => {
    if (box.ocupado_por_atencion && nuevoEstado === 'DISPONIBLE') {
      showSnackbar(
        'Este box está ocupado por una atención programada. No se puede liberar manualmente.',
        'warning'
      );
      return;
    }

    try {
      if (nuevoEstado === 'OCUPADO') {
        handleAbrirDialogoOcupar(box);
      } else {
        const response = await boxesService.liberar(box.id);
        
        if (response.data.success) {
          showSnackbar(`Box ${box.numero} liberado correctamente`, 'success');
        } else {
          showSnackbar(response.data.mensaje || 'No se pudo liberar el box', 'warning');
        }
        
        await cargarDatos();
      }
    } catch (err) {
      if (err.response && err.response.data && err.response.data.mensaje) {
        showSnackbar(err.response.data.mensaje, 'error');
      } else {
        showSnackbar('Error al cambiar estado del box', 'error');
      }
      console.error(err);
    }
  };

  const confirmarOcuparBox = async () => {
    if (!boxSeleccionado) return;

    try {
      const duracionNumerica = parseInt(duracionEstimada, 10);
      
      const response = await boxesService.ocupar(
        boxSeleccionado.id, 
        duracionNumerica,
        motivoOcupacion || 'Ocupación manual'
      );

      if (response.data.success) {
        showSnackbar(
          `Box ${boxSeleccionado.numero} ocupado por ${duracionNumerica} minutos`,
          'success'
        );
        handleCerrarDialogoOcupar();
        await cargarDatos();
      } else {
        showSnackbar(response.data.mensaje || 'Error al ocupar el box', 'error');
      }
    } catch (err) {
      if (err.response?.data?.error) {
        showSnackbar(err.response.data.error, 'error');
      } else if (err.response?.data?.mensaje) {
        showSnackbar(err.response.data.mensaje, 'error');
      } else {
        showSnackbar('Error al ocupar el box', 'error');
      }
    }
  };

  const iniciarAtencionAtrasada = async (atraso) => {
    try {
      await atencionesService.iniciarCronometro(atraso.atencionId);
      showSnackbar('Atención iniciada correctamente', 'success');
      await cargarDatos();
    } catch (err) {
      showSnackbar('Error al iniciar la atención', 'error');
      console.error(err);
    }
  };

  const notificarProfesional = (atraso) => {
    showSnackbar(`Notificación enviada para box ${atraso.box}`, 'info');
  };

  const getEstadoColor = (estado) => {
    switch (estado) {
      case 'DISPONIBLE':
        return 'success';
      case 'OCUPADO':
        return 'error';
      case 'MANTENIMIENTO':
        return 'warning';
      case 'FUERA_SERVICIO':
        return 'default';
      default:
        return 'default';
    }
  };

  const getEstadoIcon = (box) => {
    if (box.estado === 'DISPONIBLE') return <CheckCircleIcon />;
    if (box.estado === 'OCUPADO') {
      if (box.ocupado_por_atencion) return <MedicalIcon />;
      if (box.ocupacion_manual_activa) return <TimerIcon />;
      return <WarningIcon />;
    }
    return <ScheduleIcon />;
  };

  const formatearHoraAtencion = (box) => {
    if (!box.atencion_actual || !box.atencion_actual.fecha_hora_inicio) {
      return 'Sin horario';
    }
    
    const fecha = new Date(box.atencion_actual.fecha_hora_inicio);
    return fecha.toLocaleTimeString('es-CL', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calcularProgresoOcupacion = (ocupacion) => {
    if (!ocupacion) return 0;
    
    const ahora = new Date();
    const inicio = new Date(ocupacion.fecha_inicio);
    const fin = new Date(ocupacion.fecha_fin_programada);
    
    const duracionTotal = fin - inicio;
    const tiempoTranscurrido = ahora - inicio;
    
    const progreso = (tiempoTranscurrido / duracionTotal) * 100;
    return Math.min(Math.max(progreso, 0), 100);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  const boxesDisponibles = boxes.filter((b) => b.estado === 'DISPONIBLE').length;
  const boxesOcupados = boxes.filter((b) => b.estado === 'OCUPADO').length;
  const boxesMantenimiento = boxes.filter((b) => b.estado === 'MANTENIMIENTO').length;

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" fontWeight="700">
            Estado de Boxes en Tiempo Real
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={sincronizando ? <CircularProgress size={20} /> : <SyncIcon />}
              onClick={sincronizarManual}
              disabled={sincronizando}
            >
              {sincronizando ? 'Sincronizando...' : 'Sincronizar'}
            </Button>
          </Box>
        </Box>

        {/* Estadísticas */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Disponibles
                    </Typography>
                    <Typography variant="h4" fontWeight="600" color="success.main">
                      {boxesDisponibles}
                    </Typography>
                  </Box>
                  <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Ocupados
                    </Typography>
                    <Typography variant="h4" fontWeight="600" color="error.main">
                      {boxesOcupados}
                    </Typography>
                  </Box>
                  <WarningIcon sx={{ fontSize: 48, color: 'error.main', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Mantenimiento
                    </Typography>
                    <Typography variant="h4" fontWeight="600" color="warning.main">
                      {boxesMantenimiento}
                    </Typography>
                  </Box>
                  <ScheduleIcon sx={{ fontSize: 48, color: 'warning.main', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={3}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="text.secondary" gutterBottom>
                      Total
                    </Typography>
                    <Typography variant="h4" fontWeight="600">
                      {boxes.length}
                    </Typography>
                  </Box>
                  <AccessTimeIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Boxes Grid */}
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" fontWeight="600" sx={{ mb: 3 }}>
            Boxes
          </Typography>
          <Grid container spacing={2}>
            {boxes.map((box) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={box.id}>
                <Card
                  elevation={3}
                  sx={{
                    height: '100%',
                    borderLeft: '4px solid',
                    borderLeftColor:
                      box.estado === 'DISPONIBLE'
                        ? 'success.main'
                        : box.estado === 'OCUPADO'
                        ? 'error.main'
                        : 'warning.main',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" fontWeight="600">
                          {box.numero}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {box.nombre}
                        </Typography>
                      </Box>
                      <Chip
                        icon={getEstadoIcon(box)}
                        label={box.estado_display}
                        color={getEstadoColor(box.estado)}
                        size="small"
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      <strong>Especialidad:</strong> {box.especialidad_display}
                    </Typography>

                    {box.ocupado_por_atencion && box.atencion_actual && (
                      <Box sx={{ mt: 2, p: 1.5, bgcolor: 'primary.lighter', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                          <MedicalIcon sx={{ fontSize: 16, color: 'primary.main' }} />
                          <Typography variant="caption" color="primary.main" fontWeight="600">
                            ATENCIÓN EN CURSO
                          </Typography>
                        </Box>
                        <Typography variant="caption" display="block">
                          Paciente: {box.atencion_actual.paciente}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Hora: {formatearHoraAtencion(box)}
                        </Typography>
                      </Box>
                    )}

                    {box.ocupacion_manual_activa && !box.ocupado_por_atencion && (
                      <Box sx={{ mt: 2, p: 1.5, bgcolor: 'warning.lighter', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
                          <TimerIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                          <Typography variant="caption" color="warning.main" fontWeight="600">
                            OCUPACIÓN MANUAL
                          </Typography>
                        </Box>
                        <Typography variant="caption" display="block">
                          Tiempo restante: {Math.round(box.ocupacion_manual_activa.minutos_restantes)} min
                        </Typography>
                        {box.ocupacion_manual_activa.motivo && (
                          <Typography variant="caption" display="block">
                            Motivo: {box.ocupacion_manual_activa.motivo}
                          </Typography>
                        )}
                      </Box>
                    )}

                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      {box.estado === 'DISPONIBLE' ? (
                        <Button
                          variant="contained"
                          fullWidth
                          size="small"
                          onClick={() => cambiarEstadoBox(box, 'OCUPADO')}
                        >
                          Ocupar
                        </Button>
                      ) : box.estado === 'OCUPADO' ? (
                        <>
                          <Button
                            variant="outlined"
                            fullWidth
                            size="small"
                            onClick={() => cambiarEstadoBox(box, 'DISPONIBLE')}
                            disabled={box.ocupado_por_atencion || box.ocupacion_manual_activa}
                          >
                            Liberar
                          </Button>
                          {(box.ocupado_por_atencion || box.ocupacion_manual_activa) && (
                            <Tooltip title="Ver información">
                              <IconButton size="small" onClick={() => handleVerInfoAtencion(box)}>
                                <InfoIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </>
                      ) : null}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* ✅ SECCIÓN DE ATRASOS REPORTADOS - ACTUALIZADA */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h5" fontWeight="600">
                ⚠️ Atrasos Reportados por Médicos
              </Typography>
              {atrasosReales.length > 0 && (
                <Chip 
                  label={`${atrasosReales.length} atraso${atrasosReales.length > 1 ? 's' : ''}`} 
                  color="error" 
                  size="small" 
                />
              )}
            </Box>
          </Box>

          <Alert severity="info" sx={{ mb: 2 }}>
            ℹ️ Los pacientes serán marcados automáticamente como "No se presentó" después de 5 minutos de espera desde el reporte.
          </Alert>

          {atrasosReales.length === 0 ? (
            <Alert severity="success" sx={{ mt: 2 }}>
              ✓ No hay atrasos reportados.
            </Alert>
          ) : (
              <Box sx={{ mt: 2 }}>
                {atrasosReales.map((atraso) => {
                  // ✅ NUEVO: Calcular si mostrar en segundos (cuando queda menos de 1 minuto)
                  const minutosRestantes = Math.floor(atraso.tiempoRestanteAutoMarcar);
                  const segundosRestantes = Math.round((atraso.tiempoRestanteAutoMarcar - minutosRestantes) * 60);
                  const mostrarEnSegundos = atraso.tiempoRestanteAutoMarcar < 1 && atraso.tiempoRestanteAutoMarcar > 0;
                  
                  return (
                    <Card 
                      key={atraso.id} 
                      elevation={1} 
                      sx={{ 
                        mb: 2, 
                        p: 2, 
                        borderLeft: '4px solid',
                        borderLeftColor: atraso.tiempoRestanteAutoMarcar === 0 ? 'error.dark' : 'warning.main',
                        bgcolor: atraso.tiempoRestanteAutoMarcar === 0 ? 'error.lighter' : 'warning.lighter'
                      }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                        <Box sx={{ flex: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <PersonIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                            <Typography variant="subtitle1" fontWeight="600">
                              {atraso.paciente}
                            </Typography>
                            {atraso.tiempoRestanteAutoMarcar === 0 && (
                              <Chip 
                                icon={<WarningIcon />}
                                label="PROCESANDO..." 
                                color="error" 
                                size="small" 
                              />
                            )}
                          </Box>
                          
                          <Typography variant="body2" color="text.secondary">
                            <strong>Box:</strong> {atraso.box}
                          </Typography>
                          
                          <Typography variant="body2" color="text.secondary">
                            <strong>Hora programada:</strong>{' '}
                            {new Date(atraso.horaInicioProgramada).toLocaleTimeString('es-CL', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                            <AccessTimeIcon sx={{ color: 'warning.main', fontSize: 20 }} />
                            <Typography variant="body2" color="warning.main" fontWeight="600">
                              Reportado hace {atraso.minutosDesdeReporte} minuto{atraso.minutosDesdeReporte !== 1 ? 's' : ''}
                            </Typography>
                          </Box>
                          
                          {atraso.motivoAtraso && (
                            <Box sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                <strong>Motivo:</strong> {atraso.motivoAtraso}
                              </Typography>
                            </Box>
                          )}
                          
                          {atraso.tiempoRestanteAutoMarcar > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <TimerIcon sx={{ fontSize: 16, color: 'error.main' }} />
                                <Typography variant="caption" color="error.main" fontWeight="600">
                                  Se marcará como "No se presentó" en{' '}
                                  {mostrarEnSegundos 
                                    ? `${segundosRestantes} segundo${segundosRestantes !== 1 ? 's' : ''}`
                                    : `${minutosRestantes} minuto${minutosRestantes !== 1 ? 's' : ''}`
                                  }
                                </Typography>
                              </Box>
                              <LinearProgress 
                                variant="determinate" 
                                value={((5 - atraso.tiempoRestanteAutoMarcar) / 5) * 100}
                                color="error"
                                sx={{ height: 8, borderRadius: 1 }}
                              />
                            </Box>
                          )}
                        </Box>
                        <Chip label={atraso.box} color="warning" size="small" />
                      </Box>

                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          variant="contained"
                          size="small"
                          fullWidth
                          onClick={() => iniciarAtencionAtrasada(atraso)}
                          disabled={atraso.tiempoRestanteAutoMarcar === 0}
                        >
                          {atraso.tiempoRestanteAutoMarcar === 0 ? 'Procesando...' : 'Iniciar Ahora'}
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          onClick={() => notificarProfesional(atraso)}
                          disabled={atraso.tiempoRestanteAutoMarcar === 0}
                        >
                          Notificar Médico
                        </Button>
                      </Box>
                    </Card>
                  );
                })}
              </Box>
          )}
        </Paper>

        {/* Diálogo Ocupar */}
        <Dialog open={dialogOcupar} onClose={handleCerrarDialogoOcupar} maxWidth="xs" fullWidth>
          <DialogTitle>Ocupar {boxSeleccionado?.numero}</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                El box se liberará automáticamente después del tiempo seleccionado.
              </Typography>
              
              <TextField
                select
                fullWidth
                label="Duración"
                value={duracionEstimada}
                onChange={(e) => setDuracionEstimada(e.target.value)}
                sx={{ mb: 2 }}
              >
                {duracionesDisponibles.map((minutos) => (
                  <MenuItem key={minutos} value={minutos}>
                    {minutos} minutos
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                fullWidth
                label="Motivo (opcional)"
                value={motivoOcupacion}
                onChange={(e) => setMotivoOcupacion(e.target.value)}
                placeholder="Ej: Limpieza, Mantenimiento, etc."
                multiline
                rows={2}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCerrarDialogoOcupar}>Cancelar</Button>
            <Button onClick={confirmarOcuparBox} variant="contained">Confirmar</Button>
          </DialogActions>
        </Dialog>

        {/* Diálogo Info Atención/Ocupación */}
        <Dialog open={dialogInfoAtencion} onClose={handleCerrarInfoAtencion} maxWidth="sm" fullWidth>
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {boxSeleccionado?.ocupado_por_atencion ? <MedicalIcon color="primary" /> : <TimerIcon color="warning" />}
              Información - {boxSeleccionado?.numero}
            </Box>
          </DialogTitle>
          <DialogContent>
            {boxSeleccionado?.atencion_actual && (
              <Box sx={{ pt: 2 }}>
                <Typography variant="h6" gutterBottom color="primary">
                  Atención Programada
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Paciente:</strong> {boxSeleccionado.atencion_actual.paciente}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Médico:</strong> {boxSeleccionado.atencion_actual.medico}
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="body1" gutterBottom>
                  <strong>Tipo de Atención:</strong> {boxSeleccionado.atencion_actual.tipo_atencion}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Horario:</strong> {formatearHoraAtencion(boxSeleccionado)}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Duración Planificada:</strong> {boxSeleccionado.atencion_actual.duracion_planificada} minutos
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Estado:</strong> <Chip label={boxSeleccionado.atencion_actual.estado} size="small" color="primary" />
                </Typography>
              </Box>
            )}

            {boxSeleccionado?.ocupacion_manual_activa && !boxSeleccionado?.ocupado_por_atencion && (
              <Box sx={{ pt: 2 }}>
                <Typography variant="h6" gutterBottom color="warning.main">
                  Ocupación Manual
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Duración:</strong> {boxSeleccionado.ocupacion_manual_activa.duracion_minutos} minutos
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Inicio:</strong> {new Date(boxSeleccionado.ocupacion_manual_activa.fecha_inicio).toLocaleString('es-CL')}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Fin programado:</strong> {new Date(boxSeleccionado.ocupacion_manual_activa.fecha_fin_programada).toLocaleString('es-CL')}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Tiempo restante:</strong> {Math.round(boxSeleccionado.ocupacion_manual_activa.minutos_restantes)} minutos
                </Typography>
                {boxSeleccionado.ocupacion_manual_activa.motivo && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="body1" gutterBottom>
                      <strong>Motivo:</strong> {boxSeleccionado.ocupacion_manual_activa.motivo}
                    </Typography>
                  </>
                )}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                    Progreso
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={calcularProgresoOcupacion(boxSeleccionado.ocupacion_manual_activa)}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCerrarInfoAtencion}>Cerrar</Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} variant="filled">
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
};

export default EstadoBoxes;