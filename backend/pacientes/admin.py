from django.contrib import admin
from .models import Paciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['identificador_hash_corto', 'edad', 'genero', 'estado_actual', 'nivel_urgencia', 'fecha_ingreso', 'activo']
    list_filter = ['estado_actual', 'nivel_urgencia', 'genero', 'activo']
    search_fields = ['identificador_hash']
    readonly_fields = ['fecha_ingreso', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': ('identificador_hash', 'edad', 'genero')
        }),
        ('Estado Clínico', {
            'fields': ('estado_actual', 'nivel_urgencia', 'activo')
        }),
        ('Metadatos', {
            'fields': ('metadatos_adicionales',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('fecha_ingreso', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def identificador_hash_corto(self, obj):
        return f"{obj.identificador_hash[:8]}..."
    identificador_hash_corto.short_description = "ID Hash"
    
    actions = ['marcar_alta_completa', 'marcar_en_espera', 'pausar_procesos']
    
    def marcar_alta_completa(self, request, queryset):
        updated = queryset.update(estado_actual='ALTA_COMPLETA')
        self.message_user(request, f'{updated} pacientes marcados con alta completa.')
    marcar_alta_completa.short_description = "Marcar alta completa"
    
    def marcar_en_espera(self, request, queryset):
        updated = queryset.update(estado_actual='EN_ESPERA')
        self.message_user(request, f'{updated} pacientes marcados en espera.')
    marcar_en_espera.short_description = "Marcar en espera"
    
    def pausar_procesos(self, request, queryset):
        updated = queryset.update(estado_actual='PROCESO_PAUSADO')
        self.message_user(request, f'{updated} procesos de pacientes pausados.')
    pausar_procesos.short_description = "Pausar procesos"