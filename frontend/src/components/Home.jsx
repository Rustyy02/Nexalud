// frontend/src/components/Home.jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Chip,
  Paper,
  Avatar,
  Divider,
  CircularProgress,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Person as PersonIcon,
  ArrowForward as ArrowForwardIcon,
  MedicalServices as MedicalIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { pacientesService, rutasClinicasService, boxesService } from '../services/api';

const Home = () => {
  const navigate = useNavigate();
  
  const [pacientes, setPacientes] = useState([]);
  const [pacienteSeleccionado, setPacienteSeleccionado] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingRuta, setLoadingRuta] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarDatos();
    // Actualizar cada 30 segundos
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
    setLoadingRuta(true);
    
    try {
      // Obtener rutas clínicas del paciente
      const rutasRes = await pacientesService.getRutasClinicas(paciente.id);
      
      if (rutasRes.data && rutasRes.data.length > 0) {
        // Obtener la ruta más reciente
        const rutaActual = rutasRes.data[0];
        
        // Obtener el timeline completo
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

  const getEstadoEtapa = (etapa) => {
    if (!rutaClinica || !rutaClinica.timeline) return 'pending';
    
    const etapaTimeline = rutaClinica.timeline.find(t => t.etapa_key === etapa);
    if (!etapaTimeline) return 'pending';
    
    return etapaTimeline.estado;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <MedicalIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Nexalud
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sistema de Gestión de Pacientes
            </Typography>
          </Box>
        </Box>
        <Button
          variant="outlined"
          onClick={() => navigate('/boxes')}
        >
          Ver Solo Boxes
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Lista de Pacientes */}
        <Grid item xs={12} md={4}>
          <Paper elevation={3} sx={{ height: 'calc(100vh - 250px)', overflow: 'auto' }}>
            <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white', position: 'sticky', top: 0, zIndex: 1 }}>
              <Typography variant="h6" fontWeight="600">
                Lista de Pacientes
              </Typography>
              <Typography variant="body2">
                Buscar por Nombre o Rut
              </Typography>
            </Box>

            <List>
              {pacientes.map((paciente) => (
                <React.Fragment key={paciente.id}>
                  <ListItem
                    button
                    selected={pacienteSeleccionado?.id === paciente.id}
                    onClick={() => handleSeleccionarPaciente(paciente)}
                    sx={{
                      '&.Mui-selected': {
                        bgcolor: 'action.selected',
                        borderLeft: '4px solid',
                        borderColor: 'primary.main',
                      },
                    }}
                  >
                    <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                      <PersonIcon />
                    </Avatar>
                    <ListItemText
                      primary={
                        <Typography variant="subtitle1" fontWeight="600">
                          {paciente.identificador_hash.substring(0, 12)}...
                        </Typography>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          <Chip
                            label={paciente.estado_actual_display}
                            size="small"
                            color={getColorEstado(paciente.estado_actual)}
                            sx={{ mr: 1 }}
                          />
                          <Chip
                            label={paciente.nivel_urgencia_display}
                            size="small"
                            color={getColorUrgencia(paciente.nivel_urgencia)}
                          />
                        </Box>
                      }
                    />
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Detalle del Paciente Seleccionado */}
        <Grid item xs={12} md={8}>
          {!pacienteSeleccionado ? (
            <Paper
              elevation={3}
              sx={{
                height: 'calc(100vh - 250px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Box sx={{ textAlign: 'center' }}>
                <PersonIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Seleccione un paciente para ver su información
                </Typography>
              </Box>
            </Paper>
          ) : (
            <Box>
              {/* Card del Paciente */}
              <Card elevation={3} sx={{ mb: 3 }}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Avatar sx={{ width: 60, height: 60, bgcolor: 'primary.main' }}>
                        <PersonIcon sx={{ fontSize: 32 }} />
                      </Avatar>
                      <Box>
                        <Typography variant="h5" fontWeight="600">
                          Paciente {pacienteSeleccionado.identificador_hash.substring(0, 12)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          RUT: {pacienteSeleccionado.identificador_hash.substring(0, 12)}... • 
                          Edad: {pacienteSeleccionado.edad} • 
                          {pacienteSeleccionado.genero === 'M' ? 'Masculino' : pacienteSeleccionado.genero === 'F' ? 'Femenino' : 'Otro'}
                        </Typography>
                        <Box sx={{ mt: 1 }}>
                          <Chip
                            label={pacienteSeleccionado.estado_actual_display}
                            size="small"
                            color={getColorEstado(pacienteSeleccionado.estado_actual)}
                            sx={{ mr: 1 }}
                          />
                          <Chip
                            label={pacienteSeleccionado.nivel_urgencia_display}
                            size="small"
                            color={getColorUrgencia(pacienteSeleccionado.nivel_urgencia)}
                          />
                        </Box>
                      </Box>
                    </Box>
                    <Button
                      variant="contained"
                      endIcon={<ArrowForwardIcon />}
                      onClick={() => navigate(`/pacientes/${pacienteSeleccionado.id}`)}
                      size="large"
                    >
                      Ir a detalle
                    </Button>
                  </Box>

                  {/* Proceso de Ruta Clínica */}
                  {loadingRuta ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                      <CircularProgress />
                    </Box>
                  ) : rutaClinica ? (
                    <Box>
                      <Typography variant="h6" fontWeight="600" gutterBottom>
                        Proceso de Atención
                      </Typography>
                      
                      {/* Barra de Progreso */}
                      <Box sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Progreso General
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

                      {/* Etapas */}
                      <Grid container spacing={2}>
                        {rutaClinica.timeline.map((etapa) => (
                          <Grid item xs={6} sm={4} key={etapa.orden}>
                            <Card
                              variant="outlined"
                              sx={{
                                bgcolor: etapa.estado === 'COMPLETADA' ? 'success.light' : 
                                        etapa.es_actual ? 'primary.light' : 'grey.100',
                                borderWidth: etapa.es_actual ? 2 : 1,
                                borderColor: etapa.es_actual ? 'primary.main' : 'divider',
                              }}
                            >
                              <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {etapa.orden}. {etapa.etapa_label}
                                </Typography>
                                <Chip
                                  label={etapa.estado}
                                  size="small"
                                  color={
                                    etapa.estado === 'COMPLETADA' ? 'success' :
                                    etapa.estado === 'EN_PROCESO' ? 'primary' : 'default'
                                  }
                                  sx={{ mt: 1, fontSize: '0.7rem' }}
                                />
                              </CardContent>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>

                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Etapa Actual: <strong>{rutaClinica.ruta_clinica.etapa_actual_display || 'No iniciada'}</strong>
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Tiempo Transcurrido: <strong>{Math.floor(rutaClinica.tiempo_transcurrido_minutos / 60)}h {rutaClinica.tiempo_transcurrido_minutos % 60}m</strong>
                        </Typography>
                      </Box>
                    </Box>
                  ) : (
                    <Alert severity="info">
                      No hay ruta clínica registrada para este paciente
                    </Alert>
                  )}
                </CardContent>
              </Card>

              {/* Estado de Boxes */}
              <Card elevation={3}>
                <CardContent>
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    Atención en Box's
                  </Typography>
                  
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    {boxes.slice(0, 4).map((box) => (
                      <Grid item xs={6} sm={3} key={box.id}>
                        <Card
                          variant="outlined"
                          sx={{
                            textAlign: 'center',
                            p: 2,
                            bgcolor: box.estado === 'DISPONIBLE' ? 'success.light' : 'warning.light',
                          }}
                        >
                          <Typography variant="h6" fontWeight="600">
                            {box.numero}
                          </Typography>
                          <Chip
                            label={box.estado_display}
                            size="small"
                            color={getColorBox(box.estado)}
                            sx={{ mt: 1 }}
                          />
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={() => navigate('/boxes')}
                    sx={{ mt: 2 }}
                  >
                    Ir a Box's
                  </Button>
                </CardContent>
              </Card>
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Home;
