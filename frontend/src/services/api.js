// frontend/src/services/api.js
import axios from 'axios';

// Configuración base de axios
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token si existe
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de respuesta
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token inválido o expirado
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// SERVICIOS DE BOXES
// ============================================

export const boxesService = {
  // Obtener todos los boxes
  getAll: (params = {}) => api.get('/boxes/', { params }),
  
  // Obtener box por ID
  getById: (id) => api.get(`/boxes/${id}/`),
  
  // Crear box
  create: (data) => api.post('/boxes/', data),
  
  // Actualizar box
  update: (id, data) => api.patch(`/boxes/${id}/`, data),
  
  // Ocupar box
  ocupar: (id, timestamp = null) => 
    api.post(`/boxes/${id}/ocupar/`, timestamp ? { timestamp } : {}),
  
  // Liberar box
  liberar: (id, timestamp = null) => 
    api.post(`/boxes/${id}/liberar/`, timestamp ? { timestamp } : {}),
  
  // Obtener boxes disponibles
  getDisponibles: (especialidad = null) => {
    const params = especialidad ? { especialidad } : {};
    return api.get('/boxes/disponibles/', { params });
  },
  
  // Obtener boxes ocupados
  getOcupados: () => api.get('/boxes/ocupados/'),
  
  // Obtener estadísticas de boxes
  getEstadisticas: () => api.get('/boxes/estadisticas/'),
  
  // Agrupar por especialidad
  getPorEspecialidad: () => api.get('/boxes/por_especialidad/'),
  
  // Marcar en mantenimiento
  marcarMantenimiento: (id, motivo) => 
    api.post(`/boxes/${id}/mantenimiento/`, { motivo }),
  
  // Activar/Desactivar
  activar: (id) => api.post(`/boxes/${id}/activar/`),
  desactivar: (id) => api.post(`/boxes/${id}/desactivar/`),
  
  // Historial de ocupación
  getHistorialOcupacion: (id) => 
    api.get(`/boxes/${id}/historial_ocupacion/`),
};

// ============================================
// SERVICIOS DE ATENCIONES
// ============================================

export const atencionesService = {
  // Obtener todas las atenciones
  getAll: (params = {}) => api.get('/atenciones/', { params }),
  
  // Obtener atención por ID
  getById: (id) => api.get(`/atenciones/${id}/`),
  
  // Crear atención
  create: (data) => api.post('/atenciones/', data),
  
  // Iniciar cronómetro
  iniciarCronometro: (id) => 
    api.post(`/atenciones/${id}/iniciar_cronometro/`),
  
  // Finalizar cronómetro
  finalizarCronometro: (id) => 
    api.post(`/atenciones/${id}/finalizar_cronometro/`),
  
  // Cancelar atención
  cancelar: (id, motivo) => 
    api.post(`/atenciones/${id}/cancelar/`, { motivo }),
  
  // Reagendar atención
  reagendar: (id, nueva_fecha, nuevo_box = null) => 
    api.post(`/atenciones/${id}/reagendar/`, { nueva_fecha, nuevo_box }),
  
  // Obtener atenciones en curso
  getEnCurso: () => api.get('/atenciones/en_curso/'),
  
  // Obtener atenciones de hoy
  getHoy: () => api.get('/atenciones/hoy/'),
  
  // Obtener atenciones pendientes
  getPendientes: () => api.get('/atenciones/pendientes/'),
  
  // Obtener atenciones retrasadas (IMPORTANTE para el componente)
  getRetrasadas: () => api.get('/atenciones/retrasadas/'),
  
  // Obtener estadísticas
  getEstadisticas: (params = {}) => 
    api.get('/atenciones/estadisticas/', { params }),
  
  // Obtener métricas de una atención
  getMetricas: (id) => api.get(`/atenciones/${id}/metricas/`),
};

// ============================================
// SERVICIOS DE PACIENTES
// ============================================

export const pacientesService = {
  // Obtener todos los pacientes
  getAll: (params = {}) => api.get('/pacientes/', { params }),
  
  // Obtener un paciente por ID
  getById: (id) => api.get(`/pacientes/${id}/`),
  
  // Crear nuevo paciente
  create: (data) => api.post('/pacientes/', data),
  
  // Actualizar paciente
  update: (id, data) => api.patch(`/pacientes/${id}/`, data),
  
  // Cambiar estado del paciente
  cambiarEstado: (id, estado) => 
    api.post(`/pacientes/${id}/cambiar_estado/`, { estado_actual: estado }),
  
  // Obtener pacientes activos
  getActivos: () => api.get('/pacientes/activos/'),
  
  // Obtener pacientes en espera
  getEnEspera: () => api.get('/pacientes/en_espera/'),
  
  // Obtener estadísticas
  getEstadisticas: () => api.get('/pacientes/estadisticas/'),
  
  // Obtener rutas clínicas del paciente
  getRutasClinicas: (id) => api.get(`/pacientes/${id}/rutas_clinicas/`),
  
  // Obtener atenciones del paciente
  getAtenciones: (id) => api.get(`/pacientes/${id}/atenciones/`),
};

