import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Box, Alert, Container, Typography } from '@mui/material';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();

  // Debug: Mostrar información del usuario
  console.log('=== ProtectedRoute Debug ===');
  console.log('Usuario actual:', user);
  console.log('Rol del usuario:', user?.rol);
  console.log('Es superusuario:', user?.is_superuser);
  console.log('Roles permitidos:', allowedRoles);
  console.log('===========================');

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        Cargando...
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si no se especifican roles, permitir acceso a todos los autenticados
  if (allowedRoles.length === 0) {
    return children;
  }

  // Superusuarios pueden acceder a todo
  if (user?.is_superuser) {
    console.log('✅ Acceso permitido: Usuario es superusuario');
    return children;
  }

  // Verificar si el usuario tiene un rol permitido
  const hasAccess = allowedRoles.includes(user?.rol);

  console.log(`¿Tiene acceso? ${hasAccess}`);

  if (!hasAccess) {
    return (
      <Container maxWidth="md" sx={{ mt: 8 }}>
        <Alert severity="error">
          <Typography variant="h6" gutterBottom>
            No tienes permisos para acceder a esta sección
          </Typography>
          <Typography variant="body2">
            Tu rol actual: <strong>{user?.rol_display || 'Sin rol'}</strong>
          </Typography>
          <Typography variant="body2">
            Roles permitidos: <strong>{allowedRoles.join(', ')}</strong>
          </Typography>
        </Alert>
      </Container>
    );
  }

  console.log('✅ Acceso permitido');
  return children;
};

export default ProtectedRoute;