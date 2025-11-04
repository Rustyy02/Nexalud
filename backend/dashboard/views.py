# backend/dashboard/views.py - VERSIÓN CORREGIDA
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import timedelta
from pacientes.models import Paciente
from boxes.models import Box
from atenciones.models import Atencion
from users.models import User
from rutas_clinicas.models import RutaClinica
from .insights_ml import NexaThinkAnalyzer

# ============================================
# 🆕 PERMISO PERSONALIZADO MEJORADO
# ============================================
from rest_framework import permissions

class IsAdminOrStaff(permissions.BasePermission):
    """
    Permiso que permite acceso a:
    - Superusuarios (is_superuser=True)
    - Staff (is_staff=True)
    - Usuarios con rol ADMINISTRADOR
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Permitir a superusuarios
        if request.user.is_superuser:
            return True
        
        # Permitir a staff
        if request.user.is_staff:
            return True
        
        # Permitir a usuarios con rol ADMINISTRADOR
        if hasattr(request.user, 'rol') and request.user.rol == 'ADMINISTRADOR':
            return True
        
        return False

# ============================================
# VISTAS DEL DASHBOARD
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])  # 🆕 PERMISO MEJORADO
def dashboard_metricas_generales(request):
    """
    Endpoint principal del dashboard con todas las métricas.
    Accesible para: Superusuarios, Staff, y usuarios con rol ADMINISTRADOR.
    """
    ahora = timezone.now()
    hoy = ahora.date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    # ===== MÉTRICAS DE PACIENTES =====
    total_pacientes = Paciente.objects.filter(activo=True).count()
    pacientes_hoy = Paciente.objects.filter(
        fecha_ingreso__date=hoy,
        activo=True
    ).count()
    
    pacientes_por_estado = {}
    for estado_key, estado_label in Paciente.ESTADO_CHOICES:
        count = Paciente.objects.filter(
            estado_actual=estado_key,
            activo=True
        ).count()
        pacientes_por_estado[estado_key] = {
            'label': estado_label,
            'count': count
        }
    
    pacientes_por_urgencia = {}
    for urgencia_key, urgencia_label in Paciente.URGENCIA_CHOICES:
        count = Paciente.objects.filter(
            nivel_urgencia=urgencia_key,
            activo=True
        ).count()
        pacientes_por_urgencia[urgencia_key] = {
            'label': urgencia_label,
            'count': count
        }

    # ===== MÉTRICAS DE BOXES =====
    total_boxes = Box.objects.filter(activo=True).count()
    boxes_disponibles = Box.objects.filter(
        estado='DISPONIBLE',
        activo=True
    ).count()
    boxes_ocupados = Box.objects.filter(
        estado='OCUPADO',
        activo=True
    ).count()
    
    tasa_ocupacion_boxes = round(
        (boxes_ocupados / total_boxes * 100) if total_boxes > 0 else 0,
        2
    )

    # ===== MÉTRICAS DE ATENCIONES =====
    atenciones_hoy = Atencion.objects.filter(
        fecha_hora_inicio__date=hoy
    ).count()
    
    atenciones_completadas_hoy = Atencion.objects.filter(
        fecha_hora_inicio__date=hoy,
        estado='COMPLETADA'
    ).count()
    
    atenciones_en_curso = Atencion.objects.filter(
        estado='EN_CURSO'
    ).count()
    
    atenciones_pendientes = Atencion.objects.filter(
        estado__in=['PROGRAMADA', 'EN_ESPERA']
    ).count()
    
    # Tiempo promedio de atención (últimos 7 días)
    tiempo_promedio_atencion = Atencion.objects.filter(
        fecha_hora_inicio__gte=ahora - timedelta(days=7),
        estado='COMPLETADA',
        duracion_real__isnull=False
    ).aggregate(promedio=Avg('duracion_real'))['promedio'] or 0
    
    # Atenciones por tipo (hoy)
    atenciones_por_tipo = {}
    for tipo_key, tipo_label in Atencion.TIPO_ATENCION_CHOICES:
        count = Atencion.objects.filter(
            fecha_hora_inicio__date=hoy,
            tipo_atencion=tipo_key
        ).count()
        atenciones_por_tipo[tipo_key] = {
            'label': tipo_label,
            'count': count
        }

    # Detectar atenciones retrasadas
    atenciones_retrasadas = []
    atenciones_activas = Atencion.objects.filter(estado='EN_CURSO')
    for atencion in atenciones_activas:
        if atencion.is_retrasada():
            atenciones_retrasadas.append({
                'id': str(atencion.id),
                'paciente': atencion.paciente.identificador_hash[:12],
                'box': atencion.box.numero,
                'retraso_minutos': atencion.calcular_retraso()
            })

    # ===== MÉTRICAS DE RUTAS CLÍNICAS =====
    rutas_activas = RutaClinica.objects.filter(
        estado__in=['INICIADA', 'EN_PROGRESO']
    ).count()
    
    rutas_completadas_hoy = RutaClinica.objects.filter(
        fecha_fin_real__date=hoy,
        estado='COMPLETADA'
    ).count()
    
    rutas_pausadas = RutaClinica.objects.filter(
        esta_pausado=True
    ).count()
    
    progreso_promedio_rutas = RutaClinica.objects.filter(
        estado__in=['INICIADA', 'EN_PROGRESO']
    ).aggregate(promedio=Avg('porcentaje_completado'))['promedio'] or 0

    # ===== MÉTRICAS DE MÉDICOS =====
    medicos_activos = User.objects.filter(
        rol='MEDICO',
        is_active=True
    ).count()
    # Cantidad de médicos que atendieron hoy
    medicos_atendiendo_hoy = User.objects.filter(
        rol='MEDICO',
        is_active=True,
        atenciones_medico__fecha_hora_inicio__date=hoy
    ).distinct().count()

    # Top 5 médicos por atenciones hoy
    top_medicos_hoy = User.objects.filter(
        rol='MEDICO',
        is_active=True,
        atenciones_medico__fecha_hora_inicio__date=hoy
    ).annotate(
        total_atenciones=Count('atenciones_medico')
    ).order_by('-total_atenciones')[:5]
    
    top_medicos_data = []
    for medico in top_medicos_hoy:
        top_medicos_data.append({
            'id': str(medico.id),
            'nombre': medico.nombre_completo,
            'especialidad': medico.get_especialidad_principal_display(),
            'atenciones': medico.total_atenciones
        })

    # ===== TENDENCIAS (ÚLTIMOS 7 DÍAS) =====
    tendencias = []
    for i in range(7):
        dia = hoy - timedelta(days=6-i)
        tendencias.append({
            'fecha': dia.isoformat(),
            'pacientes': Paciente.objects.filter(
                fecha_ingreso__date=dia,
                activo=True
            ).count(),
            'atenciones': Atencion.objects.filter(
                fecha_hora_inicio__date=dia
            ).count(),
            'completadas': Atencion.objects.filter(
                fecha_hora_inicio__date=dia,
                estado='COMPLETADA'
            ).count()
        })

    # ===== ALERTAS Y NOTIFICACIONES =====
    alertas = []
    
    # Alerta: Atenciones retrasadas
    if len(atenciones_retrasadas) > 0:
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Atenciones Retrasadas',
            'mensaje': f'{len(atenciones_retrasadas)} atenciones están retrasadas',
            'prioridad': 'alta'
        })
    
    # Alerta: Baja disponibilidad de boxes
    if tasa_ocupacion_boxes > 80:
        alertas.append({
            'tipo': 'warning',
            'titulo': 'Alta Ocupación de Boxes',
            'mensaje': f'{tasa_ocupacion_boxes}% de boxes ocupados',
            'prioridad': 'media'
        })
    
    # Alerta: Rutas pausadas
    if rutas_pausadas > 5:
        alertas.append({
            'tipo': 'info',
            'titulo': 'Rutas Pausadas',
            'mensaje': f'{rutas_pausadas} rutas clínicas están pausadas',
            'prioridad': 'baja'
        })

    # ===== RESPONSE COMPLETO =====
    return Response({
        'timestamp': ahora.isoformat(),
        'fecha_hoy': hoy.isoformat(),
        
        # Pacientes
        'pacientes': {
            'total': total_pacientes,
            'hoy': pacientes_hoy,
            'por_estado': pacientes_por_estado,
            'por_urgencia': pacientes_por_urgencia,
        },
        
        # Boxes
        'boxes': {
            'total': total_boxes,
            'disponibles': boxes_disponibles,
            'ocupados': boxes_ocupados,
            'tasa_ocupacion': tasa_ocupacion_boxes,
        },
        
        # Atenciones
        'atenciones': {
            'hoy': atenciones_hoy,
            'completadas_hoy': atenciones_completadas_hoy,
            'en_curso': atenciones_en_curso,
            'pendientes': atenciones_pendientes,
            'tiempo_promedio_minutos': round(tiempo_promedio_atencion, 1),
            'por_tipo': atenciones_por_tipo,
            'retrasadas': atenciones_retrasadas,
        },
        
        # Rutas Clínicas
        'rutas_clinicas': {
            'activas': rutas_activas,
            'completadas_hoy': rutas_completadas_hoy,
            'pausadas': rutas_pausadas,
            'progreso_promedio': round(progreso_promedio_rutas, 1),
        },
        
        # Médicos
        'medicos': {
            'total_activos': medicos_activos,
            'atendiendo_hoy': medicos_atendiendo_hoy,
            'top_5_hoy': top_medicos_data,
        },
        
        # Tendencias
        'tendencias_7_dias': tendencias,
        
        # Alertas
        'alertas': alertas,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])  # 🆕 PERMISO MEJORADO
def dashboard_metricas_tiempo_real(request):
    """
    Endpoint para actualización en tiempo real (polling cada 5-10 segundos).
    Solo datos críticos que cambian frecuentemente.
    """
    ahora = timezone.now()
    hoy = ahora.date()
    
    return Response({
        'timestamp': ahora.isoformat(),
        
        # Datos que cambian frecuentemente
        'boxes_disponibles': Box.objects.filter(
            estado='DISPONIBLE',
            activo=True
        ).count(),
        
        'atenciones_en_curso': Atencion.objects.filter(
            estado='EN_CURSO'
        ).count(),
        
        'pacientes_en_espera': Paciente.objects.filter(
            estado_actual='EN_ESPERA',
            activo=True
        ).count(),
        
        'rutas_en_progreso': RutaClinica.objects.filter(
            estado='EN_PROGRESO'
        ).count(),
        
        # Última actividad
        'ultima_atencion': get_ultima_atencion(),
        'ultimo_paciente': get_ultimo_paciente(),
    })


def get_ultima_atencion():
    """Helper para obtener la última atención iniciada"""
    try:
        ultima = Atencion.objects.filter(
            estado='EN_CURSO'
        ).order_by('-inicio_cronometro').first()
        
        if ultima:
            return {
                'id': str(ultima.id),
                'paciente': ultima.paciente.identificador_hash[:12],
                'box': ultima.box.numero,
                'hora_inicio': ultima.inicio_cronometro.isoformat() if ultima.inicio_cronometro else None,
            }
    except:
        pass
    return None


def get_ultimo_paciente():
    """Helper para obtener el último paciente ingresado"""
    try:
        ultimo = Paciente.objects.filter(
            activo=True
        ).order_by('-fecha_ingreso').first()
        
        if ultimo:
            return {
                'id': str(ultimo.id),
                'nombre': ultimo.metadatos_adicionales.get('nombre', 'Paciente') 
                         if isinstance(ultimo.metadatos_adicionales, dict)
                         else f'Paciente {ultimo.identificador_hash[:8]}',
                'estado': ultimo.get_estado_actual_display(),
                'urgencia': ultimo.get_nivel_urgencia_display(),
                'hora_ingreso': ultimo.fecha_ingreso.isoformat(),
            }
    except:
        pass
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])  # 🆕 PERMISO MEJORADO
def dashboard_estadisticas_detalladas(request):
    """
    Endpoint para estadísticas más detalladas (para gráficos avanzados).
    """
    periodo = request.GET.get('periodo', '7')  # días
    dias = int(periodo)
    
    fecha_inicio = timezone.now() - timedelta(days=dias)
    
    # Estadísticas por día
    estadisticas_diarias = []
    for i in range(dias):
        dia = (timezone.now() - timedelta(days=dias-i-1)).date()
        
        estadisticas_diarias.append({
            'fecha': dia.isoformat(),
            'pacientes_nuevos': Paciente.objects.filter(
                fecha_ingreso__date=dia
            ).count(),
            'atenciones_total': Atencion.objects.filter(
                fecha_hora_inicio__date=dia
            ).count(),
            'atenciones_completadas': Atencion.objects.filter(
                fecha_hora_inicio__date=dia,
                estado='COMPLETADA'
            ).count(),
            'rutas_completadas': RutaClinica.objects.filter(
                fecha_fin_real__date=dia,
                estado='COMPLETADA'
            ).count(),
        })
    
    # # Estadísticas por especialidad médica
    # por_especialidad = {}
    # for esp_key, esp_label in Medico.ESPECIALIDAD_CHOICES:
    #     atenciones = Atencion.objects.filter(
    #         medico__especialidad_principal=esp_key,
    #         fecha_hora_inicio__gte=fecha_inicio
    #     )
        
    #     por_especialidad[esp_key] = {
    #         'label': esp_label,
    #         'atenciones': atenciones.count(),
    #         'tiempo_promedio': atenciones.filter(
    #             duracion_real__isnull=False
    #         ).aggregate(promedio=Avg('duracion_real'))['promedio'] or 0
    #     }
    
    # return Response({
    #     'periodo_dias': dias,
    #     'fecha_inicio': fecha_inicio.date().isoformat(),
    #     'fecha_fin': timezone.now().date().isoformat(),
    #     'estadisticas_diarias': estadisticas_diarias,
    #     'por_especialidad': por_especialidad,
    # })
    

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOrStaff])  # 🆕 PERMISO MEJORADO
def nexathink_insights(request):
    """
    Endpoint para obtener insights inteligentes de NexaThink.
    
    GET /api/dashboard/nexathink-insights/
    """
    try:
        analyzer = NexaThinkAnalyzer()
        insights = analyzer.generar_insights()
        
        return Response({
            'timestamp': timezone.now().isoformat(),
            'total_insights': len(insights),
            'insights': insights,
            'status': 'success'
        })
    
    except Exception as e:
        return Response({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)