import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Container,
  Paper,
  IconButton,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Psychology as Brain,
  TrendingUp,
  Warning as AlertCircle,
  CheckCircle,
  Analytics as Activity,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { nexathinkService } from '../services/api';
import Navbar from './Navbar';

const iconMap = {
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Activity,
  Brain,
};

const NexaThink = () => {
  const [insights, setInsights] = useState([]);
  const [currentInsight, setCurrentInsight] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isAnimating, setIsAnimating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarInsights();
    
    // Refrescar cada 60 segundos
    const interval = setInterval(cargarInsights, 60000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (insights.length === 0) return;
    
    // Timer insights, 5 segundos.
    const interval = setInterval(() => {
      setIsAnimating(true);
      setTimeout(() => {
        setCurrentInsight((prev) => (prev + 1) % insights.length);
        setIsAnimating(false);
      }, 300);
    }, 5000);

    return () => clearInterval(interval);
  }, [insights]);

  const cargarInsights = async () => {
    try {
      setError('');
      const response = await nexathinkService.getInsights();
      setInsights(response.data.insights);
      setLoading(false);
    } catch (err) {
      setError('Error al cargar insights');
      setLoading(false);
      console.error(err);
    }
  };

  const getTypeColor = (type) => {
    const colors = {
      'alert': { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800' },
      'warning': { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800' },
      'success': { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800' },
      'info': { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800' },
    };
    return colors[type] || colors.info;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'crítica': 'error',
      'alta': 'warning',
      'media': 'info',
      'baja': 'success',
    };
    return colors[priority] || 'default';
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

  const insight = insights[currentInsight];
  const IconComponent = insight && iconMap[insight.icon] ? iconMap[insight.icon] : Brain;

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Header del Bot */}
        <Paper elevation={3} sx={{ p: 4, mb: 3, borderRadius: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 2 }}>
            <Box sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              p: 2,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Brain sx={{ fontSize: 48, color: 'white' }} />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h3" fontWeight="700" sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                NexaThink
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Asistente Inteligente de Análisis Clínico
              </Typography>
            </Box>
            <Tooltip title="Actualizar insights">
              <IconButton onClick={cargarInsights} color="primary" size="large">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ 
              width: 12, 
              height: 12, 
              bgcolor: 'success.main', 
              borderRadius: '50%',
              animation: 'pulse 2s ease-in-out infinite',
              '@keyframes pulse': {
                '0%, 100%': { opacity: 1 },
                '50%': { opacity: 0.5 },
              }
            }} />
            <Typography variant="body2" color="text.secondary">
              Analizando datos en tiempo real • {insights.length} insights detectados
            </Typography>
          </Box>
        </Paper>

        {/* Insight Principal */}
        {insight && (
          <Paper
            elevation={3}
            sx={{
              p: 4,
              mb: 3,
              borderRadius: 3,
              transition: 'all 0.3s',
              opacity: isAnimating ? 0 : 1,
              transform: isAnimating ? 'scale(0.98)' : 'scale(1)',
            }}
          >
            <Box sx={{ display: 'flex', gap: 3 }}>
              <Box sx={{
                p: 2,
                borderRadius: 2,
                bgcolor: getTypeColor(insight.type).bg.replace('bg-', ''),
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <IconComponent sx={{ fontSize: 40, color: getPriorityColor(insight.priority) + '.main' }} />
              </Box>
              
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Chip
                    label={insight.priority?.toUpperCase()}
                    color={getPriorityColor(insight.priority)}
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Insight {currentInsight + 1} de {insights.length}
                  </Typography>
                </Box>
                
                <Typography variant="h6" fontWeight="600" gutterBottom>
                  {insight.message}
                </Typography>
                
                <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>💡 Recomendación:</strong> {insight.recommendation}
                  </Typography>
                </Paper>
              </Box>
            </Box>
          </Paper>
        )}

        {/* Panel de Todos los Insights */}
        <Paper elevation={3} sx={{ p: 4, borderRadius: 3 }}>
          <Typography variant="h5" fontWeight="600" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUp />
            Todos los Insights Detectados
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {insights.map((ins, idx) => {
              const InsIcon = iconMap[ins.icon] || Brain;
              return (
                <Card
                  key={idx}
                  onClick={() => setCurrentInsight(idx)}
                  sx={{
                    cursor: 'pointer',
                    border: '2px solid',
                    borderColor: idx === currentInsight ? 'primary.main' : 'transparent',
                    bgcolor: idx === currentInsight ? 'primary.50' : 'white',
                    transition: 'all 0.3s',
                    '&:hover': {
                      borderColor: 'primary.light',
                      transform: 'translateY(-2px)',
                      boxShadow: 3,
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <InsIcon sx={{ color: getPriorityColor(ins.priority) + '.main' }} />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="body1" fontWeight="500">
                          {ins.message}
                        </Typography>
                      </Box>
                      <Box sx={{
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        bgcolor: getPriorityColor(ins.priority) + '.main',
                      }} />
                    </Box>
                  </CardContent>
                </Card>
              );
            })}
          </Box>
        </Paper>

        {/* Estadísticas Rápidas */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 3, mt: 3 }}>
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <Activity sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h4" fontWeight="700">{insights.length}</Typography>
            <Typography variant="body2" color="text.secondary">Insights Activos</Typography>
          </Paper>
          
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <AlertCircle sx={{ fontSize: 48, color: 'error.main', mb: 1 }} />
            <Typography variant="h4" fontWeight="700">
              {insights.filter(i => i.priority === 'crítica' || i.priority === 'alta').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">Prioridad Alta</Typography>
          </Paper>
          
          <Paper elevation={2} sx={{ p: 3, textAlign: 'center', borderRadius: 2 }}>
            <CheckCircle sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
            <Typography variant="h4" fontWeight="700">
              {insights.filter(i => i.type === 'success').length}
            </Typography>
            <Typography variant="body2" color="text.secondary">Áreas Óptimas</Typography>
          </Paper>
        </Box>
      </Container>
    </>
  );
};

export default NexaThink;