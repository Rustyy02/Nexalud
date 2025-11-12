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
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
  Stack,
  Badge,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  useTheme,
} from '@mui/material';
import {
  Person as PersonIcon,
  MeetingRoom as BoxIcon,
  MedicalServices as AtencionIcon,
  Timeline as RutaIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Download as DownloadIcon,
  PictureAsPdf as PdfIcon,
  Image as ImageIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  AccessTime as AccessTimeIcon,
  LocalHospital as LocalHospitalIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  EventAvailable as EventAvailableIcon,
  EventBusy as EventBusyIcon,
  PauseCircle as PauseCircleIcon,
  Cancel as CancelIcon,
  Lightbulb as LightbulbIcon,
} from '@mui/icons-material';
import { dashboardService } from '../services/api';
import Navbar from './Navbar';
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  AreaChart,
  Area,
  ComposedChart,
} from 'recharts';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { useRef } from 'react';

const COLORS = {
  primary: '#0088FE',
  success: '#00C49F',
  warning: '#FFBB28',
  error: '#FF8042',
  info: '#8884D8',
  purple: '#8B5CF6',
  pink: '#EC4899',
  indigo: '#6366F1',
};

const Dashboard = () => {
  const theme = useTheme();
  const dashboardRef = useRef(null);
  const [anchorElExport, setAnchorElExport] = useState(null);
  const [exportando, setExportando] = useState(false);
  const [metricas, setMetricas] = useState(null);
  const [tiempoReal, setTiempoReal] = useState(null);
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null);

  const handleExportMenuOpen = (event) => {
    setAnchorElExport(event.currentTarget);
  };

  const handleExportMenuClose = () => {
    setAnchorElExport(null);
  };

  const exportarComoPNG = async () => {
    handleExportMenuClose();
    setExportando(true);

    try {
      const element = dashboardRef.current;
      
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#f5f5f5',
      });

      const imgData = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `dashboard-nexalud-${new Date().toISOString().split('T')[0]}.png`;
      link.href = imgData;
      link.click();
    } catch (error) {
      console.error('Error al exportar PNG:', error);
    } finally {
      setExportando(false);
    }
  };

  const exportarComoPDF = async () => {
    handleExportMenuClose();
    setExportando(true);

    try {
      const element = dashboardRef.current;
      
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#f5f5f5',
      });

      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const imgWidth = 210;
      const pageHeight = 297;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      let heightLeft = imgHeight;
      let position = 0;

      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
      heightLeft -= pageHeight;

      while (heightLeft > 0) {
        position = heightLeft - imgHeight;
        pdf.addPage();
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
      }

      pdf.save(`dashboard-nexalud-${new Date().toISOString().split('T')[0]}.pdf`);
    } catch (error) {
      console.error('Error al exportar PDF:', error);
    } finally {
      setExportando(false);
    }
  };

  useEffect(() => {
    cargarMetricasIniciales();
    cargarInsights();
    
    const interval = setInterval(() => {
      actualizarTiempoReal();
      cargarInsights();
    }, 10000);
    
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

  const cargarInsights = async () => {
    try {
      const response = await dashboardService.getNexaThinkInsights();
      setInsights(response.data.insights || []);
    } catch (err) {
      console.error('Error al cargar insights:', err);
    }
  };

  const handleRefresh = () => {
    cargarMetricasIniciales();
    actualizarTiempoReal();
    cargarInsights();
  };

  // Componente para tarjeta de métrica mejorada
  const MetricCard = ({ title, value, subtitle, icon: Icon, color, trend, trendValue, loading: cardLoading }) => (
    <Card 
      elevation={0} 
      sx={{ 
        height: '100%',
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: theme.shadows[4],
          borderColor: color,
        }
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" fontWeight={600}>
            {title}
          </Typography>
          <Avatar 
            sx={{ 
              bgcolor: `${color}15`, 
              width: 48, 
              height: 48,
            }}
          >
            <Icon sx={{ color: color, fontSize: 28 }} />
          </Avatar>
        </Box>
        
        {cardLoading ? (
          <CircularProgress size={30} />
        ) : (
          <>
            <Typography variant="h3" fontWeight="700" sx={{ mb: 1, color: color }}>
              {value}
            </Typography>
            
            {subtitle && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {subtitle}
              </Typography>
            )}
            
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {trend === 'up' ? (
                  <TrendingUpIcon sx={{ fontSize: 18, color: 'success.main' }} />
                ) : (
                  <TrendingDownIcon sx={{ fontSize: 18, color: 'error.main' }} />
                )}
                <Typography 
                  variant="caption" 
                  sx={{ 
                    color: trend === 'up' ? 'success.main' : 'error.main',
                    fontWeight: 600,
                  }}
                >
                  {trendValue}
                </Typography>
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );

  // Componente para insights de NexaThink
  const InsightCard = ({ insight }) => {
    const getIconByType = (type) => {
      switch(type) {
        case 'alert': return <WarningIcon />;
        case 'warning': return <WarningIcon />;
        case 'success': return <CheckCircleIcon />;
        case 'info': return <LightbulbIcon />;
        default: return <LightbulbIcon />;
      }
    };

    const getColorByPriority = (priority) => {
      switch(priority) {
        case 'crítica': return 'error';
        case 'alta': return 'warning';
        case 'media': return 'info';
        case 'baja': return 'success';
        default: return 'info';
      }
    };

    return (
      <Alert 
        severity={getColorByPriority(insight.priority)}
        icon={getIconByType(insight.type)}
        sx={{ 
          mb: 1.5,
          borderLeft: '4px solid',
          borderLeftColor: `${getColorByPriority(insight.priority)}.main`,
        }}
      >
        <Typography variant="body2" fontWeight={600} gutterBottom>
          {insight.message}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {insight.recommendation}
        </Typography>
        <Chip 
          label={insight.priority.toUpperCase()}
          size="small" 
          color={getColorByPriority(insight.priority)}
          sx={{ ml: 1, height: 20 }}
        />
      </Alert>
    );
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: 'calc(100vh - 64px)',
          gap: 2,
        }}>
          <CircularProgress size={60} />
          <Typography variant="h6" color="text.secondary">
            Cargando dashboard...
          </Typography>
        </Box>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <Container maxWidth="xl" sx={{ py: 4 }}>
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
          <Button variant="contained" onClick={handleRefresh}>
            Reintentar
          </Button>
        </Container>
      </>
    );
  }

  if (!metricas) return null;

  // Preparar datos para gráficos
  const datosTendencias = metricas.tendencias_7_dias.map(dia => ({
    fecha: new Date(dia.fecha).toLocaleDateString('es-CL', { 
      day: '2-digit', 
      month: '2-digit' 
    }),
    Pacientes: dia.pacientes,
    Atenciones: dia.atenciones,
    Completadas: dia.completadas,
  }));

  const datosUrgencia = Object.entries(metricas.pacientes.por_urgencia).map(
    ([key, value]) => ({
      name: value.label,
      value: value.count,
      fill: key === 'CRITICA' ? COLORS.error : 
            key === 'ALTA' ? COLORS.warning :
            key === 'MEDIA' ? COLORS.info :
            COLORS.success,
    })
  );

  const datosEstadoPacientes = Object.entries(metricas.pacientes.por_estado).map(
    ([key, value]) => ({
      name: value.label,
      value: value.count,
    })
  );

  const datosAtencionesEstado = Object.entries(metricas.atenciones.por_tipo)
    .map(([key, value]) => ({
      name: value.label.length > 20 ? value.label.substring(0, 20) + '...' : value.label,
      cantidad: value.count,
    }))
    .filter(item => item.cantidad > 0);

  // Datos para radar chart de eficiencia
  const datosEficiencia = [
    {
      categoria: 'Boxes',
      valor: metricas.boxes.tasa_ocupacion,
      fullMark: 100,
    },
    {
      categoria: 'Completitud',
      valor: metricas.atenciones.completadas_hoy > 0 
        ? (metricas.atenciones.completadas_hoy / metricas.atenciones.hoy) * 100 
        : 0,
      fullMark: 100,
    },
    {
      categoria: 'Rutas',
      valor: metricas.rutas_clinicas.progreso_promedio,
      fullMark: 100,
    },
    {
      categoria: 'Puntualidad',
      valor: metricas.atenciones.retrasadas.length === 0 ? 100 : 
             Math.max(0, 100 - (metricas.atenciones.retrasadas.length / metricas.atenciones.en_curso) * 100),
      fullMark: 100,
    },
  ];

  return (
    <>
      <Navbar />
      <Box sx={{ bgcolor: '#f8f9fa', minHeight: '100vh', pb: 4 }}>
        <Container maxWidth="xl" sx={{ py: 4 }}>
          {/* Header con gradiente */}
          <Paper
            elevation={0}
            sx={{
              p: 4,
              mb: 4,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: 3,
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h3" fontWeight="700" gutterBottom>
                  🏥 Dashboard Nexalud
                </Typography>
                <Typography variant="h6" sx={{ opacity: 0.9 }}>
                  Análisis en Tiempo Real del Sistema de Gestión Clínica
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, opacity: 0.8 }}>
                  📊 Actualizado: {ultimaActualizacion?.toLocaleString('es-CL')}
                </Typography>
              </Box>
              
              <Stack direction="row" spacing={2}>
                <Tooltip title="Exportar Dashboard">
                  <IconButton
                    onClick={handleExportMenuOpen}
                    disabled={exportando}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                      color: 'white',
                    }}
                  >
                    {exportando ? <CircularProgress size={24} color="inherit" /> : <DownloadIcon />}
                  </IconButton>
                </Tooltip>

                <Tooltip title="Actualizar datos">
                  <IconButton 
                    onClick={handleRefresh}
                    sx={{
                      bgcolor: 'rgba(255,255,255,0.2)',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
                      color: 'white',
                    }}
                  >
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Stack>
            </Box>

            {/* Menú de exportación */}
            <Menu
              anchorEl={anchorElExport}
              open={Boolean(anchorElExport)}
              onClose={handleExportMenuClose}
            >
              <MenuItem onClick={exportarComoPNG}>
                <ListItemIcon>
                  <ImageIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>Exportar como PNG</ListItemText>
              </MenuItem>
              <MenuItem onClick={exportarComoPDF}>
                <ListItemIcon>
                  <PdfIcon fontSize="small" color="error" />
                </ListItemIcon>
                <ListItemText>Exportar como PDF</ListItemText>
              </MenuItem>
            </Menu>
          </Paper>

          <Box ref={dashboardRef}>
            {/* NexaThink Insights */}
            {insights.length > 0 && (
              <Paper elevation={0} sx={{ p: 3, mb: 4, border: '1px solid', borderColor: 'divider' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <AssessmentIcon sx={{ color: 'primary.main', fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="700">
                    🧠 NexaThink AI - Insights Inteligentes
                  </Typography>
                  <Chip 
                    label={`${insights.length} insights`} 
                    size="small" 
                    color="primary" 
                  />
                </Box>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  {insights.slice(0, 6).map((insight, index) => (
                    <Grid item xs={12} md={6} key={index}>
                      <InsightCard insight={insight} />
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            )}

            {/* Tarjetas de Métricas Principales - Rediseñadas */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Total Pacientes"
                  value={metricas.pacientes.total}
                  subtitle={`+${metricas.pacientes.hoy} nuevos hoy`}
                  icon={PersonIcon}
                  color={COLORS.primary}
                  trend="up"
                  trendValue={`${metricas.pacientes.hoy} hoy`}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Boxes Disponibles"
                  value={`${metricas.boxes.disponibles}/${metricas.boxes.total}`}
                  subtitle={`Ocupación: ${metricas.boxes.tasa_ocupacion}%`}
                  icon={BoxIcon}
                  color={COLORS.warning}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Atenciones Hoy"
                  value={metricas.atenciones.hoy}
                  subtitle={`${metricas.atenciones.completadas_hoy} completadas`}
                  icon={AtencionIcon}
                  color={COLORS.success}
                  trend={metricas.atenciones.en_curso > 0 ? "up" : "down"}
                  trendValue={`${metricas.atenciones.en_curso} en curso`}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Rutas Activas"
                  value={metricas.rutas_clinicas.activas}
                  subtitle={`${metricas.rutas_clinicas.progreso_promedio}% progreso`}
                  icon={RutaIcon}
                  color={COLORS.info}
                />
              </Grid>
            </Grid>

            {/* Tarjetas adicionales de métricas */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Tiempo Promedio"
                  value={`${metricas.atenciones.tiempo_promedio_minutos} min`}
                  subtitle="Por atención"
                  icon={AccessTimeIcon}
                  color={COLORS.purple}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Médicos Activos"
                  value={metricas.medicos.atendiendo_hoy}
                  subtitle={`de ${metricas.medicos.total_activos} totales`}
                  icon={LocalHospitalIcon}
                  color={COLORS.pink}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Rutas Completadas"
                  value={metricas.rutas_clinicas.completadas_hoy}
                  subtitle="Hoy"
                  icon={CheckCircleIcon}
                  color={COLORS.success}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <MetricCard
                  title="Rutas Pausadas"
                  value={metricas.rutas_clinicas.pausadas}
                  subtitle={metricas.rutas_clinicas.con_retraso ? `${metricas.rutas_clinicas.con_retraso} con retraso` : 'Sin retrasos'}
                  icon={PauseCircleIcon}
                  color={metricas.rutas_clinicas.con_retraso > 0 ? COLORS.error : COLORS.warning}
                />
              </Grid>
            </Grid>

            {/* Gráficos Principales */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Tendencias - Mejorado */}
              <Grid item xs={12} lg={8}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3, 
                    height: '100%',
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h6" fontWeight="700" gutterBottom>
                    📈 Tendencias - Últimos 7 Días
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  <ResponsiveContainer width="100%" height={400}>
                    <ComposedChart data={datosTendencias}>
                      <defs>
                        <linearGradient id="colorPacientes" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0.1}/>
                        </linearGradient>
                        <linearGradient id="colorAtenciones" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={COLORS.success} stopOpacity={0.8}/>
                          <stop offset="95%" stopColor={COLORS.success} stopOpacity={0.1}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                      <XAxis 
                        dataKey="fecha" 
                        tick={{ fontSize: 12 }}
                        stroke="#666"
                      />
                      <YAxis 
                        tick={{ fontSize: 12 }}
                        stroke="#666"
                      />
                      <RechartsTooltip 
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #ddd',
                          borderRadius: 8,
                          padding: 12,
                        }}
                      />
                      <Legend />
                      <Area 
                        type="monotone" 
                        dataKey="Pacientes" 
                        stroke={COLORS.primary}
                        fill="url(#colorPacientes)"
                        strokeWidth={2}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="Atenciones" 
                        stroke={COLORS.success}
                        strokeWidth={3}
                        dot={{ r: 4 }}
                      />
                      <Bar 
                        dataKey="Completadas" 
                        fill={COLORS.warning}
                        radius={[8, 8, 0, 0]}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              {/* Radar de Eficiencia */}
              <Grid item xs={12} lg={4}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3, 
                    height: '100%',
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h6" fontWeight="700" gutterBottom>
                    ⚡ Eficiencia General
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  <ResponsiveContainer width="100%" height={400}>
                    <RadarChart data={datosEficiencia}>
                      <PolarGrid stroke="#e0e0e0" />
                      <PolarAngleAxis 
                        dataKey="categoria" 
                        tick={{ fontSize: 12 }}
                      />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} />
                      <Radar 
                        name="Eficiencia" 
                        dataKey="valor" 
                        stroke={COLORS.primary}
                        fill={COLORS.primary}
                        fillOpacity={0.6}
                      />
                      <RechartsTooltip />
                    </RadarChart>
                  </ResponsiveContainer>
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      Métricas de rendimiento del sistema
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
            </Grid>

            {/* Segunda fila de gráficos */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
              {/* Pacientes por Urgencia - Mejorado */}
              <Grid item xs={12} md={4}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h6" fontWeight="700" gutterBottom>
                    🚨 Urgencias
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={datosUrgencia}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => 
                          `${name}: ${(percent * 100).toFixed(0)}%`
                        }
                        outerRadius={100}
                        dataKey="value"
                      >
                        {datosUrgencia.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              {/* Estado de Pacientes */}
              <Grid item xs={12} md={4}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h6" fontWeight="700" gutterBottom>
                    👥 Estados de Pacientes
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={datosEstadoPacientes}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        labelLine={false}
                        label={({ value }) => value > 0 ? value : ''}
                        dataKey="value"
                      >
                        {datosEstadoPacientes.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={Object.values(COLORS)[index % Object.values(COLORS).length]} 
                          />
                        ))}
                      </Pie>
                      <RechartsTooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </Paper>
              </Grid>

              {/* Atenciones por Tipo */}
              <Grid item xs={12} md={4}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3,
                    border: '1px solid',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="h6" fontWeight="700" gutterBottom>
                    📋 Tipos de Atención
                  </Typography>
                  <Divider sx={{ mb: 3 }} />
                  {datosAtencionesEstado.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart 
                        data={datosAtencionesEstado}
                        layout="vertical"
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis 
                          dataKey="name" 
                          type="category" 
                          width={120}
                          tick={{ fontSize: 11 }}
                        />
                        <RechartsTooltip />
                        <Bar 
                          dataKey="cantidad" 
                          fill={COLORS.primary}
                          radius={[0, 8, 8, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      height: 300 
                    }}>
                      <Typography variant="body2" color="text.secondary">
                        No hay atenciones registradas hoy
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
            </Grid>

            {/* Top Médicos - Mejorado */}
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                mb: 4,
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Typography variant="h6" fontWeight="700" gutterBottom>
                🏆 Top 5 Médicos del Día
              </Typography>
              <Divider sx={{ mb: 3 }} />
              {metricas.medicos.top_5_hoy.length > 0 ? (
                <Grid container spacing={2}>
                  {metricas.medicos.top_5_hoy.map((medico, index) => (
                    <Grid item xs={12} sm={6} md={4} lg={2.4} key={medico.id}>
                      <Card 
                        elevation={0}
                        sx={{ 
                          p: 2,
                          border: '2px solid',
                          borderColor: index === 0 ? 'warning.main' : 'divider',
                          bgcolor: index === 0 ? 'warning.lighter' : 'background.paper',
                          position: 'relative',
                          transition: 'transform 0.2s',
                          '&:hover': {
                            transform: 'scale(1.05)',
                          }
                        }}
                      >
                        {index === 0 && (
                          <Box
                            sx={{
                              position: 'absolute',
                              top: -10,
                              right: -10,
                              bgcolor: 'warning.main',
                              color: 'white',
                              borderRadius: '50%',
                              width: 32,
                              height: 32,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontWeight: 'bold',
                            }}
                          >
                            👑
                          </Box>
                        )}
                        <Box sx={{ textAlign: 'center' }}>
                          <Avatar 
                            sx={{ 
                              width: 60, 
                              height: 60, 
                              mx: 'auto', 
                              mb: 1,
                              bgcolor: 'primary.main',
                              fontSize: '1.5rem',
                            }}
                          >
                            {medico.nombre.charAt(0)}
                          </Avatar>
                          <Typography variant="h5" fontWeight="700" color="primary">
                            #{index + 1}
                          </Typography>
                          <Typography variant="body2" fontWeight={600} noWrap>
                            {medico.nombre}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block" noWrap>
                            {medico.especialidad}
                          </Typography>
                          <Chip 
                            label={`${medico.atenciones} atenciones`}
                            size="small"
                            color={index === 0 ? "warning" : "default"}
                            sx={{ mt: 1 }}
                          />
                        </Box>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Alert severity="info">
                  No hay datos de atenciones hoy
                </Alert>
              )}
            </Paper>

            {/* Estado en Tiempo Real - Mejorado */}
            {tiempoReal && (
              <Paper 
                elevation={0}
                sx={{ 
                  p: 4, 
                  mb: 4,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                  <SpeedIcon sx={{ fontSize: 32 }} />
                  <Typography variant="h5" fontWeight="700">
                    📡 Estado en Tiempo Real
                  </Typography>
                </Box>
                
                <Grid container spacing={3}>
                  <Grid item xs={6} md={3}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      bgcolor: 'rgba(255,255,255,0.15)',
                      borderRadius: 2,
                    }}>
                      <BoxIcon sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h3" fontWeight="700">
                        {tiempoReal.boxes_disponibles}
                      </Typography>
                      <Typography variant="body2">
                        Boxes Disponibles
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      bgcolor: 'rgba(255,255,255,0.15)',
                      borderRadius: 2,
                    }}>
                      <AtencionIcon sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h3" fontWeight="700">
                        {tiempoReal.atenciones_en_curso}
                      </Typography>
                      <Typography variant="body2">
                        Atenciones en Curso
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      bgcolor: 'rgba(255,255,255,0.15)',
                      borderRadius: 2,
                    }}>
                      <PersonIcon sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h3" fontWeight="700">
                        {tiempoReal.pacientes_en_espera}
                      </Typography>
                      <Typography variant="body2">
                        Pacientes en Espera
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Box sx={{ 
                      textAlign: 'center', 
                      p: 2, 
                      bgcolor: 'rgba(255,255,255,0.15)',
                      borderRadius: 2,
                    }}>
                      <RutaIcon sx={{ fontSize: 40, mb: 1 }} />
                      <Typography variant="h3" fontWeight="700">
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
                  <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid rgba(255,255,255,0.3)' }}>
                    <Typography variant="h6" fontWeight="600" gutterBottom>
                      Última Actividad Registrada
                    </Typography>
                    <Grid container spacing={2}>
                      {tiempoReal.ultima_atencion && (
                        <Grid item xs={12} md={6}>
                          <Box sx={{ 
                            bgcolor: 'rgba(255,255,255,0.2)', 
                            p: 3, 
                            borderRadius: 2,
                            border: '1px solid rgba(255,255,255,0.3)',
                          }}>
                            <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                              🏥 ÚLTIMA ATENCIÓN INICIADA
                            </Typography>
                            <Typography variant="h6" fontWeight="700">
                              Paciente: {tiempoReal.ultima_atencion.paciente}
                            </Typography>
                            <Typography variant="body2">
                              Box: {tiempoReal.ultima_atencion.box}
                            </Typography>
                            <Typography variant="caption">
                              {new Date(tiempoReal.ultima_atencion.hora_inicio).toLocaleString('es-CL')}
                            </Typography>
                          </Box>
                        </Grid>
                      )}
                      {tiempoReal.ultimo_paciente && (
                        <Grid item xs={12} md={6}>
                          <Box sx={{ 
                            bgcolor: 'rgba(255,255,255,0.2)', 
                            p: 3, 
                            borderRadius: 2,
                            border: '1px solid rgba(255,255,255,0.3)',
                          }}>
                            <Typography variant="caption" display="block" sx={{ mb: 1 }}>
                              👤 ÚLTIMO PACIENTE INGRESADO
                            </Typography>
                            <Typography variant="h6" fontWeight="700">
                              {tiempoReal.ultimo_paciente.nombre}
                            </Typography>
                            <Typography variant="body2">
                              Estado: {tiempoReal.ultimo_paciente.estado}
                            </Typography>
                            <Typography variant="caption">
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

            {/* Alertas - Mejorado */}
            {metricas.alertas.length > 0 && (
              <Paper 
                elevation={0}
                sx={{ 
                  p: 3, 
                  mb: 4,
                  border: '2px solid',
                  borderColor: 'error.main',
                  bgcolor: 'error.lighter',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <WarningIcon sx={{ color: 'error.main', fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="700" color="error">
                    ⚠️ Alertas Activas ({metricas.alertas.length})
                  </Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  {metricas.alertas.map((alerta, index) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Alert 
                        severity={alerta.tipo}
                        icon={<WarningIcon />}
                        sx={{ 
                          borderLeft: '4px solid',
                          borderLeftColor: `${alerta.tipo}.main`,
                        }}
                      >
                        <Typography variant="subtitle2" fontWeight={600}>
                          {alerta.titulo}
                        </Typography>
                        <Typography variant="body2">
                          {alerta.mensaje}
                        </Typography>
                      </Alert>
                    </Grid>
                  ))}
                </Grid>
              </Paper>
            )}

            {/* Atenciones Retrasadas */}
            {metricas.atenciones.retrasadas.length > 0 && (
              <Paper 
                elevation={0}
                sx={{ 
                  p: 3,
                  border: '1px solid',
                  borderColor: 'warning.main',
                  bgcolor: 'warning.lighter',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <AccessTimeIcon sx={{ color: 'warning.main', fontSize: 28 }} />
                  <Typography variant="h6" fontWeight="700" color="warning.dark">
                    ⏰ Atenciones Retrasadas ({metricas.atenciones.retrasadas.length})
                  </Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Paciente</strong></TableCell>
                        <TableCell><strong>Box</strong></TableCell>
                        <TableCell align="right"><strong>Retraso</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {metricas.atenciones.retrasadas.map((atraso) => (
                        <TableRow key={atraso.id}>
                          <TableCell>{atraso.paciente}</TableCell>
                          <TableCell>{atraso.box}</TableCell>
                          <TableCell align="right">
                            <Chip 
                              label={`${atraso.retraso_minutos} min`}
                              size="small"
                              color="warning"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default Dashboard;