from django.contrib import admin
from .models import Box

@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nombre', 'especialidad', 'estado', 'activo', 'ultima_ocupacion']
    list_filter = ['estado', 'especialidad', 'activo']
    search_fields = ['numero', 'nombre']
    readonly_fields = ['tiempo_ocupado_hoy', 'ultima_ocupacion', 'ultima_liberacion', 'fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero', 'nombre', 'especialidad', 'capacidad_maxima')
        }),
        ('Estado y Disponibilidad', {
            'fields': ('estado', 'activo')
        }),
        ('Equipamiento', {
            'fields': ('equipamiento', 'horarios_disponibles'),
            'classes': ('collapse',)
        }),
        ('Métricas de Ocupación', {
            'fields': ('tiempo_ocupado_hoy', 'ultima_ocupacion', 'ultima_liberacion'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    actions = ['marcar_disponible', 'marcar_mantenimiento']
    
    def marcar_disponible(self, request, queryset):
        updated = queryset.update(estado='DISPONIBLE')
        self.message_user(request, f'{updated} boxes marcados como disponibles.')
    marcar_disponible.short_description = "Marcar como disponible"
    
    def marcar_mantenimiento(self, request, queryset):
        updated = queryset.update(estado='MANTENIMIENTO')
        self.message_user(request, f'{updated} boxes marcados en mantenimiento.')
    marcar_mantenimiento.short_description = "Marcar en mantenimiento"