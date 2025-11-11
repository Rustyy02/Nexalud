from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import RutaClinica
from .RutaClinicaAdminForm import RutaClinicaAdminForm


@admin.register(RutaClinica)
class RutaClinicaAdmin(admin.ModelAdmin):
    form = RutaClinicaAdminForm
    
    list_display = [
        'id_corto',
        'paciente_info',
        'etapa_actual_badge',
        'progreso_bar',
        'estado_badge',
        'pausado_badge',
        'fecha_inicio',
        'tiempo_info'
    ]
    list_filter = [
        'estado',
        'etapa_actual',
        'esta_pausado',
        'fecha_inicio',
        'porcentaje_completado'
    ]
    search_fields = [
        'id',
        'paciente__identificador_hash'
    ]
    readonly_fields = [
        'porcentaje_completado',
        'fecha_actualizacion',
        'etapas_completadas',
        'timestamps_etapas',
        'indice_etapa_actual',
        'tiempo_total_info',
        'etapas_orden_display',
        'timeline_info'
        
    ]
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'paciente',
                'estado',
                'esta_pausado',
                'motivo_pausa',
            )
        }),
        ('Etapas', {
            'fields': (
                'etapas_seleccionadas',
                'etapa_actual',
                'indice_etapa_actual',
                'etapas_completadas',
                'porcentaje_completado',
            )
        }),
        ('Cronología', {
            'fields': (
                'fecha_inicio',
                'fecha_estimada_fin',
                'fecha_fin_real',
                'timestamps_etapas',
            )
        }),
        ('Información de Progreso', {
            'fields': (
                'tiempo_total_info',
                'timeline_info',
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'metadatos_adicionales',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def id_corto(self, obj):
        return f"{str(obj.id)[:8]}..."
    id_corto.short_description = "ID"
    
    def paciente_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.paciente.identificador_hash[:12],
            obj.paciente.get_estado_actual_display()
        )
    paciente_info.short_description = "Paciente"
    
    def etapa_actual_badge(self, obj):
        if obj.etapa_actual:
            return format_html(
                '<span style="background: #2196F3; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 11px;">{}</span>',
                obj.get_etapa_actual_display()
            )
        return format_html(
            '<span style="color: gray;">Sin etapa</span>'
        )
    etapa_actual_badge.short_description = "Etapa Actual"
    
    def progreso_bar(self, obj):
        progreso = obj.porcentaje_completado
        color = 'green' if progreso >= 75 else 'orange' if progreso >= 50 else 'red'

        progreso_texto = f"{progreso:.1f}"  # formateamos antes de pasar a format_html

        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%</div></div>',
            progreso_texto,  # ancho
            color,           # color
            progreso_texto   # texto mostrado
        )

    progreso_bar.short_description = "Progreso"
    
    def estado_badge(self, obj):
        colors = {
            'INICIADA': 'blue',
            'EN_PROGRESO': 'green',
            'PAUSADA': 'orange',
            'COMPLETADA': 'gray',
            'CANCELADA': 'red'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def pausado_badge(self, obj):
        if obj.esta_pausado:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏸ Pausado</span>'
            )
        return format_html(
            '<span style="color: green;">▶ Activo</span>'
        )
    pausado_badge.short_description = "Estado Pausa"
    
    def tiempo_info(self, obj):
        tiempo_real = obj.obtener_tiempo_total_real()
        
        horas_real = int(tiempo_real.total_seconds() / 3600)
        min_real = int((tiempo_real.total_seconds() % 3600) / 60)
        
        return format_html(
            '<strong>{}h {}m</strong>',
            horas_real, min_real
        )
    tiempo_info.short_description = "Tiempo"
    
    def tiempo_total_info(self, obj):
        tiempo_real = obj.obtener_tiempo_total_real()
        return format_html(
            '<strong>Tiempo transcurrido:</strong> {}<br>',
            tiempo_real
        )
    tiempo_total_info.short_description = "Información de Tiempo"
    
    def timeline_info(self, obj):
        timeline = obj.obtener_info_timeline()
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f5f5f5; font-weight: bold;">'
        html += '<td style="padding: 8px; border: 1px solid #ddd;">Orden</td>'
        html += '<td style="padding: 8px; border: 1px solid #ddd;">Etapa</td>'
        html += '<td style="padding: 8px; border: 1px solid #ddd;">Estado</td>'
        html += '<td style="padding: 8px; border: 1px solid #ddd;">Inicio</td>'
        html += '<td style="padding: 8px; border: 1px solid #ddd;">Fin</td>'
        html += '</tr>'
        
        for etapa in timeline:
            color = 'green' if etapa['estado'] == 'COMPLETADA' else 'blue' if etapa['estado'] == 'EN_PROCESO' else 'gray'
            html += f'<tr style="{"background: #e3f2fd;" if etapa["es_actual"] else ""}">'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{etapa["orden"]}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;"><strong>{etapa["etapa_label"]}</strong></td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; color: {color};">{etapa["estado"]}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{etapa["fecha_inicio"] or "-"}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{etapa["fecha_fin"] or "-"}</td>'
            html += '</tr>'
        
        html += '</table>'
        return format_html(html)
    timeline_info.short_description = "Timeline de Etapas"
    
    actions = [
        'iniciar_rutas',
        'pausar_rutas',
        'reanudar_rutas',
        'completar_rutas',
        'recalcular_progreso'
    ]
    
    def iniciar_rutas(self, request, queryset):
        count = 0
        for ruta in queryset:
            if ruta.iniciar_ruta():
                count += 1
        self.message_user(request, f'{count} rutas iniciadas.')
    iniciar_rutas.short_description = "Iniciar rutas seleccionadas"
    
    def pausar_rutas(self, request, queryset):
        for ruta in queryset:
            ruta.pausar_ruta("Pausado desde administración")
        self.message_user(request, f'{queryset.count()} rutas pausadas.')
    pausar_rutas.short_description = "Pausar rutas"
    
    def reanudar_rutas(self, request, queryset):
        count = 0
        for ruta in queryset:
            if ruta.reanudar_ruta():
                count += 1
        self.message_user(request, f'{count} rutas reanudadas.')
    reanudar_rutas.short_description = "Reanudar rutas"
    
    def completar_rutas(self, request, queryset):
        updated = queryset.update(
            estado='COMPLETADA',
            fecha_fin_real=timezone.now(),
            porcentaje_completado=100.0
        )
        self.message_user(request, f'{updated} rutas marcadas como completadas.')
    completar_rutas.short_description = "Marcar como completadas"
    
    def recalcular_progreso(self, request, queryset):
        for ruta in queryset:
            # Calcular progreso
            ruta.calcular_progreso()
        self.message_user(request, f'Progreso recalculado para {queryset.count()} rutas.')
    recalcular_progreso.short_description = "Recalcular progreso"
    
    def etapas_orden_display(self, obj):
        # Orden correcto de las etapas
        todas_etapas = [key for key, _ in RutaClinica.ETAPAS_CHOICES]
        
        html = '<div style="font-family: monospace; line-height: 2;">'
        html += '<strong>Orden del Sistema (fijo):</strong><br>'
        
        for i, etapa_key in enumerate(todas_etapas):
            label = dict(RutaClinica.ETAPAS_CHOICES).get(etapa_key)
            
            # Determinar color
            if etapa_key in obj.etapas_completadas:
                color = '#4CAF50'
                icon = '✓'
            elif etapa_key == obj.etapa_actual:
                color = '#2196F3'
                icon = '▶'
            elif etapa_key in obj.etapas_seleccionadas:
                color = '#FF9800'
                icon = '○'
            else:
                color = '#9E9E9E'
                icon = '—'
            
            html += f'<span style="color: {color};">'
            html += f'{i+1}. {icon} {label}'
            html += '</span><br>'
        
        html += '</div>'
        return format_html(html)
    
    etapas_orden_display.short_description = "Orden de Etapas"