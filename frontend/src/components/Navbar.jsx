// frontend/src/components/Navbar.jsx
import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Divider,
  useMediaQuery,
  useTheme,
  Chip,
} from '@mui/material';
import {
  Psychology as Brain,
  MedicalServices as MedicalIcon,
  Person as PersonIcon,
  Dashboard as DashboardIcon,
  MeetingRoom as MeetingRoomIcon,
  ExitToApp as ExitIcon,
  Menu as MenuIcon,
  Home as HomeIcon,
  LocalHospital as HospitalIcon, // ✅ NUEVO
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [anchorEl, setAnchorEl] = useState(null);
  const [mobileMenuAnchor, setMobileMenuAnchor] = useState(null);

  const handleUserMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleMobileMenuOpen = (event) => {
    setMobileMenuAnchor(event.currentTarget);
  };

  const handleMobileMenuClose = () => {
    setMobileMenuAnchor(null);
  };

  const handleLogout = () => {
    handleUserMenuClose();
    logout();
    navigate('/login');
  };

  const handleNavigate = (path) => {
    navigate(path);
    handleMobileMenuClose();
  };

  const isActive = (path) => {
    if (path === '/' || path === '/pacientes') {
      return location.pathname === '/' || location.pathname === '/pacientes';
    }
    return location.pathname.startsWith(path);
  };

  // ✅ Definir elementos de navegación según el rol
  const getNavigationItems = () => {
    const rol = user?.rol;
    
    if (rol === 'ADMINISTRADOR') {
      return [
        { label: 'Inicio', path: '/pacientes', icon: <HomeIcon /> },
        { label: 'Gestión de Boxes', path: '/boxes', icon: <MeetingRoomIcon /> },
        { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
        { label: 'NexaThink', path: '/nexathink', icon: <Brain /> },
      ];
    }
    
    if (rol === 'SECRETARIA') {
      return [
        { label: 'Inicio', path: '/pacientes', icon: <HomeIcon /> },
        { label: 'Gestión de Boxes', path: '/boxes', icon: <MeetingRoomIcon /> },
      ];
    }
    
    // ✅ NUEVO: Navegación para médicos
    if (rol === 'MEDICO') {
      return [
        { label: 'Mis Consultas', path: '/medico/consultas', icon: <HospitalIcon /> },
        { label: 'Estado de Boxes', path: '/boxes', icon: <MeetingRoomIcon /> },
      ];
    }
    
    return [];
  };

  const navigationItems = getNavigationItems();

  const getRolColor = (rol) => {
    switch(rol) {
      case 'ADMINISTRADOR':
        return 'error';
      case 'SECRETARIA':
        return 'primary';
      case 'MEDICO':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <AppBar 
      position="sticky" 
      elevation={2} 
      sx={{ 
        bgcolor: 'white', 
        color: 'text.primary',
        top: 0,
        zIndex: theme.zIndex.appBar,
      }}
    >
      <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
        {/* Logo y Título */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            cursor: 'pointer',
            mr: { xs: 2, md: 4 },
            userSelect: 'none',
          }}
          onClick={() => navigate(navigationItems[0]?.path || '/')}
        >
          <MedicalIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
            <Typography variant="h6" fontWeight="bold" sx={{ color: 'primary.main', lineHeight: 1.2 }}>
              Nexalud
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', lineHeight: 1 }}>
              Sistema de Gestión
            </Typography>
          </Box>
        </Box>

        {/* Navegación Desktop */}
        {!isMobile && (
          <Box sx={{ display: 'flex', gap: 1, flex: 1 }}>
            {navigationItems.map((item) => (
              <Button
                key={item.path}
                startIcon={item.icon}
                onClick={() => handleNavigate(item.path)}
                sx={{
                  color: isActive(item.path) ? 'primary.main' : 'text.primary',
                  bgcolor: isActive(item.path) ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                  fontWeight: isActive(item.path) ? 600 : 400,
                  px: 3,
                  py: 1,
                  textTransform: 'none',
                  borderRadius: 2,
                  '&:hover': {
                    bgcolor: isActive(item.path) ? 'rgba(25, 118, 210, 0.12)' : 'action.hover',
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        )}

        {/* Spacer para mobile */}
        {isMobile && <Box sx={{ flex: 1 }} />}

        {/* Menú de Usuario Desktop */}
        {!isMobile && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="body2" fontWeight="600">
                {user?.first_name && user?.last_name 
                  ? `${user.first_name} ${user.last_name}`
                  : user?.username || 'Usuario'}
              </Typography>
              <Chip 
                label={user?.rol_display || 'Sin rol'} 
                size="small"
                color={getRolColor(user?.rol)}
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            </Box>
            <IconButton onClick={handleUserMenuOpen} sx={{ p: 0.5 }}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>
                <PersonIcon />
              </Avatar>
            </IconButton>
          </Box>
        )}

        {/* Menú Hamburguesa Mobile */}
        {isMobile && (
          <IconButton onClick={handleMobileMenuOpen} edge="end">
            <MenuIcon />
          </IconButton>
        )}

        {/* Menú Desplegable de Usuario */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleUserMenuClose}
          PaperProps={{
            sx: {
              mt: 1.5,
              minWidth: 200,
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2" fontWeight="600">
              {user?.first_name && user?.last_name 
                ? `${user.first_name} ${user.last_name}`
                : user?.username || 'Usuario'}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              {user?.email || 'Sin correo'}
            </Typography>
            <Chip 
              label={user?.rol_display || 'Sin rol'} 
              size="small"
              color={getRolColor(user?.rol)}
              sx={{ mt: 1, height: 22, fontSize: '0.75rem' }}
            />
          </Box>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <ExitIcon sx={{ mr: 2, fontSize: 20 }} />
            Cerrar Sesión
          </MenuItem>
        </Menu>

        {/* Menú Mobile */}
        <Menu
          anchorEl={mobileMenuAnchor}
          open={Boolean(mobileMenuAnchor)}
          onClose={handleMobileMenuClose}
          PaperProps={{
            sx: {
              mt: 1.5,
              minWidth: 250,
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1, bgcolor: 'grey.50' }}>
            <Typography variant="subtitle2" fontWeight="600">
              {user?.first_name && user?.last_name 
                ? `${user.first_name} ${user.last_name}`
                : user?.username || 'Usuario'}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              {user?.email || 'Sin correo'}
            </Typography>
            <Chip 
              label={user?.rol_display || 'Sin rol'} 
              size="small"
              color={getRolColor(user?.rol)}
              sx={{ mt: 1, height: 22, fontSize: '0.75rem' }}
            />
          </Box>
          <Divider />
          {navigationItems.map((item) => (
            <MenuItem
              key={item.path}
              onClick={() => handleNavigate(item.path)}
              selected={isActive(item.path)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {item.icon}
                <Typography>{item.label}</Typography>
              </Box>
            </MenuItem>
          ))}
          <Divider />
          <MenuItem onClick={handleLogout}>
            <ExitIcon sx={{ mr: 2, fontSize: 20 }} />
            Cerrar Sesión
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;