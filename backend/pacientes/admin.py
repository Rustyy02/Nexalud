# backend/pacientes/admin.py - ACTUALIZADO CON ETAPA_ACTUAL
from django.contrib import admin
from django.utils.html import format_html
from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = [
        'rut_display',
        'nombre_completo_display',
        'edad',
        'genero',
        'seguro_medico_display',
        'estado_actual_badge',
        'etapa_actual_badge',  # ✅ NUEVO
        'nivel_urgencia_badge',
        'telefono_display',
        'activo_badge'
    ]
    
    list_filter = [
        'estado_actual',
        'etapa_actual',  # ✅ NUEVO
        'nivel_urgencia',
        'genero',
        'tipo_sangre',
        'seguro_medico',
        'direccion_region',
        'activo',
        'fecha_ingreso'
    ]
    
    search_fields = [
        'rut',
        'nombre',
        'apellido_paterno',
        'apellido_materno',
        'correo',
        'telefono',
        'identificador_hash'
    ]
    
    readonly_fields = [
        'id',
        'identificador_hash',
        'edad',
        'fecha_ingreso',
        'fecha_actualizacion',
        'imc_display',
        'categoria_imc_display',
        'direccion_completa_display',
        'informacion_completa_display',
        'etapa_actual',  # ✅ NUEVO - Solo lectura porque se sincroniza automáticamente
    ]
    
    fieldsets = (
        ('🆔 Identificación', {
            'fields': (
                'id',
                'rut',
                'identificador_hash',
            )
        }),
        ('👤 Datos Personales', {
            'fields': (
                'nombre',
                'apellido_paterno',
                'apellido_materno',
                'fecha_nacimiento',
                'edad',
                'genero',
            )
        }),
        ('📞 Datos de Contacto', {
            'fields': (
                'correo',
                'telefono',
                'telefono_emergencia',
                'nombre_contacto_emergencia',
            )
        }),
        ('🏠 Dirección', {
            'fields': (
                'direccion_calle',
                'direccion_comuna',
                'direccion_ciudad',
                'direccion_region',
                'direccion_codigo_postal',
                'direccion_completa_display',
            )
        }),
        ('🏥 Seguro Médico y Previsión', {
            'fields': (
                'seguro_medico',
                'numero_beneficiario',
            )
        }),
        ('🩺 Información Médica Básica', {
            'fields': (
                'tipo_sangre',
                'peso',
                'altura',
                'imc_display',
                'categoria_imc_display',
            )
        }),
        ('⚕️ Información Médica Relevante', {
            'fields': (
                'alergias',
                'condiciones_preexistentes',
                'medicamentos_actuales',
            )
        }),
        ('📊 Estado Clínico', {
            'fields': (
                'estado_actual',
                'etapa_actual',  # ✅ NUEVO (readonly)
                'nivel_urgencia',
                'activo'
            ),
            'description': '⚠️ NOTA: etapa_actual se sincroniza automáticamente desde la Ruta Clínica'
        }),
        ('📝 Metadatos Adicionales', {
            'fields': ('metadatos_adicionales',),
            'classes': ('collapse',)
        }),
        ('📄 Información Completa', {
            'fields': ('informacion_completa_display',),
            'classes': ('collapse',)
        }),
        ('🕐 Timestamps', {
            'fields': ('fecha_ingreso', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    # ============================================
    # MÉTODOS DISPLAY
    # ============================================
    
    def rut_display(self, obj):
        """Muestra el RUT formateado"""
        return format_html(
            '<strong style="font-family: monospace;">{}</strong>',
            obj.rut
        )
    rut_display.short_description = "RUT"
    
    def nombre_completo_display(self, obj):
        """Muestra el nombre completo"""
        return format_html(
            '<strong>{}</strong>',
            obj.nombre_completo
        )
    nombre_completo_display.short_description = "Nombre Completo"
    
    def seguro_medico_display(self, obj):
        """Muestra el seguro médico con color"""
        colors = {
            'FONASA_A': '#4CAF50',
            'FONASA_B': '#4CAF50',
            'FONASA_C': '#FF9800',
            'FONASA_D': '#FF9800',
            'PARTICULAR': '#9E9E9E',
        }
        
        color = colors.get(obj.seguro_medico, '#2196F3')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_seguro_medico_display()
        )
    seguro_medico_display.short_description = "Seguro Médico"
    
    def telefono_display(self, obj):
        """Muestra el teléfono formateado"""
        return format_html(
            '<span style="font-family: monospace;">{}</span>',
            obj.telefono
        )
    telefono_display.short_description = "Teléfono"
    
    def estado_actual_badge(self, obj):
        """Badge con color según estado"""
        colors = {
            'EN_ESPERA': 'orange',
            'ACTIVO': 'blue',
            'PROCESO_PAUSADO': 'gray',
            'ALTA_COMPLETA': 'green',
            'ALTA_MEDICA': 'green',
            'PROCESO_INCOMPLETO': 'red',
            'INACTIVO': 'gray',
        }
        color = colors.get(obj.estado_actual, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_actual_display()
        )
    estado_actual_badge.short_description = "Estado Sistema"
    
    # ✅ NUEVO MÉTODO
    def etapa_actual_badge(self, obj):
        """Badge con color según etapa del flujo clínico"""
        if not obj.etapa_actual:
            return format_html(
                '<span style="color: gray; font-style: italic;">Sin etapa asignada</span>'
            )
        
        colors = {
            'CONSULTA_MEDICA': '#2196F3',
            'PROCESO_EXAMEN': '#9C27B0',
            'REVISION_EXAMEN': '#673AB7',
            'HOSPITALIZACION': '#FF9800',
            'OPERACION': '#F44336',
            'ALTA': '#4CAF50',
        }
        color = colors.get(obj.etapa_actual, '#607D8B')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">📋 {}</span>',
            color,
            obj.get_etapa_actual_display()
        )
    etapa_actual_badge.short_description = "Etapa Actual"
    
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
            return format_html('<strong>{}</strong>', imc)
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
    
    def direccion_completa_display(self, obj):
        """Muestra la dirección completa formateada"""
        return format_html(
            '<div style="font-family: sans-serif;">'
            '<strong>📍 Dirección Completa:</strong><br>'
            '{}'
            '</div>',
            obj.direccion_completa
        )
    direccion_completa_display.short_description = "Dirección Completa"
    
    def informacion_completa_display(self, obj):
        """Muestra toda la información en formato HTML"""
        info = obj.obtener_informacion_completa()
        
        html = '<div style="font-family: monospace; background: #f5f5f5; padding: 15px; border-radius: 5px;">'
        html += '<h3 style="margin-top: 0;">📋 Información Completa del Paciente</h3>'
        
        # Identificación
        html += '<h4 style="color: #1976D2; margin-bottom: 10px;">🆔 Identificación</h4>'
        html += '<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">'
        html += f'<tr><td style="padding: 8px; font-weight: bold; width: 30%;">RUT:</td><td style="padding: 8px;">{info["rut"]}</td></tr>'
        html += f'<tr><td style="padding: 8px; font-weight: bold;">Hash ID:</td><td style="padding: 8px;">{info["identificador_hash"]}</td></tr>'
        html += '</table>'
        
        # Estado Actual
        html += '<h4 style="color: #1976D2; margin-bottom: 10px;">📊 Estado Actual</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += f'<tr><td style="padding: 8px; font-weight: bold; width: 30%;">Estado Sistema:</td><td style="padding: 8px;">{info["estado_actual"]}</td></tr>'
        html += f'<tr><td style="padding: 8px; font-weight: bold;">Etapa Actual:</td><td style="padding: 8px; color: #2196F3; font-weight: bold;">{info["etapa_actual"]}</td></tr>'
        html += f'<tr><td style="padding: 8px; font-weight: bold;">Nivel Urgencia:</td><td style="padding: 8px;">{info["nivel_urgencia"]}</td></tr>'
        html += f'<tr><td style="padding: 8px; font-weight: bold;">En Proceso Clínico:</td><td style="padding: 8px;">{"✅ Sí" if info["esta_en_proceso_clinico"] else "❌ No"}</td></tr>'
        html += f'<tr><td style="padding: 8px; font-weight: bold;">Fecha Ingreso:</td><td style="padding: 8px;">{info["fecha_ingreso"]}</td></tr>'
        html += '</table>'
        
        # (resto del HTML se mantiene igual...)
        
        html += '</div>'
        
        return format_html(html)
    informacion_completa_display.short_description = "Información Completa"
    
    # ============================================
    # ACCIONES PERSONALIZADAS
    # ============================================
    
    actions = [
        'marcar_alta_completa',
        'marcar_en_espera',
        'pausar_procesos',
        'calcular_imc_pacientes',
        'validar_ruts'
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
    
    def validar_ruts(self, request, queryset):
        """Valida los RUTs de los pacientes seleccionados"""
        validos = 0
        invalidos = 0
        
        for paciente in queryset:
            if Paciente.validar_rut(paciente.rut):
                validos += 1
            else:
                invalidos += 1
        
        self.message_user(
            request,
            f'RUTs válidos: {validos} | RUTs inválidos: {invalidos}'
        )
    validar_ruts.short_description = "Validar RUTs"