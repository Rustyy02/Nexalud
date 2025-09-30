from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import IntegracionExterna, LogSincronizacion, ConfiguracionSistema


class LogSincronizacionInline(admin.TabularInline):
    model = LogSincronizacion
    extra = 0
    fields = ['timestamp', 'estado', 'mensaje', 'tiempo_respuesta_ms']
    readonly_fields = ['timestamp', 'estado', 'mensaje', 'tiempo_respuesta_ms']
    can_delete = False
    max_num = 10
    ordering = ['-timestamp']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(IntegracionExterna)
class IntegracionExternaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_sistema',
        'tipo_sistema',
        'estado_badge',
        'metodo_autenticacion',
        'ultima_sincronizacion_info',
        'activo_badge',
        'intervalo_sync'
    ]
    list_filter = [
        'tipo_sistema',
        'estado_conexion',
        'metodo_autenticacion',
        'activo'
    ]
    search_fields = [
        'nombre_sistema',
        'endpoint_base_url'
    ]
    readonly_fields = [
        'ultima_sincronizacion',
        'fecha_creacion',
        'fecha_actualizacion',
        'logs_recientes'
    ]
    inlines = [LogSincronizacionInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'nombre_sistema',
                'tipo_sistema',
                'estado_conexion',
                'activo',
            )
        }),
        ('Configuración de Conexión', {
            'fields': (
                'endpoint_base_url',
                'metodo_autenticacion',
                'token_acceso_encrypted',
            )
        }),
        ('Sincronización', {
            'fields': (
                'intervalo_sincronizacion',
                'ultima_sincronizacion',
                'configuracion_mapeo',
            )
        }),
        ('Responsable', {
            'fields': ('usuario_configuracion',),
            'classes': ('collapse',)
        }),
        ('Logs Recientes', {
            'fields': ('logs_recientes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        colors = {
            'ACTIVA': 'green',
            'INACTIVA': 'gray',
            'ERROR': 'red',
            'MANTENIMIENTO': 'orange',
            'CONFIGURACION': 'blue'
        }
        color = colors.get(obj.estado_conexion, 'black')
        icons = {
            'ACTIVA': '✓',
            'INACTIVA': '○',
            'ERROR': '✗',
            'MANTENIMIENTO': '⚙',
            'CONFIGURACION': '⚡'
        }
        icon = icons.get(obj.estado_conexion, '?')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_estado_conexion_display()
        )
    estado_badge.short_description = "Estado Conexión"
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>'
        )
    activo_badge.short_description = "Estado"
    
    def ultima_sincronizacion_info(self, obj):
        if obj.ultima_sincronizacion:
            delta = timezone.now() - obj.ultima_sincronizacion
            horas = int(delta.total_seconds() / 3600)
            minutos = int((delta.total_seconds() % 3600) / 60)
            
            if horas > 24:
                tiempo = f"hace {int(horas/24)} días"
                color = "red"
            elif horas > 1:
                tiempo = f"hace {horas}h {minutos}m"
                color = "orange"
            else:
                tiempo = f"hace {minutos}m"
                color = "green"
            
            return format_html(
                '<span style="color: {};">{}</span><br><small>{}</small>',
                color, tiempo, obj.ultima_sincronizacion.strftime('%d/%m/%Y %H:%M')
            )
        return format_html('<span style="color: red;">Nunca</span>')
    ultima_sincronizacion_info.short_description = "Última Sincronización"
    
    def intervalo_sync(self, obj):
        minutos = int(obj.intervalo_sincronizacion / 60)
        if minutos >= 60:
            horas = minutos / 60
            return f"{horas:.1f}h"
        return f"{minutos}m"
    intervalo_sync.short_description = "Intervalo"
    
    def logs_recientes(self, obj):
        logs = obj.logs_sincronizacion.all()[:10]
        if not logs:
            return "No hay logs disponibles"
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<tr style='background: #f5f5f5;'><th>Timestamp</th><th>Estado</th><th>Mensaje</th><th>Tiempo</th></tr>"
        
        for log in logs:
            color = {
                'EXITOSA': 'green',
                'ERROR': 'red',
                'ADVERTENCIA': 'orange',
                'WEBHOOK_PROCESADO': 'blue',
                'TIMEOUT': 'darkred',
                'DATOS_INVALIDOS': 'purple'
            }.get(log.estado, 'black')
            
            html += f"<tr style='border-bottom: 1px solid #ddd;'>"
            html += f"<td>{log.timestamp.strftime('%d/%m %H:%M')}</td>"
            html += f"<td><span style='color: {color}; font-weight: bold;'>{log.get_estado_display()}</span></td>"
            html += f"<td>{log.mensaje[:50]}...</td>"
            html += f"<td>{log.tiempo_respuesta_ms or '-'} ms</td>"
            html += "</tr>"
        
        html += "</table>"
        return format_html(html)
    logs_recientes.short_description = "Últimos 10 Logs"
    
    actions = [
        'sincronizar_ahora',
        'validar_conexion',
        'activar_integraciones',
        'desactivar_integraciones',
        'marcar_mantenimiento'
    ]
    
    def sincronizar_ahora(self, request, queryset):
        count_success = 0
        count_error = 0
        for integracion in queryset:
            if integracion.sincronizar_datos():
                count_success += 1
            else:
                count_error += 1
        
        self.message_user(
            request,
            f'{count_success} sincronizaciones exitosas, {count_error} con error.'
        )
    sincronizar_ahora.short_description = "Sincronizar ahora"
    
    def validar_conexion(self, request, queryset):
        count_ok = 0
        count_fail = 0
        for integracion in queryset:
            if integracion.validar_conexion():
                integracion.estado_conexion = 'ACTIVA'
                integracion.save()
                count_ok += 1
            else:
                integracion.estado_conexion = 'ERROR'
                integracion.save()
                count_fail += 1
        
        self.message_user(
            request,
            f'{count_ok} conexiones válidas, {count_fail} con error.'
        )
    validar_conexion.short_description = "Validar conexión"
    
    def activar_integraciones(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} integraciones activadas.')
    activar_integraciones.short_description = "Activar integraciones"
    
    def desactivar_integraciones(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} integraciones desactivadas.')
    desactivar_integraciones.short_description = "Desactivar integraciones"
    
    def marcar_mantenimiento(self, request, queryset):
        updated = queryset.update(estado_conexion='MANTENIMIENTO')
        self.message_user(request, f'{updated} integraciones en mantenimiento.')
    marcar_mantenimiento.short_description = "Marcar en mantenimiento"


