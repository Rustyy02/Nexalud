// frontend/src/services/api.js - VERSIÓN MEJORADA
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptors
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============================================
// SERVICIOS DE RUTAS CLÍNICAS - MEJORADOS
// ============================================

export const rutasClinicasService = {
  // Básicos
  getAll: (params = {}) => api.get('/rutas-clinicas/', { params }),
  getById: (id) => api.get(`/rutas-clinicas/${id}/`),
  create: (data) => api.post('/rutas-clinicas/', data),
  
  // ============================================
  // NUEVO: Timeline completo con retrasos
  // ============================================
  getTimeline: (id) => api.get(`/rutas-clinicas/${id}/timeline/`),
  
  // ============================================
  // MEJORADO: Avanzar con observaciones
  // ============================================
  avanzar: (id, data = {}) => 
    api.post(`/rutas-clinicas/${id}/avanzar/`, data),
  // Ejemplo de uso:
  // avanzar(rutaId, { observaciones: "Paciente derivado a laboratorio" })
  
  // ============================================
  // MEJORADO: Retroceder con motivo
  // ============================================
  retroceder: (id, data = {}) => 
    api.post(`/rutas-clinicas/${id}/retroceder/`, data),
  // Ejemplo de uso:
  // retroceder(rutaId, { motivo: "Error en el registro" })
  
  // Control de ruta
  iniciar: (id) => api.post(`/rutas-clinicas/${id}/iniciar/`),
  pausar: (id, motivo) => api.post(`/rutas-clinicas/${id}/pausar/`, { motivo }),
  reanudar: (id) => api.post(`/rutas-clinicas/${id}/reanudar/`),
  completar: (id) => api.post(`/rutas-clinicas/${id}/completar/`),
  
  // ============================================
  // NUEVO: Observaciones
  // ============================================
  agregarObservacion: (id, observaciones) => 
    api.post(`/rutas-clinicas/${id}/agregar_observacion/`, { observaciones }),
  
  // ============================================
  // NUEVO: Historial completo
  // ============================================
  getHistorial: (id) => api.get(`/rutas-clinicas/${id}/historial/`),
  
  // ============================================
  // NUEVO: Detección de retrasos
  // ============================================
  getRetrasos: (id) => api.get(`/rutas-clinicas/${id}/retrasos/`),
  
  // ============================================
  // NUEVO: Listar rutas con retrasos
  // ============================================
  getConRetrasos: () => api.get('/rutas-clinicas/con_retrasos/'),
  
  // Listas
  getActivas: () => api.get('/rutas-clinicas/activas/'),
  getPausadas: () => api.get('/rutas-clinicas/pausadas/'),
  
  // Información
  getEtapasDisponibles: () => api.get('/rutas-clinicas/etapas-disponibles/'),
  getEstadisticas: () => api.get('/rutas-clinicas/estadisticas/'),
  recalcularProgreso: (id) => api.post(`/rutas-clinicas/${id}/recalcular_progreso/`),
  getInfoEtapaActual: (id) => api.get(`/rutas-clinicas/${id}/info_etapa_actual/`),
};

// ============================================
// SERVICIOS DE PACIENTES
// ============================================

export const pacientesService = {
  getAll: (params = {}) => api.get('/pacientes/', { params }),
  getById: (id) => api.get(`/pacientes/${id}/`),
  create: (data) => api.post('/pacientes/', data),
  update: (id, data) => api.patch(`/pacientes/${id}/`, data),
  cambiarEstado: (id, estado) => 
    api.post(`/pacientes/${id}/cambiar_estado/`, { estado_actual: estado }),
  getActivos: () => api.get('/pacientes/activos/'),
  getEnEspera: () => api.get('/pacientes/en_espera/'),
  getEstadisticas: () => api.get('/pacientes/estadisticas/'),
  getRutasClinicas: (id) => api.get(`/pacientes/${id}/rutas_clinicas/`),
  getAtenciones: (id) => api.get(`/pacientes/${id}/atenciones/`),
};

