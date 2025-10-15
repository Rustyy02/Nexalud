// frontend/src/components/EstadoBoxes.jsx
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
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { boxesService } from '../services/api';
import Navbar from './Navbar';

const EstadoBoxes = () => {
  const [boxes, setBoxes] = useState([]);
  const [atrasosEnHoras, setAtrasosEnHoras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  useEffect(() => {
    cargarBoxes();
    const interval = setInterval(cargarBoxes, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarBoxes = async () => {
    try {
      const response = await boxesService.getAll();
      setBoxes(response.data);
      setLoading(false);
      
      setAtrasosEnHoras([
        {
          id: 1,
          paciente: 'Maria Gomez',
          box: 'Box 4',
          atrasoMinutos: 20,
        }
      ]);
    } catch (err) {
      showSnackbar('Error al cargar los boxes', 'error');
      setLoading(false);
      console.error(err);
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({
      open: true,
      message,
      severity
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({
      ...snackbar,
      open: false
    });
  };

  const cambiarEstadoBox = async (boxId, nuevoEstado) => {
    try {
      if (nuevoEstado === 'OCUPADO') {
        await boxesService.ocupar(boxId);
        showSnackbar('Box marcado como ocupado', 'success');
      } else {
        await boxesService.liberar(boxId);
        showSnackbar('Box marcado como libre', 'success');
      }
      
      await cargarBoxes();
    } catch (err) {
      showSnackbar('Error al cambiar el estado del box', 'error');
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
    if (estado === 'DISPONIBLE') {
      return <CheckCircleIcon />;
    } else if (estado === 'OCUPADO') {
      return <WarningIcon />;
    }
    return <ScheduleIcon />;
  };

  const formatearHoraAtencion = (box) => {
    if (box.ultima_ocupacion) {
      const fecha = new Date(box.ultima_ocupacion);
      const hora = fecha.toLocaleTimeString('es-CL', {
        hour: '2-digit',
        minute: '2-digit',
      });
      const fechaFin = new Date(fecha.getTime() + 60 * 60 * 1000);
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
        {/* Sección de Boxes */}
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
                      <Chip
                        icon={getEstadoIcon(box.estado)}
                        label={box.estado_display}
                        color={getEstadoColor(box.estado)}
                        size="small"
                        sx={{ fontWeight: 500 }}
                      />
                    </Box>

                    {box.estado === 'OCUPADO' && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Hora de Atención: {formatearHoraAtencion(box)}
                      </Typography>
                    )}
                    {box.estado === 'DISPONIBLE' && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Hora de Atención:
                      </Typography>
                    )}

                    <Button
                      variant="contained"
                      fullWidth
                      size="large"
                      onClick={() =>
                        cambiarEstadoBox(
                          box.id,
                          box.estado === 'DISPONIBLE' ? 'OCUPADO' : 'DISPONIBLE'
                        )
                      }
                      disabled={box.estado === 'MANTENIMIENTO' || box.estado === 'FUERA_SERVICIO'}
                      sx={{
                        textTransform: 'none',
                        fontWeight: 500,
                        backgroundColor:
                          box.estado === 'DISPONIBLE' ? 'primary.main' : 'success.main',
                        '&:hover': {
                          backgroundColor:
                            box.estado === 'DISPONIBLE' ? 'primary.dark' : 'success.dark',
                        },
                      }}
                    >
                      {box.estado === 'DISPONIBLE' ? 'Marcar como Ocupado' : 'Marcar como Libre'}
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>

        {/* Sección de Atrasos */}
        <Paper elevation={2} sx={{ p: 3 }}>
          <Typography variant="h5" fontWeight="600" gutterBottom>
            Atrasos en Horas
          </Typography>

          {atrasosEnHoras.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              No hay atrasos registrados
            </Typography>
          ) : (
            <Box sx={{ mt: 2 }}>
              {atrasosEnHoras.map((atraso) => (
                <Card key={atraso.id} elevation={1} sx={{ mb: 2, p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="subtitle1" fontWeight="600">
                        {atraso.paciente}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Atraso en Atención: {atraso.atrasoMinutos} minutos
                      </Typography>
                    </Box>
                    <Chip
                      label={atraso.box}
                      color="success"
                      size="small"
                      sx={{ fontWeight: 500 }}
                    />
                  </Box>
                  <Button
                    variant="contained"
                    fullWidth
                    sx={{
                      mt: 2,
                      textTransform: 'none',
                      fontWeight: 500,
                    }}
                  >
                    Notificar a Profesional
                  </Button>
                </Card>
              ))}
            </Box>
          )}
        </Paper>

        {/* Snackbar para notificaciones */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={1000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert 
            onClose={handleCloseSnackbar} 
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

export default EstadoBoxes;