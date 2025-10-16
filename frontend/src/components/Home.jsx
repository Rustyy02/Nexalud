// frontend/src/components/Home.jsx
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

  useEffect(() => {
    cargarDatos();
    const interval = setInterval(cargarDatos, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarDatos = async () => {
    try {
      setError('');
      const [pacientesRes, boxesRes] = await Promise.all([
        pacientesService.getAll({ activo: true }),
        boxesService.getAll()
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

  const getColorEstado = (estado) => {
    const colores = {
      'EN_ESPERA': 'warning',
      'EN_CONSULTA': 'info',
      'EN_EXAMEN': 'primary',
      'PROCESO_PAUSADO': 'default',
      'ALTA_COMPLETA': 'success',
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
    return {
      nombre: paciente.metadatos_adicionales?.nombre || `Paciente ${paciente.identificador_hash.substring(0, 8)}`,
      rut: paciente.identificador_hash.substring(0, 12) + '...',
      correo: paciente.metadatos_adicionales?.correo || 'paciente@ejemplo.com',
      contacto: paciente.metadatos_adicionales?.contacto || '+56 9 0000 0000',
    };
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
              {pacientes.length} pacientes activos
            </Typography>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.50' }}>
                  <TableCell sx={{ fontWeight: 600 }}>Rut</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Nombre</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Correo</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Contacto</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Estado</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Urgencia</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 600 }}></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pacientes.map((paciente) => {
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
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <BadgeIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                          {datos.rut}
                        </Box>
                      </TableCell>
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
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <EmailIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                          {datos.correo}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <PhoneIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                          {datos.contacto}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={paciente.estado_actual_display}
                          size="small"
                          color={getColorEstado(paciente.estado_actual)}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={paciente.nivel_urgencia_display}
                          size="small"
                          color={getColorUrgencia(paciente.nivel_urgencia)}
                        />
                      </TableCell>
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
                })}
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

        {/* Drawer de Detalle del Paciente */}
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
                          <Typography variant="body2" fontWeight="500">
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
                          <Typography variant="body2" fontWeight="500">
                            {obtenerDatosPaciente(pacienteSeleccionado).contacto}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>

                    <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                      <Chip
                        label={pacienteSeleccionado.estado_actual_display}
                        color={getColorEstado(pacienteSeleccionado.estado_actual)}
                        size="small"
                      />
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
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Etapa Actual:
                          </Typography>
                          <Typography variant="body2" fontWeight="500">
                            {rutaClinica.ruta_clinica.etapa_actual_display || 'No iniciada'}
                          </Typography>
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