// ============================================
// SERVICIOS DE BOXES
// ============================================

export const boxesService = {
  getAll: (params = {}) => api.get('/boxes/', { params }),
  getById: (id) => api.get(`/boxes/${id}/`),
  create: (data) => api.post('/boxes/', data),
  update: (id, data) => api.patch(`/boxes/${id}/`, data),
  ocupar: (id, timestamp = null) => 
    api.post(`/boxes/${id}/ocupar/`, timestamp ? { timestamp } : {}),
  liberar: (id, timestamp = null) => 
    api.post(`/boxes/${id}/liberar/`, timestamp ? { timestamp } : {}),
  getDisponibles: (especialidad = null) => {
    const params = especialidad ? { especialidad } : {};
    return api.get('/boxes/disponibles/', { params });
  },
  getOcupados: () => api.get('/boxes/ocupados/'),
  getEstadisticas: () => api.get('/boxes/estadisticas/'),
  getPorEspecialidad: () => api.get('/boxes/por_especialidad/'),
  marcarMantenimiento: (id, motivo) => 
    api.post(`/boxes/${id}/mantenimiento/`, { motivo }),
  activar: (id) => api.post(`/boxes/${id}/activar/`),
  desactivar: (id) => api.post(`/boxes/${id}/desactivar/`),
  getHistorialOcupacion: (id) => api.get(`/boxes/${id}/historial_ocupacion/`),
};

// ============================================
// SERVICIOS DE ATENCIONES
// ============================================

export const atencionesService = {
  getAll: (params = {}) => api.get('/atenciones/', { params }),
  getById: (id) => api.get(`/atenciones/${id}/`),
  create: (data) => api.post('/atenciones/', data),
  iniciarCronometro: (id) => api.post(`/atenciones/${id}/iniciar_cronometro/`),
  finalizarCronometro: (id) => api.post(`/atenciones/${id}/finalizar_cronometro/`),
  cancelar: (id, motivo) => api.post(`/atenciones/${id}/cancelar/`, { motivo }),
  reagendar: (id, nueva_fecha, nuevo_box = null) => 
    api.post(`/atenciones/${id}/reagendar/`, { nueva_fecha, nuevo_box }),
  getEnCurso: () => api.get('/atenciones/en_curso/'),
  getHoy: () => api.get('/atenciones/hoy/'),
  getPendientes: () => api.get('/atenciones/pendientes/'),
  getRetrasadas: () => api.get('/atenciones/retrasadas/'),
  getEstadisticas: (params = {}) => api.get('/atenciones/estadisticas/', { params }),
  getMetricas: (id) => api.get(`/atenciones/${id}/metricas/`),
};

// ============================================
// SERVICIOS DE MÉDICOS
// ============================================

export const medicosService = {
  getAll: (params = {}) => api.get('/medicos/', { params }),
  getById: (id) => api.get(`/medicos/${id}/`),
  create: (data) => api.post('/medicos/', data),
  update: (id, data) => api.patch(`/medicos/${id}/`, data),
  getAtencionesHoy: (id) => api.get(`/medicos/${id}/atenciones_hoy/`),
  getAgendaSemanal: (id) => api.get(`/medicos/${id}/agenda_semanal/`),
  getMetricas: (id) => api.get(`/medicos/${id}/metricas/`),
  getActivos: () => api.get('/medicos/activos/'),
  getPorEspecialidad: () => api.get('/medicos/por_especialidad/'),
  getEstadisticas: () => api.get('/medicos/estadisticas/'),
  activar: (id) => api.post(`/medicos/${id}/activar/`),
  desactivar: (id) => api.post(`/medicos/${id}/desactivar/`),
};

// ============================================
// SERVICIO DE AUTENTICACIÓN
// ============================================

export const authService = {
  login: async (username, password) => {
    try {
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
  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  },
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
};

export default api;