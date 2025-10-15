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
} from '@mui/material';
import {
  Person as PersonIcon,
  Phone as PhoneIcon,
  Home as HomeIcon,
  Security as SecurityIcon,
  MedicalServices as MedicalIcon,
} from '@mui/icons-material';
import { useParams } from 'react-router-dom';
import { pacientesService, rutasClinicasService } from '../services/api';
import Navbar from './Navbar';

const DetallePaciente = () => {
  const { id } = useParams();
  
  const [paciente, setPaciente] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarDatos();
  }, [id]);

  const cargarDatos = async () => {
    try {
      setError('');
      setLoading(true);

      const pacienteRes = await pacientesService.getById(id);
      setPaciente(pacienteRes.data);

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
      await cargarDatos();
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

  const getColorUrgencia = (urgencia) => {
    const colores = {
      'CRITICA': 'error',
      'ALTA': 'warning',
      'MEDIA': 'info',
      'BAJA': 'success',
    };
    return colores[urgencia] || 'default';
  };

  const obtenerDatosPaciente = (paciente) => {
    return {
      nombre: paciente.metadatos_adicionales?.nombre || `Ana Torres`,
      rut: paciente.identificador_hash.substring(0, 12),
      edad: paciente.edad,
      tipoSangre: paciente.metadatos_adicionales?.tipo_sangre || 'O+',
      contacto: paciente.metadatos_adicionales?.contacto || '+56 9 7846 1789',
      direccion: paciente.metadatos_adicionales?.direccion || 'Cocalan 160, Llay-Llay, Valparaiso',
      seguro: paciente.metadatos_adicionales?.seguro || 'Sura',
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

  if (!paciente) {
    return (
      <>
        <Navbar />
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <Alert severity="error">Paciente no encontrado</Alert>
        </Container>
      </>
    );
  }

  const datos = obtenerDatosPaciente(paciente);

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        {/* Card Principal del Paciente */}
        <Card elevation={3} sx={{ mb: 3 }}>
          <CardContent>
            {/* Header con información básica */}
            <Box sx={{ display: 'flex', gap: 3, mb: 4 }}>
              <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}>
                <PersonIcon sx={{ fontSize: 40 }} />
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                  {datos.nombre}
                </Typography>
                <Box sx={{ display: 'flex', gap: 3, mb: 2, flexWrap: 'wrap' }}>
                  <Typography variant="body1" color="text.secondary">
                    <strong>Rut:</strong> {datos.rut}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    <strong>Edad:</strong> {datos.edad}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    <strong>Tipo de Sangre:</strong> {datos.tipoSangre}
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Proceso de Atención - Etapas */}
            {rutaClinica && (
              <Box sx={{ mb: 4 }}>
                <Grid container spacing={2}>
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
                              label="En curso"
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
                          {etapa.estado === 'PENDIENTE' && (
                            <Typography variant="caption" display="block" sx={{ mt: 0.5, color: 'text.secondary' }}>
                              Pendiente
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            )}

            <Divider sx={{ my: 3 }} />

            {/* Datos del Paciente */}
            <Typography variant="h6" fontWeight="600" gutterBottom>
              Datos del paciente
            </Typography>
            
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={4}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <PhoneIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Contacto
                      </Typography>
                      <Typography variant="body1" fontWeight="600">
                        {datos.contacto}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Grid>

              <Grid item xs={12} sm={4}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <HomeIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Dirección
                      </Typography>
                      <Typography variant="body2" fontWeight="600">
                        {datos.direccion}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Grid>

              <Grid item xs={12} sm={4}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <SecurityIcon sx={{ color: 'primary.main', fontSize: 32 }} />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Seguro
                      </Typography>
                      <Typography variant="body1" fontWeight="600">
                        {datos.seguro}
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default DetallePaciente;
