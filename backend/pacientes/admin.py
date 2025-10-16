# backend/pacientes/admin.py - ACTUALIZADO CON NUEVOS CAMPOS
from django.contrib import admin
from django.utils.html import format_html
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = [
        'identificador_hash_corto',
        'nombre_display',
        'edad',
        'genero',
        'tipo_sangre',
        'estado_actual_badge',
        'nivel_urgencia_badge',
        'fecha_ingreso',
        'activo_badge'
    ]
    
    list_filter = [
        'estado_actual',
        'nivel_urgencia',
        'genero',
        'tipo_sangre',
        'activo',
        'fecha_ingreso'
    ]
    
    search_fields = [
        'identificador_hash',
        'metadatos_adicionales__nombre',
        'metadatos_adicionales__rut_original'
    ]
    
    readonly_fields = [
        'fecha_ingreso',
        'fecha_actualizacion',
        'imc_display',
        'categoria_imc_display',
        'informacion_medica_completa'
    ]
    
    fieldsets = (
        ('Información del Paciente', {
            'fields': (
                'identificador_hash',
                'edad',
                'genero'
            )
        }),
        ('Datos Médicos Básicos', {
            'fields': (
                'tipo_sangre',
                'peso',
                'altura',
                'imc_display',
                'categoria_imc_display',
            )
        }),
        ('Información Médica Relevante', {
            'fields': (
                'alergias',
                'condiciones_preexistentes',
                'medicamentos_actuales',
            )
        }),
        ('Estado Clínico', {
            'fields': (
                'estado_actual',
                'nivel_urgencia',
                'activo'
            )
        }),
        ('Metadatos Adicionales', {
            'fields': ('metadatos_adicionales',),
            'classes': ('collapse',)
        }),
        ('Información Completa', {
            'fields': ('informacion_medica_completa',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('fecha_ingreso', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def identificador_hash_corto(self, obj):
        """Muestra hash corto"""
        return f"{obj.identificador_hash[:8]}..."
    identificador_hash_corto.short_description = "ID Hash"
    
    def nombre_display(self, obj):
        """Muestra el nombre del paciente si existe"""
        return obj.obtener_nombre_display()
    nombre_display.short_description = "Nombre"
    
    def estado_actual_badge(self, obj):
        """Badge con color según estado"""
        colors = {
            'EN_ESPERA': 'orange',
            'EN_CONSULTA': 'blue',
            'EN_EXAMEN': 'purple',
            'PROCESO_PAUSADO': 'gray',
            'ALTA_COMPLETA': 'green',
            'PROCESO_INCOMPLETO': 'red',
        }
        color = colors.get(obj.estado_actual, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_actual_display()
        )
    estado_actual_badge.short_description = "Estado"
    
    def nivel_urgencia_badge(self, obj):
        """Badge con color según urgencia"""
        colors = {
            'BAJA': 'green',
            'MEDIA': 'blue',
            'ALTA': 'orange',
            'CRITICA': 'red',
        }
        color = colors.get(obj.nivel_urgencia, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_nivel_urgencia_display()
        )
    nivel_urgencia_badge.short_description = "Urgencia"
    
    def activo_badge(self, obj):
        """Badge activo/inactivo"""
        if obj.activo:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Inactivo</span>'
        )
    activo_badge.short_description = "Estado"
    
    def imc_display(self, obj):
        """Muestra el IMC calculado"""
        imc = obj.calcular_imc()
        if imc:
            return format_html(
                '<strong>{}</strong>',
                imc
            )
        return "No disponible"
    imc_display.short_description = "IMC"
    
    def categoria_imc_display(self, obj):
        """Muestra la categoría del IMC con color"""
        categoria = obj.obtener_categoria_imc()
        
        colors = {
            'Bajo peso': 'orange',
            'Peso normal': 'green',
            'Sobrepeso': 'orange',
            'Obesidad': 'red',
            'No disponible': 'gray'
        }
        
        color = colors.get(categoria, 'black')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            categoria
        )
    categoria_imc_display.short_description = "Categoría IMC"
    
    def informacion_medica_completa(self, obj):
        """Muestra toda la información médica formateada"""
        info = obj.obtener_informacion_medica_completa()
        
        html = '<div style="font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 5px;">'
        html += '<h3 style="margin-top: 0;">Información Médica Completa</h3>'
        
        html += '<table style="width: 100%; border-collapse: collapse;">'
        
        campos = [
            ('Identificador', info['identificador']),
            ('Nombre', info['nombre']),
            ('Edad', f"{info['edad']} años"),
            ('Género', info['genero']),
            ('Tipo de Sangre', info['tipo_sangre']),
            ('Peso', f"{info['peso']} kg" if info['peso'] else 'No registrado'),
            ('Altura', f"{info['altura']} cm" if info['altura'] else 'No registrado'),
            ('IMC', info['imc'] if info['imc'] else 'No disponible'),
            ('Categoría IMC', info['categoria_imc']),
            ('Estado Actual', info['estado_actual']),
            ('Nivel Urgencia', info['nivel_urgencia']),
        ]
        
        for label, valor in campos:
            html += f'<tr style="border-bottom: 1px solid #ddd;">'
            html += f'<td style="padding: 8px; font-weight: bold; width: 40%;">{label}:</td>'
            html += f'<td style="padding: 8px;">{valor}</td>'
            html += '</tr>'
        
        html += '</table>'
        
        # Sección de información médica crítica
        html += '<h4 style="margin-top: 20px; margin-bottom: 10px;">Información Crítica</h4>'
        
        if obj.tiene_alergias():
            html += f'<div style="background: #fff3cd; padding: 10px; margin-bottom: 10px; border-radius: 3px;">'
            html += f'<strong>⚠️ Alergias:</strong> {info["alergias"]}'
            html += '</div>'
        
        if obj.tiene_condiciones_preexistentes():
            html += f'<div style="background: #d1ecf1; padding: 10px; margin-bottom: 10px; border-radius: 3px;">'
            html += f'<strong>📋 Condiciones Preexistentes:</strong> {info["condiciones_preexistentes"]}'
            html += '</div>'
        
        if info['medicamentos'] != 'Sin medicamentos registrados':
            html += f'<div style="background: #d4edda; padding: 10px; margin-bottom: 10px; border-radius: 3px;">'
            html += f'<strong>💊 Medicamentos:</strong> {info["medicamentos"]}'
            html += '</div>'
        
        html += '</div>'
        
        return format_html(html)
    informacion_medica_completa.short_description = "Información Médica Completa"
    
    # Acciones personalizadas
    actions = [
        'marcar_alta_completa',
        'marcar_en_espera',
        'pausar_procesos',
        'calcular_imc_pacientes'
    ]
    
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
    
    def calcular_imc_pacientes(self, request, queryset):
        """Muestra el IMC de los pacientes seleccionados"""
        count = 0
        for paciente in queryset:
            imc = paciente.calcular_imc()
            if imc:
                count += 1
        
        self.message_user(
            request,
            f'{count} de {queryset.count()} pacientes tienen IMC calculable.'
        )
    calcular_imc_pacientes.short_description = "Calcular IMC"