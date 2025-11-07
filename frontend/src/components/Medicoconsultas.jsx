// frontend/src/components/MedicoConsultas.jsx - VERSIÓN CORREGIDA
// ✅ Actualización automática funcional
// ✅ Concepto correcto de "atraso" (paciente llega tarde al inicio)
// ✅ Nombres de pacientes visibles
// ✅ Cronómetro que sigue contando después del tiempo planificado

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

  // ✅ NUEVO: Usar refs para evitar re-creación de funciones
  const intervalRefActualizacion = useRef(null);
  const intervalRefCronometro = useRef(null);

  // ==================== FUNCIÓN AUXILIAR PARA OBTENER NOMBRE DEL PACIENTE ====================
  
  const obtenerNombrePaciente = (atencion) => {
    if (!atencion) return 'Sin paciente';
    
    console.log('🔍 Obteniendo nombre de paciente:', atencion);
    
    // 1. Intentar con paciente_nombre (viene en AtencionListSerializer)
    if (atencion.paciente_nombre) {
      return atencion.paciente_nombre;
    }
    
    // 2. Intentar con paciente_info.nombre_completo
    if (atencion.paciente_info?.nombre_completo) {
      return atencion.paciente_info.nombre_completo;
    }
    
    // 3. Intentar construir desde nombre y apellidos del paciente_info
    const pacienteInfo = atencion.paciente_info;
    if (pacienteInfo) {
      // Si tiene 'nombres' o 'nombre'
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
    
    // 4. Último recurso: usar hash corto
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
    try {
      const response = await medicoAtencionesService.getActual();
      console.log('✅ Atención actual cargada:', response.data);
      
      setAtencionActual(response.data.atencion);
      setTipoAtencion(response.data.tipo);
      
      // ✅ Si hay atención en curso, calcular tiempo inicial
      if (response.data.tipo === 'en_curso' && response.data.atencion?.inicio_cronometro) {
        const inicio = new Date(response.data.atencion.inicio_cronometro);
        const ahora = new Date();
        const transcurrido = Math.floor((ahora - inicio) / 1000);
        const duracionTotal = response.data.atencion.duracion_planificada * 60;
        const restante = duracionTotal - transcurrido;
        
        setTiempoTranscurrido(transcurrido);
        setTiempoRestante(restante);
      }
      
      setLoading(false);
    } catch (error) {
      console.error('❌ Error al cargar atención actual:', error);
      showSnackbar('Error al cargar la atención actual', 'error');
      setLoading(false);
    }
  }, []);

  const cargarAtencionesHoy = useCallback(async () => {
    try {
      const response = await medicoAtencionesService.getHoy();
      console.log('✅ Atenciones hoy cargadas:', response.data);
      
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
      console.error('❌ Error al cargar atenciones del día:', error);
      setAtencionesHoy([]);
    }
  }, []);

  // ==================== EFECTOS ====================
  
  // ✅ Efecto para carga inicial
  useEffect(() => {
    console.log('🚀 Componente montado, cargando datos iniciales...');
    cargarAtencionActual();
    cargarAtencionesHoy();
    
    return () => {
      console.log('🧹 Componente desmontado');
    };
  }, []); // Solo al montar

  // ✅ Efecto para actualización automática de datos
  useEffect(() => {
    console.log('⏰ Iniciando actualización automática cada 5 segundos');
    
    intervalRefActualizacion.current = setInterval(() => {
      console.log('🔄 Actualizando datos...');
      cargarAtencionActual();
      cargarAtencionesHoy();
    }, 5000); // Cada 5 segundos
    
    return () => {
      if (intervalRefActualizacion.current) {
        console.log('🧹 Limpiando intervalo de actualización');
        clearInterval(intervalRefActualizacion.current);
      }
    };
  }, [cargarAtencionActual, cargarAtencionesHoy]);

  // ✅ Efecto para cronómetro local (actualiza cada segundo)
  useEffect(() => {
      // Si no está en curso o no tiene inicio, no inicia y limpia.
      if (tipoAtencion === 'en_curso' && atencionActual?.inicio_cronometro) {
        console.log('⏱️ Iniciando cronómetro local');
        
        // Primero, limpia cualquier intervalo previo (ES CLAVE)
        if (intervalRefCronometro.current) {
          clearInterval(intervalRefCronometro.current);
          intervalRefCronometro.current = null;
        }
        
        intervalRefCronometro.current = setInterval(() => {
          const inicio = new Date(atencionActual.inicio_cronometro);
          const ahora = new Date();
          const transcurrido = Math.floor((ahora - inicio) / 1000);
          const duracionTotal = atencionActual.duracion_planificada * 60;
          const restante = duracionTotal - transcurrido;
          
          setTiempoTranscurrido(transcurrido);
          setTiempoRestante(restante);
        }, 1000); // Cada segundo
        
      } else {
        // Limpiar cronómetro si no hay atención en curso (TAMBIÉN ES CLAVE)
        if (intervalRefCronometro.current) {
          clearInterval(intervalRefCronometro.current);
          intervalRefCronometro.current = null;
        }
        setTiempoTranscurrido(0);
        setTiempoRestante(0);
      }
      
      // Función de limpieza que se ejecuta al desmontar o antes del siguiente efecto
      return () => {
        if (intervalRefCronometro.current) {
          console.log('🧹 Limpiando cronómetro');
          clearInterval(intervalRefCronometro.current);
        }
      };
  }, [tipoAtencion, atencionActual]); // Dependencias: tipoAtencion y atencionActual

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
    // ✅ El tiempo se excedió cuando el restante es negativo
    return tipoAtencion === 'en_curso' && tiempoRestante < 0;
  };

  const calcularMinutosHastaInicio = () => {
    if (!atencionActual?.fecha_hora_inicio) return 0;
    const ahora = new Date();
    const inicio = new Date(atencionActual.fecha_hora_inicio);
    const diferencia = Math.floor((inicio - ahora) / (1000 * 60));
    return Math.max(0, diferencia);
  };

  // ==================== ACCIONES ====================
  
  // En Medicoconsultas.jsx
  const handleIniciarAtencion = async () => {
      if (!atencionActual) return;

      try {
          setLoading(true);
          // La API devuelve: { success: true, atencion: { ...objeto actualizado... } }
          const response = await medicoAtencionesService.iniciar(atencionActual.id); 

          if (response.data.success) {
              showSnackbar('Atención iniciada correctamente', 'success');
              
              // 💡 SOLUCIÓN: Usar la data que YA devolvió el servidor (contiene inicio_cronometro)
              const atencionActualizada = response.data.atencion;
              
              setAtencionActual(atencionActualizada);
              setTipoAtencion('en_curso'); // Forzar la actualización del tipo

              // Recargar la lista de atenciones para que el box se actualice en la tabla
              await cargarAtencionesHoy(); 
          }
          // ... (manejo de errores y finally)
      } catch (error) {
          // ...
      } finally {
          setLoading(false);
      }
  };

  // En Medicoconsultas.jsx
  const handleFinalizarAtencion = async (motivo) => {
      if (!atencionActual) return;

      try {
          setLoading(true);
          // La API devuelve: { success: true, atencion: { ...objeto finalizado... } }
          const response = await medicoAtencionesService.finalizar(atencionActual.id, { motivo });

          if (response.data.success) {
              showSnackbar('Atención finalizada correctamente', 'success');
              
              // 💡 SOLUCIÓN: Usar la data que YA devolvió el servidor (contiene fin_cronometro y duracion_real)
              const atencionFinalizada = response.data.atencion;

              // Resetear estados locales para volver a "Sin Atenciones Programadas"
              setAtencionActual(atencionFinalizada); 
              setTipoAtencion('finalizada'); // O cualquier estado que asegure que el cronómetro se detenga.
              
              // Recargar la lista de atenciones y el conteo de estadísticas
              await cargarAtencionesHoy();


          }
          // ... (manejo de errores y finally)
      } catch (error) {
          // ...
      } finally {
          setDialogFinalizar(false);
          setLoading(false);
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
        // ✅ Forzar actualización inmediata
        await cargarAtencionActual();
        await cargarAtencionesHoy();
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Error al marcar no presentado';
      showSnackbar(errorMsg, 'error');
    }
  };

  const handleReportarAtraso = async () => {
    // ✅ NUEVO: Reportar atraso solo guarda una observación
    if (!atencionActual || !motivoAtraso.trim()) return;
    
    try {
      // Agregar observación sobre el atraso
      const observacionAtraso = `[ATRASO REPORTADO] ${motivoAtraso}`;
      
      // Actualizar la atención con la observación
      const response = await medicoAtencionesService.finalizar(
        atencionActual.id,
        { observaciones: observacionAtraso }
      );
      
      // O si tienes un endpoint específico para agregar observaciones:
      // await medicoAtencionesService.agregarObservacion(atencionActual.id, observacionAtraso);
      
      showSnackbar('Atraso reportado correctamente', 'warning');
      setDialogAtraso(false);
      setMotivoAtraso('');
      
    } catch (error) {
      showSnackbar('Error al reportar atraso', 'error');
    }
  };

  const handleRefrescar = async () => {
    console.log('🔄 Refrescando datos manualmente...');
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
          {/* ✅ PANEL IZQUIERDO - LISTADO DE ATENCIONES */}
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

          {/* ✅ PANEL DERECHO - CRONÓMETRO Y ATENCIÓN ACTUAL */}
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
                        {/* ✅ Botón de reportar atraso siempre visible en consulta activa */}
                        <Button
                          variant="outlined"
                          size="large"
                          fullWidth
                          startIcon={<WarningIcon />}
                          onClick={() => setDialogAtraso(true)}
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
                      </Stack>
                    </Box>
                  </Box>
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

        {/* ✅ Diálogo Reportar Atraso - CONCEPTO CORREGIDO */}
        <Dialog 
          open={dialogAtraso} 
          onClose={() => setDialogAtraso(false)} 
          maxWidth="sm" 
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color="warning" />
              Reportar Atraso del Paciente
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              Usa esta opción cuando el paciente llega tarde a su consulta programada. 
              La consulta continuará normalmente, pero quedará registrado el atraso.
            </Alert>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Motivo del atraso *"
              value={motivoAtraso}
              onChange={(e) => setMotivoAtraso(e.target.value)}
              placeholder="Ej: Paciente llegó 10 minutos tarde por problemas de transporte"
              required
              sx={{ mt: 2 }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogAtraso(false)}>
              Cancelar
            </Button>
            <Button 
              onClick={handleReportarAtraso} 
              variant="contained" 
              color="warning"
              disabled={!motivoAtraso.trim()}
            >
              Reportar Atraso
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