// frontend/src/components/DetallePaciente.jsx
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
  IconButton,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Home as HomeIcon,
  Security as SecurityIcon,
  MedicalServices as MedicalIcon,
  Science as ScienceIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { pacientesService, rutasClinicasService, boxesService } from '../services/api';

const DetallePaciente = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  
  const [paciente, setPaciente] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [boxes, setBoxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarDatos();
  }, [id]);

  const cargarDatos = async () => {
    try {
      setError('');
      setLoading(true);

      const [pacienteRes, boxesRes] = await Promise.all([
        pacientesService.getById(id),
        boxesService.getAll()
      ]);
      
      setPaciente(pacienteRes.data);
      setBoxes(boxesRes.data);

      // Obtener rutas clínicas
      const rutasRes = await pacientesService.getRutasClinicas(id);
      
      if (rutasRes.data && rutasRes.data.length > 0) {
        const rutaActual = rutasRes.data[0];
        const timelineRes = await rutasClinicasService.getTimeline(rutaActual.id);
        setRutaClinica(timelineRes.data);
      }

      setLoading(false);
    } catch (err) {
      setError('Error al cargar los datos del paciente');
      setLoading(false);
      console.error(err);
    }
  };

  const handleAvanzarEtapa = async () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return;

    try {
      await rutasClinicasService.avanzar(rutaClinica.ruta_clinica.id);
      await cargarDatos(); // Recargar datos
    } catch (err) {
      setError('Error al avanzar la etapa');
      console.error(err);
    }
  };

  const handleRetrocederEtapa = async () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return;

    try {
      await rutasClinicasService.retroceder(rutaClinica.ruta_clinica.id);
      await cargarDatos();
    } catch (err) {
      setError('Error al retroceder la etapa');
      console.error(err);
    }
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

  const getColorUrgencia = (urgencia) => {
    const colores = {
      'CRITICA': 'error',
      'ALTA': 'warning',
      'MEDIA': 'info',
      'BAJA': 'success',
    };
    return colores[urgencia] || 'default';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!paciente) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error">Paciente no encontrado</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <IconButton onClick={() => navigate('/')} sx={{ bgcolor: 'grey.100' }}>
            <ArrowBackIcon />
          </IconButton>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <MedicalIcon sx={{ fontSize: 40, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" fontWeight="bold">
                Nexalud
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Detalle del Paciente
              </Typography>
            </Box>
          </Box>
        </Box>

        <Button
          variant="contained"
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
        >
          Cerrar sesión
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Columna Izquierda - Lista de Pacientes */}
        <Grid item xs={12} md={3}>
          <Paper elevation={3} sx={{ height: 'calc(100vh - 250px)', overflow: 'auto' }}>
            <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white', position: 'sticky', top: 0, zIndex: 1 }}>
              <Typography variant="h6" fontWeight="600">
                Lista de Pacientes
              </Typography>
              <Typography variant="body2">
                Buscar por Nombre o Rut
              </Typography>
            </Box>
            {/* Aquí podrías agregar la lista de otros pacientes si lo necesitas */}
          </Paper>
        </Grid>

        {/* Columna Central - Detalle del Paciente */}
        <Grid item xs={12} md={9}>
          {/* Card Principal del Paciente */}
          <Card elevation={3} sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', gap: 3, mb: 4 }}>
                <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}>
                  <PersonIcon sx={{ fontSize: 40 }} />
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h4" fontWeight="bold" gutterBottom>
                    {paciente.identificador_hash.substring(0, 12)}...
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 3, mb: 2 }}>
                    <Typography variant="body1" color="text.secondary">
                      <strong>Rut:</strong> {paciente.identificador_hash.substring(0, 12)}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      <strong>Edad:</strong> {paciente.edad}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      <strong>Tipo de Sangre:</strong> O+
                    </Typography>
                  </Box>
                  <Chip
                    label={paciente.nivel_urgencia_display}
                    color={getColorUrgencia(paciente.nivel_urgencia)}
                    sx={{ mr: 1 }}
                  />
                </Box>
              </Box>

              {/* Proceso de Atención - Etapas */}
              {rutaClinica && (
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    Proceso de Atención
                  </Typography>
                  
                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    {rutaClinica.timeline.map((etapa) => (
                      <Grid item xs={6} sm={4} md={2} key={etapa.orden}>
                        <Card
                          variant="outlined"
                          sx={{
                            bgcolor: etapa.estado === 'COMPLETADA' ? 'success.main' : 
                                    etapa.es_actual ? 'primary.main' : 'grey.300',
                            color: etapa.estado !== 'PENDIENTE' ? 'white' : 'text.primary',
                            borderWidth: etapa.es_actual ? 3 : 1,
                            borderColor: etapa.es_actual ? 'primary.dark' : 'divider',
                            cursor: 'pointer',
                            transition: 'all 0.3s',
                            '&:hover': {
                              transform: 'translateY(-4px)',
                              boxShadow: 3,
                            },
                          }}
                        >
                          <CardContent sx={{ p: 2, textAlign: 'center', '&:last-child': { pb: 2 } }}>
                            <MedicalIcon sx={{ fontSize: 32, mb: 1 }} />
                            <Typography variant="body2" fontWeight="600">
                              {etapa.etapa_label}
                            </Typography>
                            {etapa.fecha_inicio && (
                              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                {new Date(etapa.fecha_inicio).toLocaleTimeString('es-CL', { 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </Typography>
                            )}
                            {etapa.es_actual && (
                              <Chip
                                label="En Curso"
                                size="small"
                                sx={{ 
                                  mt: 1, 
                                  bgcolor: 'white', 
                                  color: 'primary.main',
                                  fontWeight: 600,
                                  fontSize: '0.7rem'
                                }}
                              />
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  {/* Botones de Control */}
                  <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
                    <Button
                      variant="outlined"
                      onClick={handleRetrocederEtapa}
                      disabled={rutaClinica.ruta_clinica.porcentaje_completado === 0}
                    >
                      Retroceder Etapa
                    </Button>
                    <Button
                      variant="contained"
                      onClick={handleAvanzarEtapa}
                      disabled={rutaClinica.ruta_clinica.estado === 'COMPLETADA'}
                    >
                      Avanzar Etapa
                    </Button>
                  </Box>

                  <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <Typography variant="body2">
                      <strong>Progreso:</strong> {Math.round(rutaClinica.progreso_general)}% ({rutaClinica.etapas_completadas} de {rutaClinica.etapas_totales} etapas)
                    </Typography>
                    <Typography variant="body2">
                      <strong>Tiempo Total:</strong> {Math.floor(rutaClinica.tiempo_transcurrido_minutos / 60)}h {rutaClinica.tiempo_transcurrido_minutos % 60}m
                    </Typography>
                    <Typography variant="body2">
                      <strong>Estado:</strong> {rutaClinica.ruta_clinica.estado_display}
                    </Typography>
                  </Box>
                </Box>
              )}

              {/* Atención en Box's */}
              <Box sx={{ mb: 4 }}>
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
                          bgcolor: box.estado === 'DISPONIBLE' ? 'success.light' : 
                                  box.estado === 'OCUPADO' ? 'warning.light' : 'grey.100',
                        }}
                      >
                        <Typography variant="h6" fontWeight="600">
                          {box.numero}
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                          {box.nombre}
                        </Typography>
                        <Chip
                          label={box.estado_display}
                          size="small"
                          color={getColorBox(box.estado)}
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
              </Box>

              <Divider sx={{ my: 3 }} />

              {/* Datos del Paciente */}
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    Datos del paciente
                  </Typography>
                  
                  <List>
                    <ListItem>
                      <PhoneIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary="Contacto"
                        secondary="+56 9 7846 1789"
                      />
                    </ListItem>
                    <ListItem>
                      <HomeIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary="Dirección"
                        secondary="Cocalan 160, Llay-Llay, Valparaiso"
                      />
                    </ListItem>
                    <ListItem>
                      <SecurityIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary="Seguro"
                        secondary="Sura"
                      />
                    </ListItem>
                  </List>

                  {/* Notas */}
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="h6" fontWeight="600" gutterBottom>
                      Notas
                    </Typography>
                    <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="body2">
                        {paciente.metadatos_adicionales?.notas || 
                         "Paciente que sufrió caída desde 1 metro, niega pérdida del conocimiento. " +
                         "Posterior al evento refiere dolor de hombro, cadera y zona lumbar, con dificultad para caminar."}
                      </Typography>
                    </Paper>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  {/* Exámenes a Tomar */}
                  <Typography variant="h6" fontWeight="600" gutterBottom>
                    Exámenes a tomar
                  </Typography>
                  
                  <List>
                    <ListItem>
                      <ScienceIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary="• Toma de Radiografías en columna lumbosacra"
                      />
                    </ListItem>
                    <ListItem>
                      <ScienceIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary="• Toma de Radiografías en cadera"
                      />
                    </ListItem>
                    <ListItem>
                      <ScienceIcon sx={{ mr: 2, color: 'primary.main' }} />
                      <ListItemText
                        primary="• Toma de Resonancia magnética en hombro"
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DetallePaciente;
