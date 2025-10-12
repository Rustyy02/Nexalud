import axios from 'axios';

// Configuración base de axios
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Para enviar cookies de sesión
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
  
  // Recalcular progreso
  recalcularProgreso: (id) => 
    api.post(`/rutas-clinicas/${id}/recalcular_progreso/`),
  
  // Pausar ruta
  pausar: (id, motivo) => 
    api.post(`/rutas-clinicas/${id}/pausar/`, { motivo }),
  
  // Reanudar ruta
  reanudar: (id) => api.post(`/rutas-clinicas/${id}/reanudar/`),
  
  // Obtener retrasos
  getRetrasos: (id) => api.get(`/rutas-clinicas/${id}/retrasos/`),
};

// ============================================
// SERVICIOS DE ETAPAS (NODOS DEL TIMELINE)
// ============================================

export const etapasService = {
  // Obtener todas las etapas
  getAll: (params = {}) => api.get('/etapas/', { params }),
  
  // Obtener etapa por ID
  getById: (id) => api.get(`/etapas/${id}/`),
  
  // IMPORTANTE: Iniciar etapa (cambiar estado en timeline)
  iniciar: (id) => api.post(`/etapas/${id}/iniciar/`),
  
  // IMPORTANTE: Finalizar etapa
  finalizar: (id) => api.post(`/etapas/${id}/finalizar/`),
  
  // IMPORTANTE: Pausar etapa (nodo estático)
  pausar: (id, motivo) => 
    api.post(`/etapas/${id}/pausar/`, { motivo }),
  
  // Reanudar etapa pausada
  reanudar: (id) => api.post(`/etapas/${id}/reanudar/`),
  
  // Obtener progreso de la etapa
  getProgreso: (id) => api.get(`/etapas/${id}/progreso/`),
};

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
  ocupar: (id) => api.post(`/boxes/${id}/ocupar/`),
  
  // Liberar box
  liberar: (id) => api.post(`/boxes/${id}/liberar/`),
  
  // Obtener boxes disponibles
  getDisponibles: () => api.get('/boxes/disponibles/'),
  
  // Obtener estadísticas de boxes
  getEstadisticas: () => api.get('/boxes/estadisticas/'),
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
  
  // Obtener atenciones en curso
  getEnCurso: () => api.get('/atenciones/en_curso/'),
  
  // Obtener atenciones de hoy
  getHoy: () => api.get('/atenciones/hoy/'),
};

// ============================================
// SERVICIOS DE MÉDICOS
// ============================================

export const medicosService = {
  // Obtener todos los médicos
  getAll: (params = {}) => api.get('/medicos/', { params }),
  
  // Obtener médico por ID
  getById: (id) => api.get(`/medicos/${id}/`),
  
  // Obtener atenciones del médico hoy
  getAtencionesHoy: (id) => api.get(`/medicos/${id}/atenciones_hoy/`),
};

// ============================================
// SERVICIO DE AUTENTICACIÓN
// ============================================

export const authService = {
  // Login (usando autenticación de Django)
  login: async (username, password) => {
    const response = await api.post('/api-auth/login/', {
      username,
      password,
    });
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
    }
    return response;
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