// frontend/src/components/DetallePaciente.jsx - VERSIÓN CORREGIDA
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Person as PersonIcon,
  Phone as PhoneIcon,
  Home as HomeIcon,
  Security as SecurityIcon,
  MedicalServices as MedicalIcon,
  History as HistoryIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { pacientesService, rutasClinicasService } from '../services/api';
import Navbar from './Navbar';

const DetallePaciente = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  // Estados principales
  const [paciente, setPaciente] = useState(null);
  const [rutaClinica, setRutaClinica] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // NUEVOS ESTADOS - Faltaban estos
  const [dialogObservaciones, setDialogObservaciones] = useState(false);
  const [dialogHistorial, setDialogHistorial] = useState(false);
  const [observaciones, setObservaciones] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    cargarDatos();
    const interval = setInterval(cargarDatos, 30000);
    return () => clearInterval(interval);
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
        
        const historialRes = await rutasClinicasService.getHistorial(rutaActual.id);
        setHistorial(historialRes.data.historial || []);
      }

      setLoading(false);
    } catch (err) {
      setError('Error al cargar los datos del paciente');
      setLoading(false);
      console.error(err);
    }
  };

  const handleAvanzarEtapa = () => {
    setDialogObservaciones(true);
  };

  const handleAvanzarConObservaciones = async () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return;

    try {
      setActionLoading(true);
      await rutasClinicasService.avanzar(
        rutaClinica.ruta_clinica.id,
        { observaciones }
      );
      setDialogObservaciones(false);
      setObservaciones('');
      await cargarDatos();
    } catch (err) {
      setError(err.response?.data?.mensaje || 'Error al avanzar la etapa');
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetrocederEtapa = async () => {
    if (!rutaClinica || !rutaClinica.ruta_clinica) return;

    try {
      setActionLoading(true);
      await rutasClinicasService.retroceder(rutaClinica.ruta_clinica.id);
      await cargarDatos();
    } catch (err) {
      setError(err.response?.data?.mensaje || 'Error al retroceder la etapa');
      console.error(err);
    } finally {
      setActionLoading(false);
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
    // Verificar que metadatos_adicionales sea un objeto
    const metadatos = paciente.metadatos_adicionales || {};
    
    return {
      nombre: metadatos.nombre || `Paciente ${paciente.identificador_hash.substring(0, 8)}`,
      rut: metadatos.rut_original || paciente.identificador_hash.substring(0, 12),
      edad: paciente.edad,
      tipoSangre: metadatos.tipo_sangre || paciente.tipo_sangre || 'O+',
      contacto: metadatos.contacto || '+56 9 7846 1789',
      direccion: metadatos.direccion || 'Sin dirección registrada',
      seguro: metadatos.seguro || 'Sin seguro',
      alergias: paciente.alergias || metadatos.alergias || 'Sin alergias registradas',
      condiciones: paciente.condiciones_preexistentes || metadatos.condiciones || 'Sin condiciones',
      medicamentos: paciente.medicamentos_actuales || metadatos.medicamentos || 'Sin medicamentos',
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

        {/* Alertas de Retrasos */}
        {rutaClinica?.retrasos && rutaClinica.retrasos.length > 0 && (
          <Alert severity="error" icon={<WarningIcon />} sx={{ mb: 3 }}>
            <Typography variant="subtitle2" fontWeight="600">
              ⚠️ Se detectaron {rutaClinica.retrasos.length} etapa(s) con retraso
            </Typography>
            {rutaClinica.retrasos.map((retraso, index) => (
              <Typography key={index} variant="body2" sx={{ mt: 0.5 }}>
                • {retraso.etapa_label}: {retraso.retraso_minutos} minutos de retraso
              </Typography>
            ))}
          </Alert>
        )}

        {/* Card Principal del Paciente */}
        <Card elevation={3} sx={{ mb: 3 }}>
          <CardContent>
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
              
              <Button
                variant="outlined"
                startIcon={<HistoryIcon />}
                onClick={() => setDialogHistorial(true)}
                size="small"
              >
                Ver Historial
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Proceso de Atención - Etapas */}
            {rutaClinica && (
              <Box sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" fontWeight="600">
                    Proceso de Atención
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {rutaClinica.ruta_clinica.estado === 'EN_PROGRESO' && (
                      <>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={handleRetrocederEtapa}
                          disabled={actionLoading || rutaClinica.ruta_clinica.indice_etapa_actual === 0}
                        >
                          Retroceder
                        </Button>
                        <Button
                          variant="contained"
                          size="small"
                          onClick={handleAvanzarEtapa}
                          disabled={actionLoading}
                        >
                          Avanzar Etapa
                        </Button>
                      </>
                    )}
                  </Box>
                </Box>

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
                          borderColor: etapa.retrasada ? 'error.main' : 
                                      etapa.es_actual ? 'primary.dark' : 'divider',
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
                          {etapa.retrasada && (
                            <Chip
                              label="Retrasada"
                              size="small"
                              color="error"
                              sx={{ mt: 1, fontSize: '0.7rem' }}
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

            {/* Información Médica Adicional */}
            <Divider sx={{ my: 3 }} />
            <Typography variant="h6" fontWeight="600" gutterBottom>
              Información Médica
            </Typography>

            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={4}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
                  <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                    ⚠️ Alergias
                  </Typography>
                  <Typography variant="body2">
                    {datos.alergias}
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
                  <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                    📋 Condiciones Preexistentes
                  </Typography>
                  <Typography variant="body2">
                    {datos.condiciones}
                  </Typography>
                </Paper>
              </Grid>

              <Grid item xs={12} md={4}>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                  <Typography variant="subtitle2" fontWeight="600" gutterBottom>
                    💊 Medicamentos Actuales
                  </Typography>
                  <Typography variant="body2">
                    {datos.medicamentos}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Diálogo de Observaciones */}
        <Dialog 
          open={dialogObservaciones} 
          onClose={() => !actionLoading && setDialogObservaciones(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            Agregar Observaciones al Avanzar
          </DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Observaciones sobre esta etapa"
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                placeholder="Ej: Paciente presenta mejoría, derivado a laboratorio"
                helperText="Opcional: Agregue notas sobre esta etapa antes de avanzar"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button 
              onClick={() => setDialogObservaciones(false)}
              disabled={actionLoading}
            >
              Cancelar
            </Button>
            <Button 
              onClick={handleAvanzarConObservaciones}
              variant="contained"
              disabled={actionLoading}
            >
              {actionLoading ? 'Procesando...' : 'Avanzar'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Diálogo de Historial */}
        <Dialog 
          open={dialogHistorial} 
          onClose={() => setDialogHistorial(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HistoryIcon />
              Historial de Cambios
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            {historial.length === 0 ? (
              <Alert severity="info">
                No hay registros en el historial
              </Alert>
            ) : (
              <List>
                {historial.map((entrada, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip 
                              label={entrada.accion} 
                              size="small" 
                              color="primary"
                            />
                            {entrada.desde && entrada.hacia && (
                              <Typography variant="body2">
                                {entrada.desde} → {entrada.hacia}
                              </Typography>
                            )}
                          </Box>
                        }
                        secondary={
                          <>
                            <Typography variant="caption" display="block">
                              {new Date(entrada.timestamp).toLocaleString('es-CL')}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Usuario: {entrada.usuario}
                            </Typography>
                            {entrada.motivo && (
                              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                Motivo: {entrada.motivo}
                              </Typography>
                            )}
                          </>
                        }
                      />
                    </ListItem>
                    {index < historial.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogHistorial(false)}>
              Cerrar
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </>
  );
};

export default DetallePaciente;