from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import RutaClinica, EtapaRuta


class EtapaRutaInline(admin.TabularInline):
    model = EtapaRuta
    extra = 0
    fields = [
        'orden',
        'nombre',
        'tipo_etapa',
        'duracion_estimada',
        'estado',
        'es_estatico'
    ]
    readonly_fields = []
    ordering = ['orden']


@admin.register(RutaClinica)
class RutaClinicaAdmin(admin.ModelAdmin):
    list_display = [
        'id_corto',
        'paciente_info',
        'progreso_bar',
        'estado_badge',
        'fecha_inicio',
        'tiempo_info',
        'etapa_actual_info'
    ]
    list_filter = [
        'estado',
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
        'tiempo_total_info',
        'proxima_etapa_info',
        'retrasos_info'
    ]
    date_hierarchy = 'fecha_inicio'
    inlines = [EtapaRutaInline]
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'paciente',
                'estado',
                'porcentaje_completado',
            )
        }),
        ('Cronología', {
            'fields': (
                'fecha_inicio',
                'fecha_estimada_fin',
                'fecha_fin_real',
            )
        }),
        ('Información de Progreso', {
            'fields': (
                'tiempo_total_info',
                'proxima_etapa_info',
                'retrasos_info',
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
    
    def progreso_bar(self, obj):
        progreso = obj.porcentaje_completado
        color = 'green' if progreso >= 75 else 'orange' if progreso >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{:.1f}%</div></div>',
            progreso, color, progreso
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
    
    def tiempo_info(self, obj):
        tiempo_real = obj.obtener_tiempo_total_real()
        tiempo_estimado = obj.obtener_tiempo_total_estimado()
        
        horas_real = int(tiempo_real.total_seconds() / 3600)
        min_real = int((tiempo_real.total_seconds() % 3600) / 60)
        
        horas_est = int(tiempo_estimado.total_seconds() / 3600)
        min_est = int((tiempo_estimado.total_seconds() % 3600) / 60)
        
        return format_html(
            '<strong>Real:</strong> {}h {}m<br>'
            '<strong>Estimado:</strong> {}h {}m',
            horas_real, min_real, horas_est, min_est
        )
    tiempo_info.short_description = "Tiempo"
    
    def etapa_actual_info(self, obj):
        etapa = obj.obtener_etapa_actual()
        if etapa:
            return format_html(
                '<strong>{}</strong><br><small>{}</small>',
                etapa.nombre,
                etapa.get_tipo_etapa_display()
            )
        proxima = obj.obtener_proxima_etapa()
        if proxima:
            return format_html(
                '<em>Próxima: {}</em>',
                proxima.nombre
            )
        return "Sin etapas activas"
    etapa_actual_info.short_description = "Etapa Actual"
    
    def tiempo_total_info(self, obj):
        tiempo_real = obj.obtener_tiempo_total_real()
        tiempo_estimado = obj.obtener_tiempo_total_estimado()
        return format_html(
            '<strong>Tiempo real:</strong> {}<br>'
            '<strong>Tiempo estimado:</strong> {}',
            tiempo_real,
            tiempo_estimado
        )
    tiempo_total_info.short_description = "Información de Tiempo"
    
    def proxima_etapa_info(self, obj):
        etapa_actual = obj.obtener_etapa_actual()
        proxima = obj.obtener_proxima_etapa()
        
        info = ""
        if etapa_actual:
            info += f"<strong>Etapa actual:</strong> {etapa_actual.nombre}<br>"
        if proxima:
            info += f"<strong>Próxima etapa:</strong> {proxima.nombre}<br>"
        
        return format_html(info) if info else "No hay etapas pendientes"
    proxima_etapa_info.short_description = "Información de Etapas"
    
    def retrasos_info(self, obj):
        retrasos = obj.detectar_retrasos()
        if retrasos:
            info = "<strong>Etapas retrasadas:</strong><br>"
            for etapa in retrasos:
                info += f"- {etapa.nombre} (Orden {etapa.orden})<br>"
            return format_html('<span style="color: red;">{}</span>', info)
        return format_html('<span style="color: green;">Sin retrasos</span>')
    retrasos_info.short_description = "Retrasos Detectados"
    
    actions = [
        'recalcular_progreso',
        'pausar_rutas',
        'reanudar_rutas',
        'completar_rutas'
    ]
    
    def recalcular_progreso(self, request, queryset):
        for ruta in queryset:
            ruta.calcular_progreso()
        self.message_user(request, f'Progreso recalculado para {queryset.count()} rutas.')
    recalcular_progreso.short_description = "Recalcular progreso"
    
    def pausar_rutas(self, request, queryset):
        for ruta in queryset:
            ruta.pausar_ruta("Pausado desde administración")
        self.message_user(request, f'{queryset.count()} rutas pausadas.')
    pausar_rutas.short_description = "Pausar rutas"
    
    def reanudar_rutas(self, request, queryset):
        for ruta in queryset:
            ruta.reanudar_ruta()
        self.message_user(request, f'{queryset.count()} rutas reanudadas.')
    reanudar_rutas.short_description = "Reanudar rutas"
    
    def completar_rutas(self, request, queryset):
        updated = queryset.update(
            estado='COMPLETADA',
            fecha_fin_real=timezone.now(),
            porcentaje_completado=100.0
        )
        self.message_user(request, f'{updated} rutas marcadas como completadas.')
    completar_rutas.short_description = "Marcar como completadas"


@admin.register(EtapaRuta)
class EtapaRutaAdmin(admin.ModelAdmin):
    list_display = [
        'orden',
        'nombre',
        'ruta_paciente',
        'tipo_etapa',
        'estado_badge',
        'duracion_info',
        'estatico_badge',
        'avance_bar'
    ]
    list_filter = [
        'estado',
        'tipo_etapa',
        'es_estatico',
        'ruta_clinica__estado'
    ]
    search_fields = [
        'nombre',
        'ruta_clinica__paciente__identificador_hash',
        'descripcion'
    ]
    readonly_fields = [
        'duracion_real',
        'fecha_actualizacion',
        'tiempo_transcurrido_display',
        'porcentaje_avance_display',
        'retraso_display'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'ruta_clinica',
                'orden',
                'nombre',
                'tipo_etapa',
                'estado',
            )
        }),
        ('Cronología', {
            'fields': (
                'fecha_inicio',
                'fecha_fin',
                'duracion_estimada',
                'duracion_real',
            )
        }),
        ('Estado Estático', {
            'fields': (
                'es_estatico',
                'motivo_pausa',
            )
        }),
        ('Información Adicional', {
            'fields': (
                'descripcion',
                'configuracion_etapa',
            ),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': (
                'tiempo_transcurrido_display',
                'porcentaje_avance_display',
                'retraso_display',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def ruta_paciente(self, obj):
        return obj.ruta_clinica.paciente.identificador_hash[:12]
    ruta_paciente.short_description = "Paciente"
    
    def estado_badge(self, obj):
        colors = {
            'PENDIENTE': 'gray',
            'EN_PROCESO': 'green',
            'COMPLETADA': 'blue',
            'PAUSADA': 'orange',
            'CANCELADA': 'red'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def duracion_info(self, obj):
        est = obj.duracion_estimada
        real = obj.duracion_real if obj.duracion_real else "-"
        
        if obj.duracion_real:
            diferencia = obj.duracion_real - obj.duracion_estimada
            if diferencia > 0:
                color = "red"
                simbolo = "+"
            else:
                color = "green"
                simbolo = ""
            
            return format_html(
                'Est: {} min<br>Real: {} min<br>'
                '<span style="color: {};">({}{})</span>',
                est, real, color, simbolo, diferencia
            )
        return f"Est: {est} min"
    duracion_info.short_description = "Duración"
    
    def estatico_badge(self, obj):
        if obj.es_estatico:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⏸ Estático</span>'
            )
        return format_html(
            '<span style="color: green;">▶ Activo</span>'
        )
    estatico_badge.short_description = "Tipo"
    
    def avance_bar(self, obj):
        avance = obj.obtener_porcentaje_avance()
        color = 'green' if avance >= 75 else 'orange' if avance >= 50 else 'red'
        return format_html(
            '<div style="width: 80px; background: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background: {}; height: 18px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 10px; line-height: 18px;">'
            '{:.0f}%</div></div>',
            avance, color, avance
        )
    avance_bar.short_description = "Avance"
    
    def tiempo_transcurrido_display(self, obj):
        tiempo = obj.calcular_tiempo_transcurrido()
        if tiempo:
            minutos = int(tiempo.total_seconds() / 60)
            return f"{minutos} minutos"
        return "No iniciada"
    tiempo_transcurrido_display.short_description = "Tiempo Transcurrido"
    
    def porcentaje_avance_display(self, obj):
        return f"{obj.obtener_porcentaje_avance():.1f}%"
    porcentaje_avance_display.short_description = "Porcentaje de Avance"
    
    def retraso_display(self, obj):
        if obj.detectar_retraso():
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Retrasada</span>'
            )
        return format_html(
            '<span style="color: green;">✓ En tiempo</span>'
        )
    retraso_display.short_description = "Estado de Retraso"
    
    actions = [
        'iniciar_etapas',
        'finalizar_etapas',
        'pausar_etapas',
        'reanudar_etapas'
    ]
    
    def iniciar_etapas(self, request, queryset):
        count = 0
        for etapa in queryset:
            if etapa.iniciar_etapa():
                count += 1
        self.message_user(request, f'{count} etapas iniciadas.')
    iniciar_etapas.short_description = "Iniciar etapas"
    
    def finalizar_etapas(self, request, queryset):
        count = 0
        for etapa in queryset:
            if etapa.finalizar_etapa():
                count += 1
        self.message_user(request, f'{count} etapas finalizadas.')
    finalizar_etapas.short_description = "Finalizar etapas"
    
    def pausar_etapas(self, request, queryset):
        count = 0
        for etapa in queryset:
            if etapa.pausar_etapa("Pausado desde administración"):
                count += 1
        self.message_user(request, f'{count} etapas pausadas.')
    pausar_etapas.short_description = "Pausar etapas"
    
    def reanudar_etapas(self, request, queryset):
        count = 0
        for etapa in queryset:
            if etapa.reanudar_etapa():
                count += 1
        self.message_user(request, f'{count} etapas reanudadas.')
    reanudar_etapas.short_description = "Reanudar etapas"