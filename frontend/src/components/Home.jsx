// frontend/src/components/Home.jsx - ACTUALIZADO CON SINCRONIZACIÓN DE ETAPA
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
  CircularProgress,
  Alert,
  Drawer,
  IconButton,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  TextField,
  InputAdornment,
  Tooltip,
} from '@mui/material';
import {
  Person as PersonIcon,
  Close as CloseIcon,
  ArrowForward as ArrowForwardIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Badge as BadgeIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  Timeline as TimelineIcon,
  LocalHospital as HospitalIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { pacientesService, rutasClinicasService, boxesService } from '../services/api';
import Navbar from './Navbar';

const Home = () => {
  const navigate = useNavigate();
  
  const [pacientes, setPacientes] = useState([]);
  const [pacienteSeleccionado, setPacienteSeleccionado] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingRuta, setLoadingRuta] = useState(false);
  const [error, setError] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [terminoBusqueda, setTerminoBusqueda] = useState('');

  useEffect(() => {
    cargarDatos();
    const interval = setInterval(cargarDatos, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarDatos = async () => {
    try {
      setError('');
      const timestamp = new Date().getTime();
      const nocache = Math.random(); // ✅ NUEVO: Fuerza bypass total del caché
      
      const [pacientesRes, boxesRes] = await Promise.all([
        pacientesService.getAll({ 
          activo: true, 
          _t: timestamp,
          _nocache: nocache // ✅ NUEVO
        }),
        boxesService.getAll({ 
          _t: timestamp,
          _nocache: nocache // ✅ NUEVO
        })
      ]);
      
      setPacientes(pacientesRes.data);
      setBoxes(boxesRes.data);
      setLoading(false);
    } catch (err) {
      setError('Error al cargar los datos');
      setLoading(false);
      console.error(err);
    }
  };

  const handleSeleccionarPaciente = async (paciente) => {
    setPacienteSeleccionado(paciente);
    setDrawerOpen(true);
    setLoadingRuta(true);
    
    try {
      const rutasRes = await pacientesService.getRutasClinicas(paciente.id);
      
      if (rutasRes.data && rutasRes.data.length > 0) {
        const rutaActual = rutasRes.data[0];
        const timelineRes = await rutasClinicasService.getTimeline(rutaActual.id);
        setRutaClinica(timelineRes.data);
      } else {
        setRutaClinica(null);
      }
    } catch (err) {
      console.error('Error al cargar ruta clínica:', err);
      setRutaClinica(null);
    } finally {
      setLoadingRuta(false);
    }
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setPacienteSeleccionado(null);
    setRutaClinica(null);
  };

  const handleLimpiarBusqueda = () => {
    setTerminoBusqueda('');
  };

  const getColorEstado = (estado) => {
    const colores = {
      'EN_ESPERA': 'warning',
      'ACTIVO': 'success',
      'PROCESO_PAUSADO': 'default',
      'ALTA_COMPLETA': 'success',
      'ALTA_MEDICA': 'success',
      'PROCESO_INCOMPLETO': 'error',
      'INACTIVO': 'default',
    };
    return colores[estado] || 'default';
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

  // ============================================
  // 🆕 NUEVO: Obtener color para la etapa clínica
  // ============================================
  const getColorEtapa = (etapa) => {
    const colores = {
      'CONSULTA_MEDICA': 'primary',
      'PROCESO_EXAMEN': 'secondary',
      'REVISION_EXAMEN': 'info',
      'HOSPITALIZACION': 'warning',
      'OPERACION': 'error',
      'ALTA': 'success',
    };
    return colores[etapa] || 'default';
  };

  const getColorBox = (estado) => {
    const colores = {
      'DISPONIBLE': 'success',
      'OCUPADO': 'warning',
      'MANTENIMIENTO': 'error',
      'FUERA_SERVICIO': 'default',
    };
    return colores[estado] || 'default';
  };

  const obtenerDatosPaciente = (paciente) => {
    if (!paciente) {
      return {
        nombre: 'Paciente desconocido',
        rut: 'Sin RUT',
        correo: 'Sin correo',
        contacto: 'Sin contacto',
      };
    }

    const metadatos = (typeof paciente.metadatos_adicionales === 'object' && 
                      !Array.isArray(paciente.metadatos_adicionales)) 
                      ? paciente.metadatos_adicionales 
                      : {};

    const identificador = paciente.identificador_hash || paciente.id || '';
    const identificadorCorto = identificador ? identificador.substring(0, 8) : 'SIN-ID';

    return {
      nombre: metadatos.nombre || 
              paciente.nombre || 
              paciente.nombre_completo ||
              `Paciente ${identificadorCorto}`,
      rut: metadatos.rut_original || 
          paciente.rut || 
          (identificador ? `${identificador.substring(0, 12)}...` : 'Sin RUT'),
      correo: metadatos.correo || 
              paciente.correo || 
              'Sin correo registrado',
      contacto: metadatos.contacto || 
                paciente.telefono || 
                'Sin contacto registrado',
    };
  };

  const pacientesFiltrados = pacientes.filter((paciente) => {
    if (!terminoBusqueda.trim()) return true;
    
    const termino = terminoBusqueda.toLowerCase().trim();
    const datos = obtenerDatosPaciente(paciente);
    
    if (datos.rut.toLowerCase().includes(termino)) return true;
    if (datos.nombre.toLowerCase().includes(termino)) return true;
    if (datos.correo.toLowerCase().includes(termino)) return true;
    if (datos.contacto.toLowerCase().includes(termino)) return true;
    
    return false;
  });

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
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Sección de Pacientes */}
        <Paper elevation={3} sx={{ mb: 4, borderRadius: 2 }}>
          <Box sx={{ p: 3, bgcolor: 'primary.main', color: 'white', borderRadius: '8px 8px 0 0' }}>
            <Typography variant="h5" fontWeight="600">
              Lista de Pacientes
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {pacientesFiltrados.length} de {pacientes.length} pacientes activos
            </Typography>
          </Box>

          <Box sx={{ p: 3, pb: 2 }}>
            <TextField
              fullWidth
              placeholder="Buscar por RUT, nombre, correo o teléfono..."
              value={terminoBusqueda}
              onChange={(e) => setTerminoBusqueda(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon color="action" />
                  </InputAdornment>
                ),
                endAdornment: terminoBusqueda && (
                  <InputAdornment position="end">
                    <IconButton
                      size="small"
                      onClick={handleLimpiarBusqueda}
                      edge="end"
                    >
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'background.paper',
                },
              }}
            />
          </Box>

          {/* ============================================
              TABLA ACTUALIZADA CON ETAPA ACTUAL
              ============================================ */}
          <TableContainer                        
                    sx={{
                          maxHeight: 400, // 🔹 altura máxima
                          overflowY: 'auto', // 🔹 activa el scroll vertical
                          borderTop: '1px solid',
                          borderColor: 'divider',
                        }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.50' }}>
                  <TableCell sx={{ fontWeight: 600 }}>RUT</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Nombre</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Correo</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Contacto</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Estado Sistema</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <HospitalIcon sx={{ fontSize: 18 }} />
                      Etapa Clínica
                    </Box>
                  </TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Urgencia</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600 }}>Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pacientesFiltrados.length > 0 ? (
                  pacientesFiltrados.map((paciente) => {
                    const datos = obtenerDatosPaciente(paciente);
                    return (
                      <TableRow
                        key={paciente.id}
                        hover
                        sx={{
                          cursor: 'pointer',
                          '&:hover': {
                            bgcolor: 'action.hover',
                          },
                        }}
                        onClick={() => handleSeleccionarPaciente(paciente)}
                      >
                        {/* RUT */}
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <BadgeIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="body2" fontFamily="monospace">
                              {datos.rut}
                            </Typography>
                          </Box>
                        </TableCell>

                        {/* Nombre */}
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                              <PersonIcon sx={{ fontSize: 18 }} />
                            </Avatar>
                            <Typography variant="body2" fontWeight="500">
                              {datos.nombre}
                            </Typography>
                          </Box>
                        </TableCell>

                        {/* Correo */}
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <EmailIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="body2">
                              {datos.correo}
                            </Typography>
                          </Box>
                        </TableCell>

                        {/* Contacto */}
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PhoneIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                            <Typography variant="body2" fontFamily="monospace">
                              {datos.contacto}
                            </Typography>
                          </Box>
                        </TableCell>

                        {/* Estado del Sistema */}
                        <TableCell>
                          <Chip
                            label={paciente.estado_actual_display}
                            size="small"
                            color={getColorEstado(paciente.estado_actual)}
                            sx={{ fontWeight: 500 }}
                          />
                        </TableCell>

                        {/* 🆕 NUEVA COLUMNA: Etapa Clínica Actual */}
                        <TableCell>
                          {paciente.etapa_actual ? (
                            <Tooltip 
                              title="Etapa actual del flujo clínico"
                              placement="top"
                            >
                              <Chip
                                icon={<TimelineIcon sx={{ fontSize: 16 }} />}
                                label={paciente.etapa_actual_display}
                                size="small"
                                color={getColorEtapa(paciente.etapa_actual)}
                                sx={{ 
                                  fontWeight: 600,
                                  '& .MuiChip-icon': {
                                    marginLeft: 1,
                                  }
                                }}
                              />
                            </Tooltip>
                          ) : (
                            <Tooltip title="Sin ruta clínica activa">
                              <Chip
                                label="Sin etapa"
                                size="small"
                                variant="outlined"
                                sx={{ 
                                  fontWeight: 500,
                                  color: 'text.secondary',
                                  borderColor: 'grey.300',
                                }}
                              />
                            </Tooltip>
                          )}
                        </TableCell>

                        {/* Urgencia */}
                        <TableCell>
                          <Chip
                            label={paciente.nivel_urgencia_display}
                            size="small"
                            color={getColorUrgencia(paciente.nivel_urgencia)}
                            sx={{ fontWeight: 500 }}
                          />
                        </TableCell>

                        {/* Acciones */}
                        <TableCell align="center">
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSeleccionarPaciente(paciente);
                            }}
                          >
                            Ver Detalle
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        No se encontraron pacientes que coincidan con la búsqueda
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        {/* Sección de Boxes */}
        <Paper elevation={3} sx={{ borderRadius: 2 }}>
          <Box sx={{ p: 3, bgcolor: 'secondary.main', color: 'white', borderRadius: '8px 8px 0 0' }}>
            <Typography variant="h5" fontWeight="600">
              Estado de Box's
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Monitoreo en tiempo real
            </Typography>
          </Box>

          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {boxes.map((box) => (
                <Grid item xs={12} sm={6} md={3} key={box.id}>
                  <Card
                    elevation={2}
                    sx={{
                      borderRadius: 2,
                      border: '2px solid',
                      borderColor: box.estado === 'DISPONIBLE' ? 'success.main' : 
                                  box.estado === 'OCUPADO' ? 'warning.main' : 'grey.300',
                      transition: 'all 0.3s',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4,
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6" fontWeight="600">
                          {box.numero}
                        </Typography>
                        {box.estado === 'DISPONIBLE' ? (
                          <CheckCircleIcon sx={{ color: 'success.main', fontSize: 28 }} />
                        ) : (
                          <WarningIcon sx={{ color: 'warning.main', fontSize: 28 }} />
                        )}
                      </Box>

                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {box.nombre}
                      </Typography>

                      <Chip
                        label={box.estado_display}
                        color={getColorBox(box.estado)}
                        size="small"
                        sx={{ mt: 1, fontWeight: 500 }}
                      />

                      {box.ultima_ocupacion && box.estado === 'OCUPADO' && (
                        <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
                          Ocupado desde: {new Date(box.ultima_ocupacion).toLocaleTimeString('es-CL', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        </Paper>

        {/* ============================================
            DRAWER ACTUALIZADO CON ETAPA ACTUAL
            ============================================ */}
        <Drawer
          anchor="right"
          open={drawerOpen}
          onClose={handleCloseDrawer}
          PaperProps={{
            sx: { width: { xs: '100%', sm: 500 } }
          }}
        >
          {pacienteSeleccionado && (
            <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ p: 3, bgcolor: 'primary.main', color: 'white' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <Box>
                    <Typography variant="h5" fontWeight="600" gutterBottom>
                      Detalle del Paciente
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                      Información completa
                    </Typography>
                  </Box>
                  <IconButton onClick={handleCloseDrawer} sx={{ color: 'white' }}>
                    <CloseIcon />
                  </IconButton>
                </Box>
              </Box>

              <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
                <Card elevation={0} sx={{ mb: 3, bgcolor: 'grey.50' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                      <Avatar sx={{ width: 60, height: 60, bgcolor: 'primary.main' }}>
                        <PersonIcon sx={{ fontSize: 32 }} />
                      </Avatar>
                      <Box>
                        <Typography variant="h6" fontWeight="600">
                          {obtenerDatosPaciente(pacienteSeleccionado).nombre}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {pacienteSeleccionado.edad} años • {pacienteSeleccionado.genero === 'M' ? 'Masculino' : pacienteSeleccionado.genero === 'F' ? 'Femenino' : 'Otro'}
                        </Typography>
                      </Box>
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <BadgeIcon sx={{ color: 'primary.main' }} />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            RUT
                          </Typography>
                          <Typography variant="body2" fontWeight="500" fontFamily="monospace">
                            {obtenerDatosPaciente(pacienteSeleccionado).rut}
                          </Typography>
                        </Box>
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <EmailIcon sx={{ color: 'primary.main' }} />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Correo
                          </Typography>
                          <Typography variant="body2" fontWeight="500">
                            {obtenerDatosPaciente(pacienteSeleccionado).correo}
                          </Typography>
                        </Box>
                      </Box>

                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <PhoneIcon sx={{ color: 'primary.main' }} />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            Contacto
                          </Typography>
                          <Typography variant="body2" fontWeight="500" fontFamily="monospace">
                            {obtenerDatosPaciente(pacienteSeleccionado).contacto}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>

                    {/* 🆕 CHIPS ACTUALIZADOS CON ETAPA */}
                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Chip
                        label={pacienteSeleccionado.estado_actual_display}
                        color={getColorEstado(pacienteSeleccionado.estado_actual)}
                        size="small"
                      />
                      {pacienteSeleccionado.etapa_actual && (
                        <Chip
                          icon={<TimelineIcon sx={{ fontSize: 14 }} />}
                          label={pacienteSeleccionado.etapa_actual_display}
                          color={getColorEtapa(pacienteSeleccionado.etapa_actual)}
                          size="small"
                          sx={{ fontWeight: 600 }}
                        />
                      )}
                      <Chip
                        label={pacienteSeleccionado.nivel_urgencia_display}
                        color={getColorUrgencia(pacienteSeleccionado.nivel_urgencia)}
                        size="small"
                      />
                    </Box>
                  </CardContent>
                </Card>

                {loadingRuta ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                    <CircularProgress />
                  </Box>
                ) : rutaClinica ? (
                  <Card elevation={0} sx={{ mb: 3, bgcolor: 'grey.50' }}>
                    <CardContent>
                      <Typography variant="h6" fontWeight="600" gutterBottom>
                        Estado de Ruta Clínica
                      </Typography>

                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Progreso
                          </Typography>
                          <Typography variant="body2" fontWeight="600">
                            {Math.round(rutaClinica.progreso_general)}%
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={rutaClinica.progreso_general}
                          sx={{ height: 8, borderRadius: 1 }}
                        />
                      </Box>

                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {/* 🆕 MOSTRAR ETAPA ACTUAL SINCRONIZADA */}
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Etapa Actual:
                          </Typography>
                          <Chip
                            label={rutaClinica.ruta_clinica.etapa_actual_display || 'No iniciada'}
                            size="small"
                            color={rutaClinica.ruta_clinica.etapa_actual ? 
                                  getColorEtapa(rutaClinica.ruta_clinica.etapa_actual) : 
                                  'default'}
                            sx={{ fontWeight: 500 }}
                          />
                        </Box>

                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Etapas Completadas:
                          </Typography>
                          <Typography variant="body2" fontWeight="500">
                            {rutaClinica.etapas_completadas} de {rutaClinica.etapas_totales}
                          </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Tiempo Transcurrido:
                          </Typography>
                          <Typography variant="body2" fontWeight="500">
                            {Math.floor(rutaClinica.tiempo_transcurrido_minutos / 60)}h {rutaClinica.tiempo_transcurrido_minutos % 60}m
                          </Typography>
                        </Box>

                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Estado:
                          </Typography>
                          <Chip
                            label={rutaClinica.ruta_clinica.estado_display}
                            size="small"
                            color={rutaClinica.ruta_clinica.estado === 'COMPLETADA' ? 'success' : 'primary'}
                          />
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ) : (
                  <Alert severity="info" sx={{ mb: 3 }}>
                    No hay ruta clínica registrada para este paciente
                  </Alert>
                )}

                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  endIcon={<ArrowForwardIcon />}
                  onClick={() => navigate(`/pacientes/${pacienteSeleccionado.id}`)}
                  sx={{ py: 1.5 }}
                >
                  Ver Detalle Completo
                </Button>
              </Box>
            </Box>
          )}
        </Drawer>
      </Container>
    </>
  );
};

export default Home;