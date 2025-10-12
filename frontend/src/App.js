import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider, useAuth } from './context/AuthContext';

// Componentes
import Login from './components/Login';
// import ListaPacientes from './components/ListaPacientes';
// import DetallePaciente from './components/DetallePaciente';
// import EstadoBoxes from './components/EstadoBoxes';

// Tema personalizado de Material UI
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Azul
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#4caf50', // Verde
      light: '#81c784',
      dark: '#388e3c',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
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

// Componente para proteger rutas
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Cargando...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

// Componente temporal para rutas que aún no existen
const ComingSoon = ({ title }) => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100vh',
    flexDirection: 'column',
  }}>
    <h1>{title}</h1>
    <p>Este componente está en desarrollo</p>
  </div>
);

function AppContent() {
  return (
    <Router>
      <Routes>
        {/* Ruta pública */}
        <Route path="/login" element={<Login />} />

        {/* Rutas protegidas */}
        <Route
          path="/pacientes"
          element={
            <ProtectedRoute>
              <ComingSoon title="Lista de Pacientes" />
              {/* <ListaPacientes /> */}
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/pacientes/:id"
          element={
            <ProtectedRoute>
              <ComingSoon title="Detalle del Paciente" />
              {/* <DetallePaciente /> */}
            </ProtectedRoute>
          }
        />

        <Route
          path="/boxes"
          element={
            <ProtectedRoute>
              <ComingSoon title="Estado de Box's" />
              {/* <EstadoBoxes /> */}
            </ProtectedRoute>
          }
        />

        {/* Redirección por defecto */}
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
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