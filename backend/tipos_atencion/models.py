# backend/tipos_atencion/models.py - NUEVO APP PARA TIPOS DE ATENCIÓN
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class TipoAtencion(models.Model):
    """
    Modelo que define los tipos de atención médica con sus etapas específicas.
    Cada tipo de atención tiene su propio flujo clínico personalizado.
    """
    
    NIVEL_CHOICES = [
        ('PRIMARIA', 'Atención Primaria'),
        ('SECUNDARIA', 'Atención Secundaria'),
        ('TERCIARIA', 'Atención Terciaria'),
        ('CUATERNARIA', 'Atención Cuaternaria'),
    ]
    
    # Todas las etapas posibles del sistema
    ETAPAS_DISPONIBLES = [
        # Etapas Comunes
        ('ADMISION', 'Admisión/Recepción'),
        ('REGISTRO', 'Registro de Paciente'),
        ('TRIAJE', 'Triaje'),
        
        # Atención Primaria
        ('CONSULTA_GENERAL', 'Consulta Medicina General'),
        ('CONTROL_PREVENTIVO', 'Control Preventivo'),
        ('VACUNACION', 'Vacunación'),
        ('CONTROL_CRONICO', 'Control Enfermedad Crónica'),
        ('ATENCION_MATERNO_INFANTIL', 'Atención Materno-Infantil'),
        ('EDUCACION_SALUD', 'Educación en Salud'),
        
        # Atención Secundaria
        ('CONSULTA_ESPECIALISTA', 'Consulta con Especialista'),
        ('EXAMENES_DIAGNOSTICOS', 'Exámenes Diagnósticos'),
        ('PROCEDIMIENTOS_MENORES', 'Procedimientos Menores'),
        ('HOSPITALIZACION_BASICA', 'Hospitalización Básica'),
        ('CIRUGIA_MENOR', 'Cirugía Menor'),
        ('RECUPERACION_CORTA', 'Recuperación Corta'),
        
        # Atención Terciaria
        ('EVALUACION_ESPECIALIZADA', 'Evaluación Especializada'),
        ('ESTUDIOS_AVANZADOS', 'Estudios Avanzados'),
        ('JUNTA_MEDICA', 'Junta Médica'),
        ('HOSPITALIZACION_COMPLEJA', 'Hospitalización Compleja'),
        ('CIRUGIA_MAYOR', 'Cirugía Mayor'),
        ('UCI', 'Unidad de Cuidados Intensivos'),
        ('RECUPERACION_PROLONGADA', 'Recuperación Prolongada'),
        ('REHABILITACION', 'Rehabilitación'),
        
        # Atención Cuaternaria
        ('EVALUACION_MULTIDISCIPLINARIA', 'Evaluación Multidisciplinaria'),
        ('PROTOCOLO_INVESTIGACION', 'Protocolo de Investigación'),
        ('PREPARACION_ESPECIALIZADA', 'Preparación Especializada'),
        ('PROCEDIMIENTO_ALTA_COMPLEJIDAD', 'Procedimiento Alta Complejidad'),
        ('TRASPLANTE', 'Trasplante de Órganos'),
        ('TERAPIA_AVANZADA', 'Terapia Avanzada'),
        ('UCI_ESPECIALIZADA', 'UCI Especializada'),
        ('SEGUIMIENTO_LARGO_PLAZO', 'Seguimiento Largo Plazo'),
        
        # Etapas Finales Comunes
        ('ALTA_MEDICA', 'Alta Médica'),
        ('DERIVACION', 'Derivación a Otro Nivel'),
        ('SEGUIMIENTO', 'Seguimiento Posterior'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identificación
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Código único del tipo de atención (ej: PRIM-001)"
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo del tipo de atención"
    )
    nivel = models.CharField(
        max_length=20,
        choices=NIVEL_CHOICES,
        db_index=True,
        help_text="Nivel de complejidad de la atención"
    )
    
    # Descripción y características
    descripcion = models.TextField(
        help_text="Descripción detallada del tipo de atención y sus alcances"
    )
    
    # Etapas específicas de este tipo de atención
    etapas_flujo = models.JSONField(
        default=list,
        help_text="Lista ordenada de etapas que componen este flujo de atención"
    )
    
    # Duraciones estimadas por etapa (en minutos)
    duraciones_estimadas = models.JSONField(
        default=dict,
        help_text="Duración estimada en minutos para cada etapa"
    )
    
    # Requisitos y recursos
    requiere_especialista = models.BooleanField(
        default=False,
        help_text="Indica si requiere atención por especialista"
    )
    requiere_hospitalizacion = models.BooleanField(
        default=False,
        help_text="Indica si puede requerir hospitalización"
    )
    nivel_complejidad = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        help_text="Nivel de complejidad del 1 (simple) al 5 (máxima complejidad)"
    )
    
    # Control de costos estimados
    costo_estimado_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo estimado base de este tipo de atención"
    )
    
    # Estado y gestión
    activo = models.BooleanField(
        default=True,
        help_text="Indica si este tipo de atención está disponible"
    )
    
    # Prioridad automática
    prioridad_default = models.CharField(
        max_length=10,
        choices=[
            ('BAJA', 'Baja'),
            ('MEDIA', 'Media'),
            ('ALTA', 'Alta'),
            ('CRITICA', 'Crítica'),
        ],
        default='MEDIA',
        help_text="Prioridad por defecto para este tipo de atención"
    )
    
    # Metadatos
    metadatos = models.JSONField(
        default=dict,
        blank=True,
        help_text="Información adicional específica del tipo de atención"
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tipos_atencion'
        verbose_name = 'Tipo de Atención'
        verbose_name_plural = 'Tipos de Atención'
        ordering = ['nivel_complejidad', 'nombre']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['nivel']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.get_nivel_display()} - {self.nombre}"
    
    def obtener_etapas_con_duraciones(self):
        """
        Retorna las etapas con sus duraciones estimadas.
        """
        resultado = []
        for etapa_key in self.etapas_flujo:
            etapa_label = dict(self.ETAPAS_DISPONIBLES).get(etapa_key, etapa_key)
            duracion = self.duraciones_estimadas.get(etapa_key, 30)
            
            resultado.append({
                'key': etapa_key,
                'label': etapa_label,
                'duracion_estimada': duracion,
            })
        
        return resultado
    
    def calcular_duracion_total_estimada(self):
        """
        Calcula la duración total estimada del flujo completo.
        """
        total_minutos = sum(
            self.duraciones_estimadas.get(etapa, 30)
            for etapa in self.etapas_flujo
        )
        
        horas = total_minutos // 60
        minutos = total_minutos % 60
        
        return {
            'total_minutos': total_minutos,
            'horas': horas,
            'minutos': minutos,
            'formateado': f"{horas}h {minutos}m"
        }
    
    def es_compatible_con_urgencia(self, nivel_urgencia):
        """
        Verifica si este tipo de atención es compatible con el nivel de urgencia.
        """
        compatibilidad = {
            'PRIMARIA': ['BAJA', 'MEDIA'],
            'SECUNDARIA': ['MEDIA', 'ALTA'],
            'TERCIARIA': ['ALTA', 'CRITICA'],
            'CUATERNARIA': ['CRITICA'],
        }
        
        niveles_compatibles = compatibilidad.get(self.nivel, [])
        return nivel_urgencia in niveles_compatibles
    
    @classmethod
    def obtener_tipo_sugerido(cls, nivel_urgencia, especialista_requerido=False):
        """
        Sugiere un tipo de atención basado en la urgencia y requerimientos.
        """
        tipos = cls.objects.filter(activo=True)
        
        # Filtrar por urgencia
        if nivel_urgencia in ['CRITICA']:
            tipos = tipos.filter(nivel__in=['TERCIARIA', 'CUATERNARIA'])
        elif nivel_urgencia == 'ALTA':
            tipos = tipos.filter(nivel__in=['SECUNDARIA', 'TERCIARIA'])
        elif nivel_urgencia == 'MEDIA':
            tipos = tipos.filter(nivel__in=['PRIMARIA', 'SECUNDARIA'])
        else:  # BAJA
            tipos = tipos.filter(nivel='PRIMARIA')
        
        # Filtrar por requerimiento de especialista
        if especialista_requerido:
            tipos = tipos.filter(requiere_especialista=True)
        
        return tipos.first()


class PlantillaFlujo(models.Model):
    """
    Plantillas predefinidas de flujos clínicos para facilitar la configuración.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    nivel_atencion = models.CharField(max_length=20, choices=TipoAtencion.NIVEL_CHOICES)
    
    # Etapas y configuración
    etapas = models.JSONField(default=list)
    duraciones = models.JSONField(default=dict)
    
    # Flags
    es_plantilla_base = models.BooleanField(
        default=False,
        help_text="Indica si es una plantilla base del sistema"
    )
    
    activo = models.BooleanField(default=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'plantillas_flujo'
        verbose_name = 'Plantilla de Flujo'
        verbose_name_plural = 'Plantillas de Flujo'
        ordering = ['nivel_atencion', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_nivel_atencion_display()})"
    
    def aplicar_a_tipo_atencion(self, tipo_atencion):
        """
        Aplica esta plantilla a un tipo de atención.
        """
        tipo_atencion.etapas_flujo = self.etapas
        tipo_atencion.duraciones_estimadas = self.duraciones
        tipo_atencion.save()
        
        return True
