import uuid
from django.db import models
from django.utils import timezone

class Paciente(models.Model):
    """
    Modelo para gestionar pacientes en el sistema Nexalud.
    Usa hash del identificador para proteger privacidad.
    """
    
    ESTADO_CHOICES = [
        ('EN_ESPERA', 'En Espera'),
        ('EN_CONSULTA', 'En Consulta'),
        ('EN_EXAMEN', 'En Exámen'),
        ('PROCESO_PAUSADO', 'Proceso Pausado'),
        ('ALTA_COMPLETA', 'Alta Completa'),
        ('PROCESO_INCOMPLETO', 'Proceso Incompleto'),
    ]
    
    URGENCIA_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('NE', 'No Especifica'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identificador_hash = models.CharField(
        max_length=64, 
        unique=True, 
        help_text="Hash del RUT/identificador para proteger privacidad"
    )
    edad = models.PositiveIntegerField(
        help_text="Edad del paciente en años"
    )
    genero = models.CharField(
        max_length=2, 
        choices=GENERO_CHOICES,
        default='NE'
    )
    fecha_ingreso = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de ingreso al sistema"
    )
    estado_actual = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES,
        default='EN_ESPERA'
    )
    nivel_urgencia = models.CharField(
        max_length=10, 
        choices=URGENCIA_CHOICES,
        default='MEDIA'
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    # Metadatos adicionales para flexibilidad
    metadatos_adicionales = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Información adicional en formato JSON"
    )
    
    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['identificador_hash']),
            models.Index(fields=['estado_actual']),
            models.Index(fields=['fecha_ingreso']),
        ]
    
    def __str__(self):
        return f"Paciente {self.identificador_hash[:8]}... - {self.get_estado_actual_display()}"
    
    def obtener_estado_actual(self):
        """Retorna el estado actual del paciente"""
        return self.estado_actual
    
    def actualizar_estado(self, nuevo_estado):
        """Actualiza el estado del paciente con validación"""
        if nuevo_estado in dict(self.ESTADO_CHOICES):
            self.estado_actual = nuevo_estado
            self.save()
            return True
        return False
    
    def calcular_tiempo_total(self):
        """Calcula el tiempo total desde el ingreso hasta ahora"""
        if self.fecha_ingreso:
            return timezone.now() - self.fecha_ingreso
        return None
    
    def is_proceso_completo(self):
        """Verifica si el proceso del paciente está completo"""
        return self.estado_actual == 'ALTA_COMPLETA'
    
    def is_proceso_pausado(self):
        """Verifica si el proceso está pausado (para nodo estático)"""
        return self.estado_actual == 'PROCESO_PAUSADO'