@admin.register(LogSincronizacion)
class LogSincronizacionAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'integracion',
        'estado_badge',
        'mensaje_corto',
        'tiempo_respuesta_ms',
    ]
    list_filter = [
        'estado',
        'integracion__nombre_sistema',
        'timestamp'
    ]
    search_fields = [
        'mensaje',
        'integracion__nombre_sistema'
    ]
    readonly_fields = [
        'timestamp',
        'integracion',
        'estado',
        'mensaje',
        'datos_adicionales',
        'tiempo_respuesta_ms',
        'datos_formateados'
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Información del Log', {
            'fields': (
                'timestamp',
                'integracion',
                'estado',
                'tiempo_respuesta_ms',
            )
        }),
        ('Mensaje', {
            'fields': ('mensaje',)
        }),
        ('Datos Adicionales', {
            'fields': ('datos_formateados',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def estado_badge(self, obj):
        colors = {
            'EXITOSA': 'green',
            'ERROR': 'red',
            'ADVERTENCIA': 'orange',
            'WEBHOOK_PROCESADO': 'blue',
            'TIMEOUT': 'darkred',
            'DATOS_INVALIDOS': 'purple'
        }
        color = colors.get(obj.estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    estado_badge.short_description = "Estado"
    
    def mensaje_corto(self, obj):
        if len(obj.mensaje) > 80:
            return f"{obj.mensaje[:80]}..."
        return obj.mensaje
    mensaje_corto.short_description = "Mensaje"
    
    def datos_formateados(self, obj):
        if not obj.datos_adicionales:
            return "No hay datos adicionales"
        
        import json
        try:
            datos_json = json.dumps(obj.datos_adicionales, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px;">{}</pre>', datos_json)
        except:
            return str(obj.datos_adicionales)
    datos_formateados.short_description = "Datos Adicionales (JSON)"
    
    actions = ['exportar_logs']
    
    def exportar_logs(self, request, queryset):
        # Aquí podrías implementar la exportación a CSV/JSON
        self.message_user(
            request,
            f'{queryset.count()} logs seleccionados para exportar.'
        )
    exportar_logs.short_description = "Exportar logs seleccionados"


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = [
        'clave',
        'valor_corto',
        'tipo_dato',
        'activo_badge',
        'usuario_modificacion',
        'fecha_modificacion'
    ]
    list_filter = [
        'tipo_dato',
        'activo',
        'fecha_modificacion'
    ]
    search_fields = [
        'clave',
        'valor',
        'descripcion'
    ]
    readonly_fields = [
        'fecha_modificacion',
        'valor_tipado_display'
    ]
    
    fieldsets = (
        ('Configuración', {
            'fields': (
                'clave',
                'valor',
                'tipo_dato',
                'activo',
            )
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
        ('Valor Interpretado', {
            'fields': ('valor_tipado_display',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': (
                'usuario_modificacion',
                'fecha_modificacion',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def activo_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>'
        )
    activo_badge.short_description = "Estado"
    
    def valor_corto(self, obj):
        if len(obj.valor) > 50:
            return f"{obj.valor[:50]}..."
        return obj.valor
    valor_corto.short_description = "Valor"
    
    def valor_tipado_display(self, obj):
        try:
            valor_tipado = obj.obtener_valor_tipado()
            tipo_python = type(valor_tipado).__name__
            return format_html(
                '<strong>Tipo Python:</strong> {}<br>'
                '<strong>Valor:</strong> <pre>{}</pre>',
                tipo_python,
                str(valor_tipado)
            )
        except Exception as e:
            return format_html(
                '<span style="color: red;">Error al convertir: {}</span>',
                str(e)
            )
    valor_tipado_display.short_description = "Valor Tipado"
    
    def save_model(self, request, obj, form, change):
        if not change or not obj.usuario_modificacion:
            obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)
    
    actions = [
        'activar_configuraciones',
        'desactivar_configuraciones',
        'validar_valores'
    ]
    
    def activar_configuraciones(self, request, queryset):
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} configuraciones activadas.')
    activar_configuraciones.short_description = "Activar configuraciones"
    
    def desactivar_configuraciones(self, request, queryset):
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} configuraciones desactivadas.')
    desactivar_configuraciones.short_description = "Desactivar configuraciones"
    
    def validar_valores(self, request, queryset):
        count_ok = 0
        count_error = 0
        
        for config in queryset:
            try:
                config.obtener_valor_tipado()
                count_ok += 1
            except:
                count_error += 1
        
        self.message_user(
            request,
            f'{count_ok} configuraciones válidas, {count_error} con error de conversión.'
        )
    validar_valores.short_description = "Validar conversión de valores"