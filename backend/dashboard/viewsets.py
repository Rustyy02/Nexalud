from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta

from pacientes.models import Paciente
from boxes.models import Box
from atenciones.models import Atencion, Medico
from rutas_clinicas.models import RutaClinica


class DashboardViewSet(viewsets.ViewSet):
    
    # ViewSet para el dashboard administrativo con métricas en tiempo real.
    # Solo accesible para usuarios administradores.
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def metricas_generales(self, request):
        """
        Obtiene métricas generales del sistema en tiempo real.
        GET /api/dashboard/metricas_generales/
        """
        hoy = timezone.now().date()
        ahora = timezone.now()
        
        # ============================================
        # MÉTRICAS DE PACIENTES
        # ============================================
        pacientes_totales = Paciente.objects.filter(activo=True).count()
        pacientes_hoy = Paciente.objects.filter(
            fecha_ingreso__date=hoy,
            activo=True
        ).count()
        
        # Por estado
        pacientes_por_estado = {}
        for estado_key, estado_label in Paciente.ESTADO_CHOICES:
            count = Paciente.objects.filter(
                estado_actual=estado_key,
                activo=True
            ).count()
            pacientes_por_estado[estado_key] = {
                'label': estado_label,
                'count': count,
                'porcentaje': round((count / pacientes_totales * 100) if pacientes_totales > 0 else 0, 2)
            }
        
        # Por urgencia
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
        
        # ============================================
        # MÉTRICAS DE BOXES
        # ============================================
        boxes_totales = Box.objects.filter(activo=True).count()
        boxes_disponibles = Box.objects.filter(
            estado='DISPONIBLE',
            activo=True
        ).count()
        boxes_ocupados = Box.objects.filter(
            estado='OCUPADO',
            activo=True
        ).count()
        boxes_mantenimiento = Box.objects.filter(
            estado='MANTENIMIENTO',
            activo=True
        ).count()
        
        tasa_ocupacion = round((boxes_ocupados / boxes_totales * 100) if boxes_totales > 0 else 0, 2)
        
        # ============================================
        # MÉTRICAS DE ATENCIONES
        # ============================================
        atenciones_hoy = Atencion.objects.filter(
            fecha_hora_inicio__date=hoy
        ).count()
        
        atenciones_en_curso = Atencion.objects.filter(
            estado='EN_CURSO'
        ).count()
        
        atenciones_completadas_hoy = Atencion.objects.filter(
            fecha_hora_inicio__date=hoy,
            estado='COMPLETADA'
        ).count()
        
        atenciones_pendientes = Atencion.objects.filter(
            estado__in=['PROGRAMADA', 'EN_ESPERA']
        ).count()
        
        # Tiempo promedio de atención
        tiempo_promedio_atencion = Atencion.objects.filter(
            fecha_hora_inicio__date=hoy,
            estado='COMPLETADA',
            duracion_real__isnull=False
        ).aggregate(promedio=Avg('duracion_real'))['promedio'] or 0
        
        # Atenciones retrasadas
        atenciones_en_curso_list = Atencion.objects.filter(estado='EN_CURSO')
        atenciones_retrasadas = sum(1 for a in atenciones_en_curso_list if a.is_retrasada())
        
        # Por tipo de atención
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
        
        # ============================================
        # MÉTRICAS DE RUTAS CLÍNICAS
        # ============================================
        rutas_activas = RutaClinica.objects.filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        ).count()
        
        rutas_pausadas = RutaClinica.objects.filter(
            esta_pausado=True
        ).count()
        
        rutas_completadas_hoy = RutaClinica.objects.filter(
            fecha_fin_real__date=hoy,
            estado='COMPLETADA'
        ).count()
        
        # Progreso promedio de rutas activas
        progreso_promedio_rutas = RutaClinica.objects.filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        ).aggregate(promedio=Avg('porcentaje_completado'))['promedio'] or 0
        
        # Detectar rutas con retraso
        rutas_con_retraso = 0
        for ruta in RutaClinica.objects.filter(estado='EN_PROGRESO'):
            if ruta.detectar_retrasos():
                rutas_con_retraso += 1
        
        # ============================================
        # MÉTRICAS DE MÉDICOS
        # ============================================
        medicos_activos = Medico.objects.filter(activo=True).count()
        medicos_atendiendo_hoy = Medico.objects.filter(
            atenciones__fecha_hora_inicio__date=hoy,
            activo=True
        ).distinct().count()
        
        # Top 5 médicos por atenciones hoy
        top_medicos = Medico.objects.filter(
            atenciones__fecha_hora_inicio__date=hoy,
            activo=True
        ).annotate(
            total_atenciones=Count('atenciones')
        ).order_by('-total_atenciones')[:5].values(
            'id',
            'nombre',
            'apellido',
            'especialidad_principal',
            'total_atenciones'
        )
        
        # ============================================
        # ALERTAS Y NOTIFICACIONES
        # ============================================
        alertas = []
        
        # Alerta: Boxes con baja disponibilidad
        if tasa_ocupacion > 80:
            alertas.append({
                'tipo': 'warning',
                'categoria': 'boxes',
                'mensaje': f'Alta ocupación de boxes: {tasa_ocupacion}%',
                'prioridad': 'alta'
            })
        
        # Alerta: Atenciones retrasadas
        if atenciones_retrasadas > 0:
            alertas.append({
                'tipo': 'danger',
                'categoria': 'atenciones',
                'mensaje': f'{atenciones_retrasadas} atención(es) retrasada(s)',
                'prioridad': 'alta'
            })
        
        # Alerta: Rutas con retraso
        if rutas_con_retraso > 0:
            alertas.append({
                'tipo': 'warning',
                'categoria': 'rutas',
                'mensaje': f'{rutas_con_retraso} ruta(s) clínica(s) con retraso',
                'prioridad': 'media'
            })
        
        # Alerta: Rutas pausadas
        if rutas_pausadas > 0:
            alertas.append({
                'tipo': 'info',
                'categoria': 'rutas',
                'mensaje': f'{rutas_pausadas} ruta(s) clínica(s) pausada(s)',
                'prioridad': 'media'
            })
        
        # ============================================
        # RESPUESTA CONSOLIDADA
        # ============================================
        return Response({
            'timestamp': ahora.isoformat(),
            
            'pacientes': {
                'totales': pacientes_totales,
                'hoy': pacientes_hoy,
                'por_estado': pacientes_por_estado,
                'por_urgencia': pacientes_por_urgencia,
            },
            
            'boxes': {
                'totales': boxes_totales,
                'disponibles': boxes_disponibles,
                'ocupados': boxes_ocupados,
                'mantenimiento': boxes_mantenimiento,
                'tasa_ocupacion': tasa_ocupacion,
            },
            
            'atenciones': {
                'hoy': atenciones_hoy,
                'en_curso': atenciones_en_curso,
                'completadas_hoy': atenciones_completadas_hoy,
                'pendientes': atenciones_pendientes,
                'retrasadas': atenciones_retrasadas,
                'tiempo_promedio': round(tiempo_promedio_atencion, 2),
                'por_tipo': atenciones_por_tipo,
            },
            
            'rutas_clinicas': {
                'activas': rutas_activas,
                'pausadas': rutas_pausadas,
                'completadas_hoy': rutas_completadas_hoy,
                'progreso_promedio': round(progreso_promedio_rutas, 2),
                'con_retraso': rutas_con_retraso,
            },
            
            'medicos': {
                'activos': medicos_activos,
                'atendiendo_hoy': medicos_atendiendo_hoy,
                'top_medicos': list(top_medicos),
            },
            
            'alertas': alertas,
        })
    
    @action(detail=False, methods=['get'])
    def grafico_atenciones_hora(self, request):
        """
        Datos para gráfico de atenciones por hora del día.
        GET /api/dashboard/grafico_atenciones_hora/
        """
        hoy = timezone.now().date()
        
        # Crear array de 24 horas
        atenciones_por_hora = []
        for hora in range(24):
            count = Atencion.objects.filter(
                fecha_hora_inicio__date=hoy,
                fecha_hora_inicio__hour=hora
            ).count()
            
            atenciones_por_hora.append({
                'hora': f"{hora:02d}:00",
                'cantidad': count
            })
        
        return Response({
            'fecha': hoy.isoformat(),
            'datos': atenciones_por_hora
        })
    
    @action(detail=False, methods=['get'])
    def grafico_progreso_rutas(self, request):
        """
        Datos para gráfico de progreso de rutas clínicas.
        GET /api/dashboard/grafico_progreso_rutas/
        """
        rutas_activas = RutaClinica.objects.filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        )
        
        # Agrupar por rangos de progreso
        rangos = {
            '0-25%': 0,
            '26-50%': 0,
            '51-75%': 0,
            '76-100%': 0,
        }
        
        for ruta in rutas_activas:
            progreso = ruta.porcentaje_completado
            if progreso <= 25:
                rangos['0-25%'] += 1
            elif progreso <= 50:
                rangos['26-50%'] += 1
            elif progreso <= 75:
                rangos['51-75%'] += 1
            else:
                rangos['76-100%'] += 1
        
        return Response({
            'rangos': rangos,
            'total_rutas': rutas_activas.count()
        })
    
    @action(detail=False, methods=['get'])
    def actividad_reciente(self, request):
        """
        Lista de actividad reciente del sistema.
        GET /api/dashboard/actividad_reciente/
        """
        limite = int(request.query_params.get('limite', 20))
        
        actividades = []
        
        # Últimas atenciones iniciadas
        atenciones_recientes = Atencion.objects.filter(
            inicio_cronometro__isnull=False
        ).order_by('-inicio_cronometro')[:limite]
        
        for atencion in atenciones_recientes:
            actividades.append({
                'timestamp': atencion.inicio_cronometro.isoformat(),
                'tipo': 'atencion_iniciada',
                'icono': 'play',
                'titulo': 'Atención Iniciada',
                'descripcion': f'{atencion.get_tipo_atencion_display()} - Box {atencion.box.numero}',
                'paciente': atencion.paciente.identificador_hash[:12],
            })
        
        # Ordenar por timestamp
        actividades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'actividades': actividades[:limite]
        })