// ============================================
// SERVICIOS DE RUTAS CLÍNICAS (TIMELINE)
// ============================================

export const rutasClinicasService = {
  // Obtener todas las rutas
  getAll: (params = {}) => api.get('/rutas-clinicas/', { params }),
  
  // Obtener una ruta por ID
  getById: (id) => api.get(`/rutas-clinicas/${id}/`),
  
  // Crear nueva ruta clínica
  create: (data) => api.post('/rutas-clinicas/', data),
  
  // IMPORTANTE: Obtener timeline completo del paciente
  getTimeline: (id) => api.get(`/rutas-clinicas/${id}/timeline/`),
  
  // Iniciar ruta
  iniciar: (id) => api.post(`/rutas-clinicas/${id}/iniciar/`),
  
  // Avanzar etapa
  avanzar: (id) => api.post(`/rutas-clinicas/${id}/avanzar/`),
  
  // Retroceder etapa
  retroceder: (id) => api.post(`/rutas-clinicas/${id}/retroceder/`),
  
  // Recalcular progreso
  recalcularProgreso: (id) => 
    api.post(`/rutas-clinicas/${id}/recalcular_progreso/`),
  
  // Pausar ruta
  pausar: (id, motivo) => 
    api.post(`/rutas-clinicas/${id}/pausar/`, { motivo }),
  
  // Reanudar ruta
  reanudar: (id) => api.post(`/rutas-clinicas/${id}/reanudar/`),
  
  // Completar ruta
  completar: (id) => api.post(`/rutas-clinicas/${id}/completar/`),
  
  // Obtener etapas disponibles
  getEtapasDisponibles: () => 
    api.get('/rutas-clinicas/etapas-disponibles/'),
  
  // Obtener rutas activas
  getActivas: () => api.get('/rutas-clinicas/activas/'),
  
  // Obtener rutas pausadas
  getPausadas: () => api.get('/rutas-clinicas/pausadas/'),
  
  // Obtener estadísticas
  getEstadisticas: () => api.get('/rutas-clinicas/estadisticas/'),
};

// ============================================
// SERVICIOS DE MÉDICOS
// ============================================

export const medicosService = {
  // Obtener todos los médicos
  getAll: (params = {}) => api.get('/medicos/', { params }),
  
  // Obtener médico por ID
  getById: (id) => api.get(`/medicos/${id}/`),
  
  // Crear médico
  create: (data) => api.post('/medicos/', data),
  
  // Actualizar médico
  update: (id, data) => api.patch(`/medicos/${id}/`, data),
  
  // Obtener atenciones del médico hoy
  getAtencionesHoy: (id) => api.get(`/medicos/${id}/atenciones_hoy/`),
  
  // Obtener agenda semanal
  getAgendaSemanal: (id) => api.get(`/medicos/${id}/agenda_semanal/`),
  
  // Obtener métricas del médico
  getMetricas: (id) => api.get(`/medicos/${id}/metricas/`),
  
  // Obtener médicos activos
  getActivos: () => api.get('/medicos/activos/'),
  
  // Agrupar por especialidad
  getPorEspecialidad: () => api.get('/medicos/por_especialidad/'),
  
  // Obtener estadísticas
  getEstadisticas: () => api.get('/medicos/estadisticas/'),
  
  // Activar/Desactivar
  activar: (id) => api.post(`/medicos/${id}/activar/`),
  desactivar: (id) => api.post(`/medicos/${id}/desactivar/`),
};

// ============================================
// SERVICIO DE AUTENTICACIÓN
// ============================================
export const authService = {
  // Login
  login: async (username, password) => {
    try {
      // Usar el endpoint correcto de autenticación por token
      const response = await axios.post('http://127.0.0.1:8000/api-token-auth/', {
        username,
        password,
      });
      
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        return { success: true, data: response.data };
      }
    } catch (error) {
      console.error('Error en login:', error);
      return { 
        success: false, 
        error: 'Usuario o contraseña incorrectos' 
      };
    }
  },
  // Logout
  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  },
  
  // Verificar si está autenticado
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
};

export default api;