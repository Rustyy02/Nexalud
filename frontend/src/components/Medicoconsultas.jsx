import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Container,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Grid,
  Chip,
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
  CloudDone as SyncIcon,
} from '@mui/icons-material';
import { medicoAtencionesService, boxesService } from '../services/api';
import Navbar from './Navbar';
const MedicoConsultas = () => {
  // Estados principales
  const [atencionActual, setAtencionActual] = useState(null);
  const [tipoAtencion, setTipoAtencion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [atencionesHoy, setAtencionesHoy] = useState([]);
  const [estadisticasHoy, setEstadisticasHoy] = useState(null);
  const [ultimaActualizacion, setUltimaActualizacion] = useState(new Date());
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
  // Refs para intervalos (evita memory leaks)
  const intervalRefActualizacion = useRef(null);
  const intervalRefCronometro = useRef(null);
  const isMountedRef = useRef(true);
  // ==================== FUNCIÓN AUXILIAR PARA OBTENER NOMBRE DEL PACIENTE ====================
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
  // ==================== FUNCIONES DE CARGA ====================
  const cargarAtencionActual = useCallback(async () => {
    if (!isMountedRef.current) return;
    try {
      console.log('🔄 Cargando atención actual...');
      const response = await medicoAtencionesService.getActual();
      if (!isMountedRef.current) return;
      console.log('✅ Atención actual:', response.data);
      const atencion = response.data.atencion;
      // Verificar si debe marcar automáticamente como NO_PRESENTADO
      if (atencion && atencion.atraso_reportado && atencion.debe_marcar_no_presentado) {
        console.log('⏰ Han pasado 5 minutos desde el reporte de atraso. Marcando como NO_PRESENTADO...');
        try {
          await medicoAtencionesService.verificarAtraso(atencion.id);
          showSnackbar('El paciente no se presentó en el tiempo esperado', 'warning');
          // Recargar datos después de marcar como NO_PRESENTADO
          const updatedResponse = await medicoAtencionesService.getActual();
          setAtencionActual(updatedResponse.data.atencion);
          setTipoAtencion(updatedResponse.data.tipo);
          return;
        } catch (error) {
          console.error('❌ Error al verificar atraso:', error);
        }
      }
      setAtencionActual(atencion);
      setTipoAtencion(response.data.tipo);
      setUltimaActualizacion(new Date());
      if (response.data.tipo === 'en_curso' && atencion?.inicio_cronometro) {
        const inicio = new Date(atencion.inicio_cronometro);
        const ahora = new Date();
        const transcurrido = Math.floor((ahora - inicio) / 1000);
        const duracionTotal = atencion.duracion_planificada * 60;
        const restante = duracionTotal - transcurrido;
        setTiempoTranscurrido(transcurrido);
        setTiempoRestante(restante);
      } else {
        setTiempoTranscurrido(0);
        setTiempoRestante(0);
      }
      setLoading(false);
    } catch (error) {
      if (isMountedRef.current) {
        console.error('❌ Error al cargar atención actual:', error);
        showSnackbar('Error al cargar la atención actual', 'error');
        setLoading(false);
      }
    }
  }, []);
  const cargarAtencionesHoy = useCallback(async () => {
    if (!isMountedRef.current) return;
    try {
      console.log('📅 Cargando atenciones del día...');
      const response = await medicoAtencionesService.getHoy();
      if (!isMountedRef.current) return;
      console.log('✅ Atenciones hoy:', response.data);
      const atenciones = Array.isArray(response.data.atenciones)
        ? response.data.atenciones
        : [];
      setAtencionesHoy(atenciones);
      setEstadisticasHoy({
        total: response.data.total || atenciones.length,
        completadas: response.data.completadas || 0,
        pendientes: response.data.pendientes || 0,
      });
    } catch (error) {
      if (isMountedRef.current) {
        console.error('❌ Error al cargar atenciones del día:', error);
        setAtencionesHoy([]);
      }
    }
  }, []);
  // Sincronizar estados de boxes (importante para consistencia)
  const sincronizarBoxes = useCallback(async () => {
    try {
      console.log('🔄 Sincronizando estados de boxes...');
      await boxesService.sincronizarEstados();
    } catch (error) {
      console.error('❌ Error al sincronizar boxes:', error);
    }
  }, []);
  // ==================== EFECTOS ====================
  // Efecto para marcar el componente como montado
  useEffect(() => {
    isMountedRef.current = true;
    console.log('🚀 Componente MedicoConsultas montado');
    return () => {
      isMountedRef.current = false;
      console.log('🧹 Componente MedicoConsultas desmontado');
    };
  }, []);
  // Efecto para carga inicial
  useEffect(() => {
    console.log('📥 Carga inicial de datos...');
    const cargarDatosIniciales = async () => {
      await Promise.all([
        cargarAtencionActual(),
        cargarAtencionesHoy(),
        sincronizarBoxes()
      ]);
    };
    cargarDatosIniciales();
  }, []); // Solo al montar
  // Efecto para actualización automática (POLLING)
  useEffect(() => {
    console.log('⏰ Configurando polling automático...');
    // Limpiar intervalo previo si existe
    if (intervalRefActualizacion.current) {
      clearInterval(intervalRefActualizacion.current);
    }
    // Configurar nuevo intervalo
    intervalRefActualizacion.current = setInterval(async () => {
      console.log('🔄 [POLLING] Actualizando datos automáticamente...');
      // Sincronizar boxes primero (esto actualiza estados)
      await sincronizarBoxes();
      // Luego cargar datos actualizados
      await Promise.all([
        cargarAtencionActual(),
        cargarAtencionesHoy()
      ]);
    }, 3000); // ✅ Cada 3 segundos para respuesta más rápida
    // Limpieza
    return () => {
      if (intervalRefActualizacion.current) {
        console.log('🧹 Limpiando intervalo de actualización');
        clearInterval(intervalRefActualizacion.current);
        intervalRefActualizacion.current = null;
      }
    };
  }, [cargarAtencionActual, cargarAtencionesHoy, sincronizarBoxes]);
  // Efecto para cronómetro local
  useEffect(() => {
    // Limpiar intervalo previo
    if (intervalRefCronometro.current) {
      clearInterval(intervalRefCronometro.current);
      intervalRefCronometro.current = null;
    }
    if (tipoAtencion === 'en_curso' && atencionActual?.inicio_cronometro) {
      console.log('⏱️ Iniciando cronómetro local');
      intervalRefCronometro.current = setInterval(() => {
        if (!isMountedRef.current) return;
        const inicio = new Date(atencionActual.inicio_cronometro);
        const ahora = new Date();
        const transcurrido = Math.floor((ahora - inicio) / 1000);
        const duracionTotal = atencionActual.duracion_planificada * 60;
        const restante = duracionTotal - transcurrido;
        setTiempoTranscurrido(transcurrido);
        setTiempoRestante(restante);
      }, 1000);
    } else {
      setTiempoTranscurrido(0);
      setTiempoRestante(0);
    }
    return () => {
      if (intervalRefCronometro.current) {
        console.log('🧹 Limpiando cronómetro');
        clearInterval(intervalRefCronometro.current);
        intervalRefCronometro.current = null;
      }
    };
  }, [tipoAtencion, atencionActual]);
  // ==================== FUNCIONES AUXILIARES ====================
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };
  const formatearTiempo = (segundos) => {
    const absSegundos = Math.abs(segundos);
    const horas = Math.floor(absSegundos / 3600);
    const minutos = Math.floor((absSegundos % 3600) / 60);
    const segs = absSegundos % 60;
    const signo = segundos < 0 ? '+' : '';
    if (horas > 0) {
      return `${signo}${String(horas).padStart(2, '0')}:${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
    }
    return `${signo}${String(minutos).padStart(2, '0')}:${String(segs).padStart(2, '0')}`;
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
  const tiempoExcedido = () => {
    return tipoAtencion === 'en_curso' && tiempoRestante < 0;
  };
  const calcularMinutosHastaInicio = () => {
    if (!atencionActual?.fecha_hora_inicio) return 0;
    const ahora = new Date();
    const inicio = new Date(atencionActual.fecha_hora_inicio);
    // Retorna la diferencia en minutos, truncada hacia abajo
    const diferencia = Math.floor((inicio - ahora) / (1000 * 60));
    return Math.max(0, diferencia);
  };

  // ✅ NUEVA FUNCIÓN: Calcula el tiempo restante en segundos.
  const calcularSegundosHastaInicio = () => {
    if (!atencionActual?.fecha_hora_inicio) return 0;
    const ahora = new Date();
    const inicio = new Date(atencionActual.fecha_hora_inicio);
    // Retorna la diferencia en segundos, redondeada hacia arriba para mostrar cuenta regresiva.
    const diferenciaSegundos = Math.ceil((inicio - ahora) / 1000);
    return Math.max(0, diferenciaSegundos);
  };

  // ==================== ACCIONES ====================
  const handleIniciarAtencion = async () => {
    if (!atencionActual) return;
    try {
      setLoading(true);
      console.log('▶️ Iniciando atención:', atencionActual.id);
      const response = await medicoAtencionesService.iniciar(atencionActual.id);
      if (response.data.success) {
        showSnackbar('Atención iniciada correctamente', 'success');
        // Actualizar inmediatamente con los datos del servidor
        const atencionActualizada = response.data.atencion;
        setAtencionActual(atencionActualizada);
        setTipoAtencion('en_curso');
        // Recargar todo para sincronizar
        await Promise.all([
          sincronizarBoxes(),
          cargarAtencionesHoy()
        ]);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al iniciar la atención';
      showSnackbar(errorMsg, 'error');
      console.error('❌ Error:', error);
    } finally {
      setLoading(false);
    }
  };
  const handleFinalizarAtencion = async () => {
    if (!atencionActual) return;
    try {
      setLoading(true);
      console.log('⏹️ Finalizando atención:', atencionActual.id);
      const response = await medicoAtencionesService.finalizar(
        atencionActual.id,
        observaciones ? { observaciones } : {}
      );
      if (response.data.success) {
        showSnackbar('Atención finalizada correctamente', 'success');
        // Resetear estados
        setAtencionActual(null);
        setTipoAtencion('ninguna');
        setObservaciones('');
        setDialogFinalizar(false);
        // Recargar todo para sincronizar
        await Promise.all([
          sincronizarBoxes(),
          cargarAtencionActual(),
          cargarAtencionesHoy()
        ]);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al finalizar la atención';
      showSnackbar(errorMsg, 'error');
      console.error('❌ Error:', error);
    } finally {
      setLoading(false);
    }
  };
  const handleNoPresentado = async () => {
    if (!atencionActual) return;
    try {
      setLoading(true);
      console.log('❌ Marcando no presentado:', atencionActual.id);
      const response = await medicoAtencionesService.noPresentado(
        atencionActual.id,
        observaciones ? { observaciones } : {}
      );
      if (response.data.success) {
        showSnackbar('Paciente marcado como no presentado', 'info');
        setDialogNoPresentado(false);
        setObservaciones('');
        // Recargar todo
        await Promise.all([
          sincronizarBoxes(),
          cargarAtencionActual(),
          cargarAtencionesHoy()
        ]);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al marcar no presentado';
      showSnackbar(errorMsg, 'error');
      console.error('❌ Error:', error);
    } finally {
      setLoading(false);
    }
  };
  const handleReportarAtraso = async () => {
    if (!motivoAtraso.trim() || !atencionActual) return;
    try {
      setLoading(true);
      // LOG ANTES DE LLAMAR AL BACKEND (Agregado para debug)
      console.log('⚠️ Reportando atraso:');
      console.log('  - ID:', atencionActual.id);
      console.log('  - Motivo:', motivoAtraso);
      console.log('  - Estado actual:', atencionActual.estado);
      console.log('  - URL:', `/medico/atenciones/${atencionActual.id}/reportar_atraso/`);
      const response = await medicoAtencionesService.reportarAtraso(
        atencionActual.id,
        { motivo: motivoAtraso }
      );
      // LOG DE LA RESPUESTA (Agregado para debug)
      console.log('✅ Respuesta del servidor:', response.data);
      if (response.data.success) {
        showSnackbar('Atraso reportado - Esperando 5 minutos', 'warning');
        // Actualizar la atención actual con los datos del servidor
        setAtencionActual(response.data.atencion);
        // Cerrar diálogo y limpiar
        setDialogAtraso(false);
        setMotivoAtraso('');
        // Recargar datos
        await Promise.all([
          sincronizarBoxes(),
          cargarAtencionesHoy()
        ]);
      }
    } catch (error) {
      // LOG DEL ERROR COMPLETO (Agregado para debug)
      console.error('❌ Error completo:', error);
      console.error('❌ Response:', error.response);
      console.error('❌ Data:', error.response?.data);
      const errorMsg = error.response?.data?.error || 'Error al reportar atraso';
      showSnackbar(errorMsg, 'error');
    } finally {
      setLoading(false);
    }
  };
  const handleIniciarConsulta = async () => {
    if (!atencionActual) return;
    try {
      setLoading(true);
      console.log('✅ Paciente llegó, iniciando consulta:', atencionActual.id);
      const response = await medicoAtencionesService.iniciarConsulta(atencionActual.id);
      if (response.data.success) {
        showSnackbar('Consulta iniciada correctamente', 'success');
        // Actualizar atención actual
        setAtencionActual(response.data.atencion);
        // Recargar datos
        await Promise.all([
          sincronizarBoxes(),
          cargarAtencionesHoy()
        ]);
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al iniciar consulta';
      showSnackbar(errorMsg, 'error');
      console.error('❌ Error:', error);
    } finally {
      setLoading(false);
    }
  };
  const handleRefrescar = async () => {
    console.log('🔄 Refrescando manualmente...');
    setLoading(true);
    await Promise.all([
      sincronizarBoxes(),
      cargarAtencionActual(),
      cargarAtencionesHoy()
    ]);
    setLoading(false);
    showSnackbar('Datos actualizados', 'info');
  };
  // ==================== RENDER ====================
  if (loading && !atencionActual) {
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
        {/* Header con indicador de última actualización */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box>
            <Typography variant="h4" fontWeight="700" gutterBottom>
              Mis Consultas
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SyncIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                Última actualización: {ultimaActualizacion.toLocaleTimeString('es-CL')}
              </Typography>
            </Box>
          </Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefrescar}
            disabled={loading}
          >
            Actualizar
          </Button>
        </Box>
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
          {/* Panel izquierdo - Lista */}
          <Grid item xs={12} lg={4}>
            <Card elevation={3} sx={{ minHeight: 500 }}>
              <CardContent>
                <Typography variant="h5" fontWeight="600" gutterBottom sx={{ mb: 3 }}>
                  📋 Atenciones de Hoy ({atencionesHoy.length})
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
                              <Typography variant="body2" fontWeight="500">
                                {obtenerNombrePaciente(atencion)}
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
          {/* Panel derecho - Cronómetro */}
          <Grid item xs={12} lg={8}>
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
                    {/* ALERTA DE ATRASO REPORTADO */}
                    {atencionActual.atraso_reportado && (
                      <Alert
                        severity="warning"
                        icon={<WarningIcon />}
                        sx={{ mb: 3 }}
                      >
                        <strong>⏳ Atraso reportado - Esperando al paciente</strong>
                        <Typography variant="body2">
                          Si el paciente llega, presiona "PACIENTE LLEGÓ - INICIAR".<br/>
                          Si no llega en 5 minutos, se marcará automáticamente como "No se presentó".
                        </Typography>
                      </Alert>
                    )}
                    <Paper sx={{
                      p: 3,
                      bgcolor: 'rgba(255,255,255,0.15)',
                      backdropFilter: 'blur(10px)',
                      mb: 3,
                      textAlign: 'center'
                    }}>
                      <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                        {calcularSegundosHastaInicio() > 0 ? 'Inicia en' : 'Atención programada'}
                      </Typography>
                      <Typography variant="h3" fontWeight="700">
                        {/* ✅ LÓGICA MODIFICADA PARA MOSTRAR SEGUNDOS */}
                        {calcularSegundosHastaInicio() > 60
                          ? `${calcularMinutosHastaInicio()} min`
                          : calcularSegundosHastaInicio() > 0
                            ? `${calcularSegundosHastaInicio()} seg`
                            : 'AHORA'
                        }
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
                            {obtenerNombrePaciente(atencionActual)}
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
                        {/* Botón INICIAR - Cambia comportamiento si hay atraso reportado */}
                        <Button
                          variant="contained"
                          size="large"
                          fullWidth
                          startIcon={<PlayIcon />}
                          onClick={atencionActual.atraso_reportado ? handleIniciarConsulta : handleIniciarAtencion}
                          disabled={
                            (!atencionActual.atraso_reportado && calcularMinutosHastaInicio() > 15) ||
                            loading
                          }
                          sx={{
                            py: 2,
                            bgcolor: atencionActual.atraso_reportado ? 'success.main' : 'white',
                            color: atencionActual.atraso_reportado ? 'white' : 'primary.main',
                            '&:hover': {
                              bgcolor: atencionActual.atraso_reportado ? 'success.dark' : 'rgba(255,255,255,0.9)',
                            }
                          }}
                        >
                          {loading ? 'Iniciando...' :
                           atencionActual.atraso_reportado
                            ? '✓ PACIENTE LLEGÓ - INICIAR'
                            : calcularMinutosHastaInicio() > 15
                              ? `Disponible en ${calcularMinutosHastaInicio()} min`
                              : 'INICIAR CONSULTA'
                          }
                        </Button>
                        {/* Botón REPORTAR ATRASO - Solo si ya es la hora Y NO hay atraso reportado */}
                        {!atencionActual.atraso_reportado && calcularMinutosHastaInicio() === 0 && (
                          <Button
                            variant="outlined"
                            size="large"
                            fullWidth
                            startIcon={<WarningIcon />}
                            onClick={() => setDialogAtraso(true)}
                            disabled={loading}
                            sx={{
                              color: 'white',
                              borderColor: 'rgba(255, 193, 7, 0.8)',
                              bgcolor: 'rgba(255, 193, 7, 0.1)',
                              '&:hover': {
                                borderColor: 'rgba(255, 193, 7, 1)',
                                bgcolor: 'rgba(255, 193, 7, 0.2)',
                              }
                            }}
                          >
                            REPORTAR ATRASO
                          </Button>
                        )}
                        {/* Botón NO SE PRESENTÓ */}
                        <Button
                          variant="outlined"
                          size="large"
                          fullWidth
                          startIcon={<CancelIcon />}
                          onClick={() => setDialogNoPresentado(true)}
                          disabled={loading}
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
                {/* ========================================= */}
                {/* ATENCIÓN EN CURSO - SECCIÓN  */}
                {/* ========================================= */}
                {tipoAtencion === 'en_curso' && atencionActual && (
                  <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ mb: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Chip
                          label="EN CURSO"
                          icon={<ClockIcon />}
                          sx={{
                            bgcolor: 'success.main',
                            color: 'white',
                            fontWeight: 600,
                          }}
                        />
                        {tiempoExcedido() && (
                          <Chip
                            icon={<WarningIcon />}
                            label="TIEMPO EXCEDIDO"
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
                      bgcolor: tiempoExcedido() ? 'rgba(244,67,54,0.2)' : 'rgba(76,175,80,0.2)',
                      backdropFilter: 'blur(10px)',
                      mb: 3,
                      textAlign: 'center',
                      border: tiempoExcedido() ? '2px solid rgba(244,67,54,0.5)' : '2px solid rgba(76,175,80,0.5)',
                    }}>
                      <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                        {tiempoExcedido() ? 'TIEMPO EXCEDIDO' : 'TIEMPO RESTANTE'}
                      </Typography>
                      <Typography
                        variant="h1"
                        fontWeight="700"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '4rem',
                          mb: 1,
                          color: tiempoExcedido() ? 'error.light' : 'inherit'
                        }}
                      >
                        {formatearTiempo(tiempoRestante)}
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
                            {obtenerNombrePaciente(atencionActual)}
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
                        {/* CASO 1: HAY ATRASO REPORTADO EN CURSO */}
                        {atencionActual.atraso_reportado && (
                            <Box>
                                <Alert severity="warning" sx={{ mb: 1 }}>
                                    <Typography variant="body2" fontWeight={600}>
                                        ⏳ Esperando que el paciente regrese ({Math.round(atencionActual.minutos_desde_reporte_atraso || 0)}/5 min)
                                    </Typography>
                                    <Typography variant="caption">
                                        Si regresa, presiona el botón para continuar
                                    </Typography>
                                </Alert>
                                <Button
                                    variant="contained"
                                    size="large"
                                    fullWidth
                                    startIcon={<PlayIcon />}
                                    onClick={handleIniciarConsulta}
                                    disabled={loading || atencionActual.debe_marcar_no_presentado}
                                    sx={{
                                        py: 2,
                                        bgcolor: 'success.main',
                                        color: 'white',
                                        fontWeight: 600,
                                        '&:hover': {
                                            bgcolor: 'success.dark',
                                        },
                                        '&.Mui-disabled': {
                                            bgcolor: 'grey.500',
                                            color: 'white',
                                        }
                                    }}
                                >
                                    {loading
                                        ? 'Continuando...'
                                        : atencionActual.debe_marcar_no_presentado
                                            ? 'TIEMPO AGOTADO'
                                            : '✓ PACIENTE REGRESÓ - CONTINUAR'
                                    }
                                </Button>
                            </Box>
                        )}
                        
                        {/* CASO 2: NO HAY ATRASO REPORTADO EN CURSO (Flujo normal) */}
                        {!atencionActual.atraso_reportado && (
                            <Box>
                                <Button
                                  variant="outlined"
                                  size="large"
                                  fullWidth
                                  startIcon={<WarningIcon />}
                                  onClick={() => setDialogAtraso(true)}
                                  disabled={loading}
                                  sx={{
                                    color: 'white',
                                    borderColor: 'rgba(255, 193, 7, 0.8)',
                                    bgcolor: 'rgba(255, 193, 7, 0.1)',
                                    '&:hover': {
                                      borderColor: 'rgba(255, 193, 7, 1)',
                                      bgcolor: 'rgba(255, 193, 7, 0.2)',
                                    }
                                  }}
                                >
                                  REPORTAR ATRASO / AUSENCIA
                                </Button>
                                {/* Info sobre tiempo disponible para reportar */}
                                {atencionActual.minutos_desde_inicio_atencion !== undefined &&
                                atencionActual.minutos_desde_inicio_atencion <= 5 && (
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      display: 'block',
                                      textAlign: 'center',
                                      mt: 0.5,
                                      color: 'rgba(255, 255, 255, 0.8)'
                                    }}
                                  >
                                    ⏱️ Disponible durante primeros 5 min
                                    ({Math.max(0, Math.round(5 - atencionActual.minutos_desde_inicio_atencion))} min restantes)
                                  </Typography>
                                )}
                                {/* Advertencia si ya pasaron 5 minutos */}
                                {atencionActual.minutos_desde_inicio_atencion !== undefined &&
                                atencionActual.minutos_desde_inicio_atencion > 5 && (
                                  <Typography
                                    variant="caption"
                                    sx={{
                                      display: 'block',
                                      textAlign: 'center',
                                      mt: 0.5,
                                      color: 'rgba(255, 193, 7, 0.9)',
                                      fontWeight: 600
                                    }}
                                  >
                                    ⚠️ Han pasado más de 5 min - El sistema puede rechazar el reporte
                                  </Typography>
                                )}
                            </Box>
                        )}
                        
                        {/* Botón FINALIZAR (siempre disponible si está en curso) */}
                        <Button
                          variant="contained"
                          size="large"
                          fullWidth
                          startIcon={<StopIcon />}
                          onClick={() => setDialogFinalizar(true)}
                          disabled={loading}
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
                        
                        {/* Botón NO SE PRESENTÓ (Siempre disponible si está en curso) */}
                        <Button
                          variant="outlined"
                          size="large"
                          fullWidth
                          startIcon={<CancelIcon />}
                          onClick={() => setDialogNoPresentado(true)}
                          disabled={loading}
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
                {/* ========================================= */}
                {/* FIN SECCIÓN ATENCIÓN EN CURSO */}
                {/* ========================================= */}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        {/* DIÁLOGOS */}
        <Dialog
          open={dialogFinalizar}
          onClose={() => !loading && setDialogFinalizar(false)}
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
              disabled={loading}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogFinalizar(false)} disabled={loading}>
              Cancelar
            </Button>
            <Button
              onClick={handleFinalizarAtencion}
              variant="contained"
              color="error"
              disabled={loading}
            >
              {loading ? 'Finalizando...' : 'Finalizar Consulta'}
            </Button>
          </DialogActions>
        </Dialog>
        <Dialog
          open={dialogNoPresentado}
          onClose={() => !loading && setDialogNoPresentado(false)}
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
              disabled={loading}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogNoPresentado(false)} disabled={loading}>
              Cancelar
            </Button>
            <Button
              onClick={handleNoPresentado}
              variant="contained"
              color="warning"
              disabled={loading}
            >
              {loading ? 'Procesando...' : 'Confirmar'}
            </Button>
          </DialogActions>
        </Dialog>
        {/* DIÁLOGO DE REPORTAR ATRASO - TEXTO ACTUALIZADO */}
        <Dialog
          open={dialogAtraso}
          onClose={() => !loading && setDialogAtraso(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color="warning" />
              Reportar Atraso / Ausencia del Paciente
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>⏳ Ventana de espera: 5 minutos</strong>
              <Typography variant="body2" sx={{ mt: 1 }}>
                • Si el paciente llega/regresa dentro de 5 minutos, podrás continuar<br/>
                • Si no llega/regresa, se marcará automáticamente como "No se presentó"<br/>
                • Esta espera será visible en el panel de Estado de Boxes
              </Typography>
            </Alert>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Motivo del atraso/ausencia *"
              value={motivoAtraso}
              onChange={(e) => setMotivoAtraso(e.target.value)}
              placeholder={
                tipoAtencion === 'en_curso'
                  ? "Ej: Paciente salió a hacer una llamada / Paciente fue al baño"
                  : "Ej: Paciente no se presentó a la hora programada (17:00)"
              }
              required
              disabled={loading}
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogAtraso(false)} disabled={loading}>
              Cancelar
            </Button>
            <Button
              onClick={handleReportarAtraso}
              variant="contained"
              color="warning"
              disabled={!motivoAtraso.trim() || loading}
            >
              {loading ? 'Reportando...' : 'Confirmar - Dar 5 min de gracia'}
            </Button>
          </DialogActions>
        </Dialog>
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