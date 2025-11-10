import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Componentes
import Login from './components/Login';
import Home from './components/Home';
import EstadoBoxes from './components/EstadoBoxes';
import DetallePaciente from './components/DetallePaciente';
import Dashboard from './components/Dashboard';
import NexaThink from './components/NexaThink';
import Medicoconsultas from './components/Medicoconsultas'; 

// Tema personalizado de Material UI
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
      light: '#c8e6c9',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

const RoleBasedRedirect = () => {
  const { user } = useAuth();

  // Redirigir según el rol del usuario
  if (user?.rol === 'MEDICO') {
    return <Navigate to="/boxes" replace />;
  }

  // Administradores y Secretarias van a Home
  return <Navigate to="/pacientes" replace />;
};

function AppContent() {
  return (
    <Router>
      <Routes>
        {/* Ruta pública */}
        <Route path="/login" element={<Login />} />

        {/* Ruta raíz - Redirige según rol */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <RoleBasedRedirect />
            </ProtectedRoute>
          }
        />

        {/* Rutas protegidas - INICIO (Administrador y Secretaria) */}
        <Route
          path="/pacientes"
          element={
            <ProtectedRoute allowedRoles={['ADMINISTRADOR', 'SECRETARIA']}>
              <Home />
            </ProtectedRoute>
          }
        />
        
        {/* Detalle Paciente - Administrador y Secretaria */}
        <Route
          path="/pacientes/:id"
          element={
            <ProtectedRoute allowedRoles={['ADMINISTRADOR', 'SECRETARIA']}>
              <DetallePaciente />
            </ProtectedRoute>
          }
        />

        {/* Estado Boxes - Todos los roles */}
        <Route
          path="/boxes"
          element={
            <ProtectedRoute allowedRoles={['ADMINISTRADOR', 'SECRETARIA', 'MEDICO']}>
              <EstadoBoxes />
            </ProtectedRoute>
          }
        />

        {/* Dashboard - Solo Administrador */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute allowedRoles={['ADMINISTRADOR']}>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        {/* NexaThink - Solo Administrador */}
        <Route
          path="/nexathink"
          element={
            <ProtectedRoute allowedRoles={['ADMINISTRADOR']}>
              <NexaThink />
            </ProtectedRoute>
          }
        />

        {/* ========== RUTAS PARA MÉDICOS ========== */}
        
        {/* Panel principal del médico con cronómetro */}
        <Route
          path="/medico/consultas"
          element={
            <ProtectedRoute allowedRoles={['ADMINISTRADOR','MEDICO']}>
              <Medicoconsultas />
            </ProtectedRoute>
          }
        />

        {/* Redirección por defecto */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}


export default App;