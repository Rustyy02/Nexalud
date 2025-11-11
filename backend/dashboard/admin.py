from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Avg, Sum, Q
from pacientes.models import Paciente
from boxes.models import Box
from atenciones.models import Atencion
from rutas_clinicas.models import RutaClinica
from users.models import User


class DashboardAdmin(admin.AdminSite):
    """
    AdminSite personalizado para el dashboard.
    Aunque no tiene modelos propios, puede agregar vistas personalizadas.
    """
    site_header = "Nexalud - Panel de Control"
    site_title = "Nexalud Admin"
    index_title = "Dashboard Principal"


# Registrar un modelo proxy simple para tener una entrada en el admin
class DashboardMetricas(Paciente):
    """Modelo proxy para mostrar métricas en el admin"""
    class Meta:
        proxy = True
        verbose_name = "Métrica del Sistema"
        verbose_name_plural = "📊 Dashboard y Métricas"


@admin.register(DashboardMetricas)
class DashboardMetricasAdmin(admin.ModelAdmin):
    """
    Admin personalizado que muestra métricas del sistema.
    No permite agregar/editar/eliminar, solo visualización.
    """
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Vista personalizada del dashboard con métricas"""
        
        # Métricas de Pacientes
        hoy = timezone.now().date()
        pacientes_hoy = Paciente.objects.filter(
            fecha_ingreso__date=hoy,
            activo=True
        ).count()
        
        pacientes_por_estado = Paciente.objects.filter(
            activo=True
        ).values('estado_actual').annotate(
            total=Count('id')
        )
        
        # Métricas de Boxes
        boxes_disponibles = Box.objects.filter(
            estado='DISPONIBLE',
            activo=True
        ).count()
        
        boxes_ocupados = Box.objects.filter(
            estado='OCUPADO',
            activo=True
        ).count()
        
        boxes_total = Box.objects.filter(activo=True).count()
        
        ocupacion_porcentaje = (boxes_ocupados / boxes_total * 100) if boxes_total > 0 else 0
        
        # Métricas de Atenciones
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
        
        # Tiempo promedio de atención hoy
        tiempo_promedio = Atencion.objects.filter(
            fecha_hora_inicio__date=hoy,
            estado='COMPLETADA',
            duracion_real__isnull=False
        ).aggregate(promedio=Avg('duracion_real'))['promedio'] or 0
        
        # Métricas de Rutas Clínicas
        rutas_activas = RutaClinica.objects.filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        ).count()
        
        rutas_completadas_hoy = RutaClinica.objects.filter(
            fecha_fin_real__date=hoy,
            estado='COMPLETADA'
        ).count()
        
        # Progreso promedio de rutas activas
        progreso_promedio = RutaClinica.objects.filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        ).aggregate(promedio=Avg('porcentaje_completado'))['promedio'] or 0
        
        # Médicos activos hoy (usando User con rol MEDICO)
        medicos_atendiendo = User.objects.filter(
            rol='MEDICO',
            atenciones_medico__fecha_hora_inicio__date=hoy,
            is_active=True
        ).distinct().count()
        
        medicos_total = User.objects.filter(
            rol='MEDICO',
            is_active=True
        ).count()
        
        #Etapas q se han retrasado
        etapas_retrasadas = 0
        for ruta in RutaClinica.objects.filter(estado='EN_PROGRESO'):
            if ruta.detectar_retrasos():
                etapas_retrasadas += 1
        
        # Atenciones por tipo
        atenciones_por_tipo = Atencion.objects.filter(
            fecha_hora_inicio__date=hoy
        ).values('tipo_atencion').annotate(
            total=Count('id')
        )
        
        #Top 5 médicos
        top_medicos = User.objects.filter(
            rol='MEDICO',
            atenciones_medico__fecha_hora_inicio__date=hoy,
            is_active=True
        ).annotate(
            total_atenciones=Count('atenciones_medico')
        ).order_by('-total_atenciones')[:5]
        
        # Boxes más utilizados
        top_boxes = Box.objects.filter(
            atenciones__fecha_hora_inicio__date=hoy,
            activo=True
        ).annotate(
            total_atenciones=Count('atenciones')
        ).order_by('-total_atenciones')[:5]
        
        context = extra_context or {}
        context.update({
            'title': 'Dashboard de Métricas',
            
            # Métricas generales para dashboard
            'pacientes_hoy': pacientes_hoy,
            'pacientes_por_estado': pacientes_por_estado,
            'atenciones_hoy': atenciones_hoy,
            'atenciones_en_curso': atenciones_en_curso,
            'atenciones_completadas_hoy': atenciones_completadas_hoy,
            'tiempo_promedio_atencion': tiempo_promedio,
            
            # Boxes
            'boxes_disponibles': boxes_disponibles,
            'boxes_ocupados': boxes_ocupados,
            'boxes_total': boxes_total,
            'ocupacion_porcentaje': ocupacion_porcentaje,
            
            # Rutas clínicas
            'rutas_activas': rutas_activas,
            'rutas_completadas_hoy': rutas_completadas_hoy,
            'progreso_promedio': progreso_promedio,
            
            # Médicos
            'medicos_atendiendo': medicos_atendiendo,
            'medicos_total': medicos_total,
            
            # Detallado
            'etapas_retrasadas': etapas_retrasadas,
            'atenciones_por_tipo': atenciones_por_tipo,
            'top_medicos': top_medicos,
            'top_boxes': top_boxes,
            
            # Metadata
            'fecha_actual': timezone.now(),
        })
        
        return render(request, 'admin/dashboard_metricas.html', context)
    
    class Media:
        css = {
            'all': ('admin/css/dashboard.css',)
        }


# Si quieres crear una vista de admin personalizada sin modelo
class MetricasGeneralesAdmin(admin.ModelAdmin):
    """
    Administrador adicional para métricas generales del sistema.
    """
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('metricas-tiempo-real/', 
                 self.admin_site.admin_view(self.metricas_tiempo_real_view),
                 name='metricas-tiempo-real'),
        ]
        return custom_urls + urls
    
    def metricas_tiempo_real_view(self, request):
        """Vista de métricas en tiempo real"""
        context = {
            'title': 'Métricas en Tiempo Real',
            'atenciones_activas': Atencion.objects.filter(estado='EN_CURSO'),
            'boxes_ocupados': Box.objects.filter(estado='OCUPADO'),
            'pacientes_en_espera': Paciente.objects.filter(estado_actual='EN_ESPERA'),
        }
        return render(request, 'admin/metricas_tiempo_real.html', context)