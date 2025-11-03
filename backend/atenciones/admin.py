from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Medico, Atencion


@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    """
    Admin para el modelo Medico (legacy).
    Este modelo se mantiene para compatibilidad con datos históricos.
    """
    list_display = [
        'codigo_medico', 
        'nombre_completo_display', 
        'especialidad_principal', 
        'activo_badge',
        'fecha_ingreso',
        'atenciones_hoy'
    ]
    list_filter = [
        'especialidad_principal', 
        'activo', 
        'fecha_ingreso'
    ]
    search_fields = [
        'codigo_medico', 
        'nombre', 
        'apellido'
    ]
    readonly_fields = [
        'fecha_ingreso', 
        'tiempo_promedio_display',
        'metricas_eficiencia'
    ]
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                'codigo_medico',
                'nombre',
                'apellido',
            )
        }),
        ('Especialidades', {
            'fields': (
                'especialidad_principal',
                'especialidades_secundarias',
            )
        }),
        ('Configuración', {
            'fields': (
                'horarios_atencion',
                'configuraciones_personales',
                'activo',
            )
        }),
        ('Métricas', {
            'fields': (
                'fecha_ingreso',
                'tiempo_promedio_display',
                'metricas_eficiencia',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_completo_display(self, obj):
        return obj.nombre_completo
    nombre_completo_display.short_description = "Nombre Completo"
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>'
        )
    activo_badge.short_description = "Estado"
    
    def atenciones_hoy(self, obj):
        hoy = timezone.now().date()
        count = obj.atenciones.filter(fecha_hora_inicio__date=hoy).count()
        return f"{count} atenciones"
    atenciones_hoy.short_description = "Atenciones Hoy"
    
    def tiempo_promedio_display(self, obj):
        tiempo = obj.calcular_tiempo_promedio_atencion()
        return f"{tiempo:.1f} minutos"
    tiempo_promedio_display.short_description = "Tiempo Promedio (30 días)"
    
    def metricas_eficiencia(self, obj):
        metricas = obj.obtener_eficiencia()
        return format_html(
            '<strong>Atenciones mes:</strong> {}<br>'
            '<strong>Tiempo promedio:</strong> {:.1f} min<br>'
            '<strong>Score eficiencia:</strong> {:.1f}%',
            metricas['atenciones_mes'],
            metricas['tiempo_promedio'],
            metricas['eficiencia_score']
        )
    metricas_eficiencia.short_description = "Métricas de Eficiencia"
    
    actions = ['activar_medicos', 'desactivar_medicos']
    
    def activar_medicos(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} médicos activados.')
    activar_medicos.short_description = "Activar médicos seleccionados"
    
    def desactivar_medicos(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} médicos desactivados.')
    desactivar_medicos.short_description = "Desactivar médicos seleccionados"


@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    """
    Admin para Atenciones.
    El campo médico ahora apunta a User con rol MEDICO.
    """
    list_display = [
        'id_corto',
        'paciente_info',
        'medico_info',  # ✅ Actualizado para mostrar User
        'box',
        'tipo_atencion',
        'estado_badge',
        'fecha_hora_inicio',
        'duracion_info',
        'retraso_info'
    ]
    list_filter = [
        'estado',
        'tipo_atencion',
        'fecha_hora_inicio',
        'box__especialidad'
    ]
    search_fields = [
        'id',
        'paciente__identificador_hash',
        'medico__username',  # ✅ Actualizado
        'medico__first_name',  # ✅ Actualizado
        'medico__last_name',  # ✅ Actualizado
        'box__numero'
    ]
    readonly_fields = [
        'fecha_creacion',
        'fecha_actualizacion',
        'duracion_real',
        'tiempo_transcurrido_display',
        'metricas_atencion'
    ]
    date_hierarchy = 'fecha_hora_inicio'
    
    # ✅ Filtrar solo usuarios con rol MEDICO
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "medico":
            from users.models import User
            kwargs["queryset"] = User.objects.filter(rol='MEDICO')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'paciente',
                'medico',  # ✅ Ahora apunta a User
                'box',
                'tipo_atencion',
                'estado',
            )
        }),
        ('Planificación', {
            'fields': (
                'fecha_hora_inicio',
                'fecha_hora_fin',
                'duracion_planificada',
            )
        }),
        ('Ejecución Real (Cronómetro)', {
            'fields': (
                'inicio_cronometro',
                'fin_cronometro',
                'duracion_real',
                'tiempo_transcurrido_display',
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Métricas', {
            'fields': ('metricas_atencion',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
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
    
    # ✅ Actualizado para mostrar información de User
    def medico_info(self, obj):
        nombre = obj.medico.get_full_name() or obj.medico.username
        return format_html(
            '<strong>{}</strong><br><small>Médico</small>',
            nombre
        )
    medico_info.short_description = "Médico"
    
    def estado_badge(self, obj):
        colors = {
            'PROGRAMADA': 'blue',
            'EN_ESPERA': 'orange',
            'EN_CURSO': 'green',
            'COMPLETADA': 'gray',
            'CANCELADA': 'red',
            'NO_PRESENTADO': 'darkred'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def duracion_info(self, obj):
        planificada = obj.duracion_planificada
        real = obj.duracion_real if obj.duracion_real else "-"
        
        if obj.duracion_real:
            diferencia = obj.calcular_diferencia_duracion()
            if diferencia > 0:
                color = "red"
                simbolo = "+"
            else:
                color = "green"
                simbolo = ""
            
            return format_html(
                'Plan: {} min<br>Real: {} min<br>'
                '<span style="color: {};">({}{})</span>',
                planificada, real, color, simbolo, diferencia
            )
        return f"Plan: {planificada} min"
    duracion_info.short_description = "Duración"
    
    def retraso_info(self, obj):
        if obj.estado in ['COMPLETADA', 'CANCELADA', 'NO_PRESENTADO']:
            retraso = obj.calcular_retraso()
            if retraso > 0:
                return format_html(
                    '<span style="color: red;">+{} min</span>',
                    retraso
                )
            return format_html(
                '<span style="color: green;">A tiempo</span>'
            )
        elif obj.estado == 'EN_CURSO' and obj.is_retrasada():
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Retrasada</span>'
            )
        return "-"
    retraso_info.short_description = "Retraso"
    
    def tiempo_transcurrido_display(self, obj):
        tiempo = obj.obtener_tiempo_transcurrido()
        if tiempo:
            minutos = int(tiempo.total_seconds() / 60)
            return f"{minutos} minutos"
        return "No iniciada"
    tiempo_transcurrido_display.short_description = "Tiempo Transcurrido"
    
    def metricas_atencion(self, obj):
        metricas = obj.generar_metricas()
        return format_html(
            '<strong>Tipo:</strong> {}<br>'
            '<strong>Duración planificada:</strong> {} min<br>'
            '<strong>Duración real:</strong> {} min<br>'
            '<strong>Retraso inicio:</strong> {} min<br>'
            '<strong>Diferencia duración:</strong> {} min<br>'
            '<strong>Estado:</strong> {}',
            metricas['tipo'],
            metricas['duracion_planificada'],
            metricas['duracion_real'] or 'N/A',
            metricas['retraso_inicio'],
            metricas['diferencia_duracion'],
            metricas['estado']
        )
    metricas_atencion.short_description = "Métricas Completas"
    
    actions = [
        'iniciar_atenciones',
        'finalizar_atenciones',
        'cancelar_atenciones'
    ]
    
    def iniciar_atenciones(self, request, queryset):
        count = 0
        for atencion in queryset:
            if atencion.iniciar_cronometro():
                count += 1
        self.message_user(request, f'{count} atenciones iniciadas.')
    iniciar_atenciones.short_description = "Iniciar cronómetro"
    
    def finalizar_atenciones(self, request, queryset):
        count = 0
        for atencion in queryset:
            if atencion.finalizar_cronometro():
                count += 1
        self.message_user(request, f'{count} atenciones finalizadas.')
    finalizar_atenciones.short_description = "Finalizar cronómetro"
    
    def cancelar_atenciones(self, request, queryset):
        count = 0
        for atencion in queryset:
            if atencion.cancelar_atencion("Cancelada desde admin"):
                count += 1
        self.message_user(request, f'{count} atenciones canceladas.')
    cancelar_atenciones.short_description = "Cancelar atenciones"