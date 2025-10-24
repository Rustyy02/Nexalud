// frontend/src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  LinearProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Person as PersonIcon,
  MeetingRoom as BoxIcon,
  MedicalServices as AtencionIcon,
  Timeline as RutaIcon,
  LocalHospital as MedicoIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  TrendingUp as TrendingIcon,
} from '@mui/icons-material';
import { dashboardService } from '../services/api';
import Navbar from './Navbar';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Dashboard = () => {
  const [metricas, setMetricas] = useState(null);
  const [tiempoReal, setTiempoReal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null);

  useEffect(() => {
    cargarMetricasIniciales();
    
    // Polling cada 10 segundos para datos en tiempo real
    const interval = setInterval(actualizarTiempoReal, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const cargarMetricasIniciales = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await dashboardService.getMetricas();
      setMetricas(response.data);
      setUltimaActualizacion(new Date());
    } catch (err) {
      console.error('Error al cargar métricas:', err);
      if (err.response?.status === 403) {
        setError('No tienes permisos para acceder al dashboard. Solo administradores.');
      } else {
        setError('Error al cargar las métricas del dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const actualizarTiempoReal = async () => {
    try {
      const response = await dashboardService.getTiempoReal();
      setTiempoReal(response.data);
      setUltimaActualizacion(new Date());
    } catch (err) {
      console.error('Error al actualizar tiempo real:', err);
    }
  };

  const handleRefresh = () => {
    cargarMetricasIniciales();
    actualizarTiempoReal();
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: 'calc(100vh - 64px)' 
        }}>
          <CircularProgress />
        </Box>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <Alert severity="error">{error}</Alert>
        </Container>
      </>
    );
  }

  if (!metricas) return null;

  // Datos para gráfico de tendencias
  const datosTendencias = metricas.tendencias_7_dias.map(dia => ({
    fecha: new Date(dia.fecha).toLocaleDateString('es-CL', { 
      day: '2-digit', 
      month: '2-digit' 
    }),
    Pacientes: dia.pacientes,
    Atenciones: dia.atenciones,
    Completadas: dia.completadas,
  }));

  // Datos para gráfico de pacientes por urgencia
  const datosUrgencia = Object.entries(metricas.pacientes.por_urgencia).map(
    ([key, value]) => ({
      name: value.label,
      value: value.count,
    })
  );

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 4 
        }}>
          <Box>
            <Typography variant="h4" fontWeight="600">
              Dashboard de Gestión
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Actualizado: {ultimaActualizacion?.toLocaleTimeString('es-CL')}
            </Typography>
          </Box>
          
          <Tooltip title="Actualizar datos">
            <IconButton onClick={handleRefresh} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Alertas */}
        {metricas.alertas.length > 0 && (
          <Box sx={{ mb: 3 }}>
            {metricas.alertas.map((alerta, index) => (
              <Alert 
                key={index} 
                severity={alerta.tipo} 
                sx={{ mb: 1 }}
                icon={alerta.tipo === 'warning' ? <WarningIcon /> : undefined}
              >
                <strong>{alerta.titulo}:</strong> {alerta.mensaje}
              </Alert>
            ))}
          </Box>
        )}

        {/* Tarjetas de Métricas Principales */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Pacientes */}
          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" color="text.secondary">
                    Pacientes
                  </Typography>
                  <PersonIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                </Box>
                <Typography variant="h3" fontWeight="700">
                  {metricas.pacientes.total}
                </Typography>
                <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                  +{metricas.pacientes.hoy} hoy
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    En espera: {metricas.pacientes.por_estado.EN_ESPERA?.count || 0}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Boxes */}
          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" color="text.secondary">
                    Boxes
                  </Typography>
                  <BoxIcon sx={{ fontSize: 40, color: 'warning.main' }} />
                </Box>
                <Typography variant="h3" fontWeight="700">
                  {metricas.boxes.disponibles}/{metricas.boxes.total}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Disponibles
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={metricas.boxes.tasa_ocupacion} 
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    Ocupación: {metricas.boxes.tasa_ocupacion}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Atenciones */}
          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" color="text.secondary">
                    Atenciones
                  </Typography>
                  <AtencionIcon sx={{ fontSize: 40, color: 'success.main' }} />
                </Box>
                <Typography variant="h3" fontWeight="700">
                  {metricas.atenciones.hoy}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Hoy
                </Typography>
                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Chip 
                    label={`${metricas.atenciones.en_curso} en curso`} 
                    size="small" 
                    color="primary"
                  />
                  {metricas.atenciones.retrasadas.length > 0 && (
                    <Chip 
                      label={`${metricas.atenciones.retrasadas.length} atrasos`} 
                      size="small" 
                      color="error"
                    />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Rutas Clínicas */}
          <Grid item xs={12} sm={6} md={3}>
            <Card elevation={3}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" color="text.secondary">
                    Rutas Clínicas
                  </Typography>
                  <RutaIcon sx={{ fontSize: 40, color: 'info.main' }} />
                </Box>
                <Typography variant="h3" fontWeight="700">
                  {metricas.rutas_clinicas.activas}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Activas
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">
                    Progreso promedio: {metricas.rutas_clinicas.progreso_promedio}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Gráficos */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Gráfico de Tendencias - Temporary Simplified Version */}
          <Grid item xs={12} md={8}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom>
                Tendencias - Últimos 7 Días
              </Typography>
              <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography color="text.secondary">
                  Gráfico temporalmente no disponible
                </Typography>
              </Box>
            </Paper>
          </Grid>

          {/* Gráfico de Urgencias - Temporary Simplified Version */}
          <Grid item xs={12} md={4}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom>
                Pacientes por Urgencia
              </Typography>
              <Box sx={{ height: 300 }}>
                {datosUrgencia.map((item, index) => (
                  <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">{item.name}</Typography>
                    <Chip label={item.value} size="small" />
                  </Box>
                ))}
              </Box>
            </Paper>
          </Grid>
        </Grid>
        {/* Top Médicos */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom>
                Top 5 Médicos - Atenciones Hoy
              </Typography>
              {metricas.medicos.top_5_hoy.length > 0 ? (
                <Box sx={{ mt: 2 }}>
                  {metricas.medicos.top_5_hoy.map((medico, index) => (
                    <Box 
                      key={medico.id}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        p: 2,
                        mb: 1,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        borderLeft: '4px solid',
                        borderLeftColor: 'primary.main',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="h6" color="primary.main" fontWeight="700">
                          #{index + 1}
                        </Typography>
                        <Box>
                          <Typography variant="body1" fontWeight="600">
                            {medico.nombre}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {medico.especialidad}
                          </Typography>
                        </Box>
                      </Box>
                      <Chip 
                        label={`${medico.atenciones} atenciones`}
                        color="primary"
                        size="small"
                      />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Alert severity="info" sx={{ mt: 2 }}>
                  No hay datos de atenciones hoy
                </Alert>
              )}
            </Paper>
          </Grid>

          {/* Atenciones por Tipo */}
          <Grid item xs={12} md={6}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="600" gutterBottom>
                Atenciones por Tipo - Hoy
              </Typography>
              <Box sx={{ mt: 2 }}>
                {Object.entries(metricas.atenciones.por_tipo)
                  .filter(([_, data]) => data.count > 0)
                  .sort(([_, a], [__, b]) => b.count - a.count)
                  .map(([key, data]) => (
                    <Box 
                      key={key}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        mb: 2,
                      }}
                    >
                      <Typography variant="body2">
                        {data.label}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1, ml: 2 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={(data.count / metricas.atenciones.hoy) * 100}
                          sx={{ flex: 1, height: 8, borderRadius: 1 }}
                        />
                        <Typography variant="body2" fontWeight="600" sx={{ minWidth: 40 }}>
                          {data.count}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                {Object.values(metricas.atenciones.por_tipo).every(d => d.count === 0) && (
                  <Alert severity="info">
                    No hay atenciones registradas hoy
                  </Alert>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Indicadores en Tiempo Real */}
        {tiempoReal && (
          <Paper 
            elevation={3} 
            sx={{ 
              p: 3, 
              mb: 4, 
              bgcolor: 'primary.light',
              color: 'white',
            }}
          >
            <Typography variant="h6" fontWeight="600" gutterBottom>
              📡 Estado en Tiempo Real
            </Typography>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="700">
                    {tiempoReal.boxes_disponibles}
                  </Typography>
                  <Typography variant="body2">
                    Boxes Disponibles
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="700">
                    {tiempoReal.atenciones_en_curso}
                  </Typography>
                  <Typography variant="body2">
                    Atenciones en Curso
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="700">
                    {tiempoReal.pacientes_en_espera}
                  </Typography>
                  <Typography variant="body2">
                    Pacientes en Espera
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight="700">
                    {tiempoReal.rutas_en_progreso}
                  </Typography>
                  <Typography variant="body2">
                    Rutas en Progreso
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            {/* Última Actividad */}
            {(tiempoReal.ultima_atencion || tiempoReal.ultimo_paciente) && (
              <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Última Actividad:
                </Typography>
                <Grid container spacing={2}>
                  {tiempoReal.ultima_atencion && (
                    <Grid item xs={12} md={6}>
                      <Box sx={{ 
                        bgcolor: 'rgba(255,255,255,0.2)', 
                        p: 2, 
                        borderRadius: 1 
                      }}>
                        <Typography variant="caption" display="block">
                          🏥 Última Atención Iniciada
                        </Typography>
                        <Typography variant="body2" fontWeight="600">
                          Paciente: {tiempoReal.ultima_atencion.paciente}
                        </Typography>
                        <Typography variant="caption">
                          Box: {tiempoReal.ultima_atencion.box} • {' '}
                          {new Date(tiempoReal.ultima_atencion.hora_inicio).toLocaleTimeString('es-CL')}
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                  {tiempoReal.ultimo_paciente && (
                    <Grid item xs={12} md={6}>
                      <Box sx={{ 
                        bgcolor: 'rgba(255,255,255,0.2)', 
                        p: 2, 
                        borderRadius: 1 
                      }}>
                        <Typography variant="caption" display="block">
                          👤 Último Paciente Ingresado
                        </Typography>
                        <Typography variant="body2" fontWeight="600">
                          {tiempoReal.ultimo_paciente.nombre}
                        </Typography>
                        <Typography variant="caption">
                          {tiempoReal.ultimo_paciente.estado} • {' '}
                          Urgencia: {tiempoReal.ultimo_paciente.urgencia}
                        </Typography>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              </Box>
            )}
          </Paper>
        )}

        {/* Atenciones Retrasadas */}
        {metricas.atenciones.retrasadas.length > 0 && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" fontWeight="600" gutterBottom color="error">
              ⚠️ Atenciones Retrasadas
            </Typography>
            <Box sx={{ mt: 2 }}>
              {metricas.atenciones.retrasadas.map((atraso) => (
                <Alert 
                  key={atraso.id} 
                  severity="warning" 
                  sx={{ mb: 1 }}
                >
                  <strong>Paciente:</strong> {atraso.paciente} • {' '}
                  <strong>Box:</strong> {atraso.box} • {' '}
                  <strong>Retraso:</strong> {atraso.retraso_minutos} minutos
                </Alert>
              ))}
            </Box>
          </Paper>
        )}
      </Container>
    </>
  );
};

export default Dashboard;