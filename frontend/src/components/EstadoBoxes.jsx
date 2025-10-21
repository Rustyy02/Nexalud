// frontend/src/components/EstadoBoxes.jsx - CON SINCRONIZACIÓN COMPLETA
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
  const [tiemposLiberacion, setTiemposLiberacion] = useState({});

  useEffect(() => {
    cargarDatos();
    sincronizarEstados();
    
    const intervalSync = setInterval(sincronizarEstados, 30000);
    const intervalData = setInterval(cargarDatos, 15000);
    
    return () => {
      clearInterval(intervalSync);
      clearInterval(intervalData);
      Object.values(tiemposLiberacion).forEach(timeout => clearTimeout(timeout));
    };
  }, []);

  const sincronizarEstados = async () => {
    try {
      setSincronizando(true);
      await boxesService.sincronizarEstados();
    } catch (err) {
      console.error('Error en sincronización automática:', err);
    } finally {
      setSincronizando(false);
    }
  };

  const sincronizarManual = async () => {
    try {
      setSincronizando(true);
      const response = await boxesService.sincronizarEstados();
      showSnackbar(
        `Sincronización completa: ${response.data.boxes_actualizados} boxes actualizados`,
        'success'
      );
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
      const [boxesRes, atencionesRes] = await Promise.all([
        boxesService.getAll(),
        atencionesService.getRetrasadas()
      ]);
      
      setBoxes(boxesRes.data);
      
      if (atencionesRes.data && atencionesRes.data.atenciones) {
        const atrasosFormateados = atencionesRes.data.atenciones.map(atencion => {
          const atrasoMinutos = calcularAtrasoMinutos(atencion);
          return {
            id: atencion.id,
            paciente: atencion.paciente_hash || 'Paciente sin identificar',
            box: atencion.box_numero || 'Sin box asignado',
            atrasoMinutos: atrasoMinutos,
            atencionId: atencion.id,
            horaInicioProgramada: atencion.fecha_hora_inicio,
            duracionPlanificada: atencion.duracion_planificada,
          };
        });
        
        setAtrasosReales(atrasosFormateados.filter(a => a.atrasoMinutos > 0));
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

  const calcularAtrasoMinutos = (atencion) => {
    if (!atencion.fecha_hora_inicio) return 0;
    
    const ahora = new Date();
    const horaInicio = new Date(atencion.fecha_hora_inicio);
    
    if (!atencion.inicio_cronometro && ahora > horaInicio) {
      const diferenciaMs = ahora - horaInicio;
      const diferenciaMinutos = Math.floor(diferenciaMs / (1000 * 60));
      return diferenciaMinutos;
    }
    
    return 0;
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
    setDialogOcupar(true);
  };

  const handleCerrarDialogoOcupar = () => {
    setDialogOcupar(false);
    setBoxSeleccionado(null);
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
        await boxesService.liberar(box.id);
        
        if (tiemposLiberacion[box.id]) {
          clearTimeout(tiemposLiberacion[box.id]);
          const nuevosTimeouts = { ...tiemposLiberacion };
          delete nuevosTimeouts[box.id];
          setTiemposLiberacion(nuevosTimeouts);
        }
        
        showSnackbar(`Box ${box.numero} liberado correctamente`, 'success');
        await cargarDatos();
      }
    } catch (err) {
      showSnackbar('Error al cambiar el estado del box', 'error');
      console.error(err);
    }
  };

  const confirmarOcuparBox = async () => {
    if (!boxSeleccionado) return;

    try {
      await boxesService.ocupar(boxSeleccionado.id);
      
      const duracionMs = duracionEstimada * 60 * 1000;
      const timeoutId = setTimeout(async () => {
        try {
          await boxesService.liberar(boxSeleccionado.id);
          showSnackbar(`Box ${boxSeleccionado.numero} liberado automáticamente`, 'info');
          await cargarDatos();
          
          const nuevosTimeouts = { ...tiemposLiberacion };
          delete nuevosTimeouts[boxSeleccionado.id];
          setTiemposLiberacion(nuevosTimeouts);
        } catch (err) {
          console.error('Error en auto-liberación:', err);
        }
      }, duracionMs);

      setTiemposLiberacion({
        ...tiemposLiberacion,
        [boxSeleccionado.id]: timeoutId
      });

      showSnackbar(
        `Box ${boxSeleccionado.numero} ocupado. Se liberará en ${duracionEstimada} minutos`,
        'success'
      );
      
      handleCerrarDialogoOcupar();
      await cargarDatos();
    } catch (err) {
      showSnackbar('Error al ocupar el box', 'error');
      console.error(err);
    }
  };

  const notificarProfesional = async (atraso) => {
    showSnackbar(`Notificación enviada al profesional del ${atraso.box}`, 'info');
  };

  const iniciarAtencionAtrasada = async (atraso) => {
    try {
      await atencionesService.iniciarCronometro(atraso.atencionId);
      
      const boxCorrespondiente = boxes.find(b => b.numero === atraso.box);
      
      if (boxCorrespondiente) {
        await boxesService.ocupar(boxCorrespondiente.id);
        
        const duracionMs = atraso.duracionPlanificada * 60 * 1000;
        const timeoutId = setTimeout(async () => {
          try {
            await boxesService.liberar(boxCorrespondiente.id);
            await atencionesService.finalizarCronometro(atraso.atencionId);
            showSnackbar(`Atención completada y box ${atraso.box} liberado`, 'success');
            await cargarDatos();
          } catch (err) {
            console.error('Error en auto-liberación:', err);
          }
        }, duracionMs);

        setTiemposLiberacion({
          ...tiemposLiberacion,
          [boxCorrespondiente.id]: timeoutId
        });
      }

      showSnackbar(
        `Atención iniciada. Se liberará en ${atraso.duracionPlanificada} minutos`,
        'success'
      );
      
      await cargarDatos();
    } catch (err) {
      showSnackbar('Error al iniciar la atención', 'error');
      console.error(err);
    }
  };

  const getEstadoColor = (estado) => {
    const colores = {
      DISPONIBLE: 'success',
      OCUPADO: 'warning',
      MANTENIMIENTO: 'error',
      FUERA_SERVICIO: 'default',
    };
    return colores[estado] || 'default';
  };

  const getEstadoIcon = (estado) => {
    if (estado === 'DISPONIBLE') return <CheckCircleIcon />;
    if (estado === 'OCUPADO') return <WarningIcon />;
    return <ScheduleIcon />;
  };

  const formatearHoraAtencion = (box) => {
    if (box.atencion_actual) {
      const fecha = new Date(box.atencion_actual.fecha_hora_inicio);
      const hora = fecha.toLocaleTimeString('es-CL', {
        hour: '2-digit',
        minute: '2-digit',
      });
      
      const fechaFin = new Date(fecha.getTime() + box.atencion_actual.duracion_planificada * 60 * 1000);
      const horaFin = fechaFin.toLocaleTimeString('es-CL', {
        hour: '2-digit',
        minute: '2-digit',
      });
      
      return `${hora} - ${horaFin}`;
    }
    return '';
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

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" fontWeight="600">
            Gestión de Boxes
          </Typography>
          
          <Button
            variant="outlined"
            startIcon={sincronizando ? <CircularProgress size={20} /> : <SyncIcon />}
            onClick={sincronizarManual}
            disabled={sincronizando}
          >
            {sincronizando ? 'Sincronizando...' : 'Sincronizar Estados'}
          </Button>
        </Box>

        {/* Alerta */}
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
          Los estados de los boxes se sincronizan automáticamente cada 30 segundos con las atenciones programadas.
        </Alert>

        {/* Boxes */}
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h5" fontWeight="600" gutterBottom>
            Box's
          </Typography>

          <Grid container spacing={3} sx={{ mt: 2 }}>
            {boxes.map((box) => (
              <Grid item xs={12} sm={6} md={3} key={box.id}>
                <Card
                  elevation={3}
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 2,
                    transition: 'transform 0.2s',
                    borderLeft: box.ocupado_por_atencion ? '4px solid' : 'none',
                    borderLeftColor: 'primary.main',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" fontWeight="600">
                        {box.numero}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                        <Chip
                          icon={getEstadoIcon(box.estado)}
                          label={box.estado_display}
                          color={getEstadoColor(box.estado)}
                          size="small"
                          sx={{ fontWeight: 500 }}
                        />
                        {box.ocupado_por_atencion && (
                          <Tooltip title="Ver información">
                            <IconButton size="small" onClick={() => handleVerInfoAtencion(box)}>
                              <InfoIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </Box>

                    {box.ocupado_por_atencion && box.atencion_actual && (
                      <Box sx={{ 
                        bgcolor: 'primary.light', 
                        p: 1.5, 
                        borderRadius: 1, 
                        mb: 2,
                        border: '1px solid',
                        borderColor: 'primary.main',
                      }}>
                        <Typography variant="caption" color="primary.dark" fontWeight="600" display="block">
                          📋 ATENCIÓN PROGRAMADA
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                          <strong>Paciente:</strong> {box.atencion_actual.paciente}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Hora:</strong> {formatearHoraAtencion(box)}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Tipo:</strong> {box.atencion_actual.tipo_atencion}
                        </Typography>
                      </Box>
                    )}

                    {box.estado === 'OCUPADO' && !box.ocupado_por_atencion && (
                      <>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          <strong>Ocupación Manual</strong>
                        </Typography>
                        {tiemposLiberacion[box.id] && (
                          <Chip
                            icon={<AccessTimeIcon />}
                            label="Auto-liberación activa"
                            size="small"
                            color="info"
                            sx={{ mb: 2 }}
                          />
                        )}
                      </>
                    )}

                    {box.estado === 'DISPONIBLE' && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        ✓ Disponible para atención
                      </Typography>
                    )}

                    <Button
                      variant="contained"
                      fullWidth
                      size="large"
                      onClick={() => cambiarEstadoBox(box, box.estado === 'DISPONIBLE' ? 'OCUPADO' : 'DISPONIBLE')}
                      disabled={
                        box.estado === 'MANTENIMIENTO' || 
                        box.estado === 'FUERA_SERVICIO' ||
                        box.ocupado_por_atencion
                      }
                      sx={{
                        textTransform: 'none',
                        fontWeight: 500,
                        backgroundColor: box.estado === 'DISPONIBLE' ? 'primary.main' : 'success.main',
                        '&:hover': {
                          backgroundColor: box.estado === 'DISPONIBLE' ? 'primary.dark' : 'success.dark',
                        },
                      }}
                    >
                      {box.ocupado_por_atencion 
                        ? '🔒 Ocupado por Atención' 
                        : box.estado === 'DISPONIBLE' 
                          ? 'Marcar como Ocupado' 
                          : 'Marcar como Libre'}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* Atrasos */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5" fontWeight="600">
              Atrasos en Atenciones
            </Typography>
            {atrasosReales.length > 0 && (
              <Chip label={`${atrasosReales.length} atraso${atrasosReales.length > 1 ? 's' : ''}`} color="error" size="small" />
            )}
          </Box>

          {atrasosReales.length === 0 ? (
            <Alert severity="success" sx={{ mt: 2 }}>
              ✓ No hay atrasos registrados.
            </Alert>
          ) : (
            <Box sx={{ mt: 2 }}>
              {atrasosReales.map((atraso) => (
                <Card key={atraso.id} elevation={1} sx={{ mb: 2, p: 2, borderLeft: '4px solid', borderLeftColor: 'error.main' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Box sx={{ flex: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <PersonIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                        <Typography variant="subtitle1" fontWeight="600">
                          {atraso.paciente}
                        </Typography>
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
                        <WarningIcon sx={{ color: 'error.main', fontSize: 20 }} />
                        <Typography variant="body2" color="error.main" fontWeight="600">
                          Atraso: {atraso.atrasoMinutos} minutos
                        </Typography>
                      </Box>
                    </Box>
                    <Chip label={atraso.box} color="warning" size="small" />
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      size="small"
                      fullWidth
                      onClick={() => iniciarAtencionAtrasada(atraso)}
                    >
                      Iniciar Ahora
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      fullWidth
                      onClick={() => notificarProfesional(atraso)}
                    >
                      Notificar
                    </Button>
                  </Box>
                </Card>
              ))}
            </Box>
          )}
        </Paper>

        {/* Diálogo Ocupar */}
        <Dialog open={dialogOcupar} onClose={handleCerrarDialogoOcupar} maxWidth="xs" fullWidth>
          <DialogTitle>Ocupar {boxSeleccionado?.numero}</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                El box se liberará automáticamente.
              </Typography>
              <TextField
                select
                fullWidth
                label="Duración estimada"
                value={duracionEstimada}
                onChange={(e) => setDuracionEstimada(e.target.value)}
              >
                <MenuItem value={15}>15 minutos</MenuItem>
                <MenuItem value={20}>20 minutos</MenuItem>
                <MenuItem value={30}>30 minutos</MenuItem>
                <MenuItem value={45}>45 minutos</MenuItem>
                <MenuItem value={60}>1 hora</MenuItem>
                <MenuItem value={90}>1.5 horas</MenuItem>
                <MenuItem value={120}>2 horas</MenuItem>
              </TextField>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCerrarDialogoOcupar}>Cancelar</Button>
            <Button onClick={confirmarOcuparBox} variant="contained">Confirmar</Button>
          </DialogActions>
        </Dialog>

        {/* Diálogo Info Atención */}
        <Dialog open={dialogInfoAtencion} onClose={handleCerrarInfoAtencion} maxWidth="sm" fullWidth>
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MedicalIcon color="primary" />
              Información de Atención - {boxSeleccionado?.numero}
            </Box>
          </DialogTitle>
          <DialogContent>
            {boxSeleccionado?.atencion_actual && (
              <Box sx={{ pt: 2 }}>
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