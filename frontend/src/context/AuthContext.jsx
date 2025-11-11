import React, { createContext, useState, useContext, useEffect } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Verificar si hay token y usuario al cargar
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        console.log('Usuario cargado desde localStorage:', userData);
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Error al parsear usuario:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await authService.login(username, password);
      
      console.log('Respuesta completa del login:', response);
      
      if (response.success) {
        console.log('Usuario recibido del backend:', response.data.user);
        console.log('Rol del usuario:', response.data.user?.rol);
        
        setUser(response.data.user);
        setIsAuthenticated(true);
        // Guardar usuario en localStorage
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return { success: true, user: response.data.user };
      }
      
      return { 
        success: false, 
        error: response.error || 'Error al iniciar sesión' 
      };
    } catch (error) {
      console.error('Error en login:', error);
      return { 
        success: false, 
        error: 'Error al iniciar sesión' 
      };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem('user');
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de AuthProvider');
  }
  return context;
};