import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class Box(models.Model):
    """
    Modelo para gestionar los boxes de atención médica.
    Incluye seguimiento de disponibilidad y ocupación en tiempo real.
    """
    
    ESTADO_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('OCUPADO', 'Ocupado'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('FUERA_SERVICIO', 'Fuera de Servicio'),
    ]
    
    ESPECIALIDAD_CHOICES = [
        ('GENERAL', 'Medicina General'),
        ('CARDIOLOGIA', 'Cardiología'),
        ('NEUROLOGIA', 'Neurología'),
        ('PEDIATRIA', 'Pediatría'),
        ('GINECOLOGIA', 'Ginecología'),
        ('TRAUMATOLOGIA', 'Traumatología'),
        ('OFTALMOLOGIA', 'Oftalmología'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('PSIQUIATRIA', 'Psiquiatría'),
        ('RADIOLOGIA', 'Radiología'),
        ('LABORATORIO', 'Laboratorio'),
        ('PROCEDIMIENTOS', 'Procedimientos'),
        ('CIRUGIA_MENOR', 'Cirugía Menor'),
        ('MULTIUSO', 'Multiuso'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(
        max_length=10, 
        unique=True,
        help_text="Número identificador del box (ej: BOX-001, SALA-A)"
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo del box"
    )
    especialidad = models.CharField(
        max_length=20, 
        choices=ESPECIALIDAD_CHOICES,
        default='GENERAL'
    )
    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_CHOICES,
        default='DISPONIBLE'
    )
    capacidad_maxima = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Número máximo de personas que puede atender simultáneamente"
    )
    
    # Equipamiento disponible (JSON flexible)
    equipamiento = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de equipamiento disponible en el box"
    )
    
    # Horarios de disponibilidad
    horarios_disponibles = models.JSONField(
        default=dict,
        blank=True,
        help_text="Horarios de disponibilidad por día de la semana"
    )
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campos para métricas
    tiempo_ocupado_hoy = models.DurationField(
        default=timezone.timedelta,
        help_text="Tiempo total ocupado en el día actual"
    )
    ultima_ocupacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Última vez que el box fue ocupado"
    )
    ultima_liberacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Última vez que el box fue liberado"
    )
    
    class Meta:
        db_table = 'boxes'
        verbose_name = 'Box'
        verbose_name_plural = 'Boxes'
        ordering = ['numero']
        indexes = [
            models.Index(fields=['numero']),
            models.Index(fields=['estado']),
            models.Index(fields=['especialidad']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.nombre} ({self.get_estado_display()})"
    
    def ocupar(self, timestamp=None):
        """
        Marca el box como ocupado y registra el timestamp.
        """
        if self.estado == 'DISPONIBLE':
            self.estado = 'OCUPADO'
            self.ultima_ocupacion = timestamp or timezone.now()
            self.save()
            return True
        return False
    
    def liberar(self, timestamp=None):
        """
        Marca el box como disponible y calcula tiempo de ocupación.
        """
        if self.estado == 'OCUPADO':
            self.estado = 'DISPONIBLE'
            liberacion_time = timestamp or timezone.now()
            self.ultima_liberacion = liberacion_time
            
            # Calcular duración de la ocupación
            if self.ultima_ocupacion:
                duracion = liberacion_time - self.ultima_ocupacion
                self.tiempo_ocupado_hoy += duracion
            
            self.save()
            return True
        return False
    
    def obtener_disponibilidad(self):
        """
        Retorna True si el box está disponible para ser ocupado.
        """
        return self.estado == 'DISPONIBLE' and self.activo
    
    def calcular_tiempo_ocupacion_hoy(self):
        """
        Calcula el porcentaje de ocupación del día actual.
        """
        hoy = timezone.now().date()
        total_segundos_dia = 24 * 60 * 60  # Total segundos en un día
        
        if self.tiempo_ocupado_hoy:
            segundos_ocupado = self.tiempo_ocupado_hoy.total_seconds()
            porcentaje = (segundos_ocupado / total_segundos_dia) * 100
            return min(porcentaje, 100)  # Máximo 100%
        return 0
    
    def obtener_ocupacion_actual(self):
        """
        Retorna información sobre la ocupación actual del box.
        """
        if self.estado == 'OCUPADO' and self.ultima_ocupacion:
            tiempo_ocupado = timezone.now() - self.ultima_ocupacion
            return {
                'ocupado': True,
                'tiempo_ocupacion': tiempo_ocupado,
                'inicio_ocupacion': self.ultima_ocupacion
            }
        return {
            'ocupado': False,
            'tiempo_ocupacion': None,
            'inicio_ocupacion': None
        }
    
    def reset_tiempo_ocupado_diario(self):
        """
        Resetea el contador de tiempo ocupado diario. 
        Se ejecutaría automáticamente a medianoche.
        """
        self.tiempo_ocupado_hoy = timezone.timedelta()
        self.save()
        
    def is_disponible_para_especialidad(self, especialidad):
        """
        Verifica si el box puede ser usado para una especialidad específica.
        """
        return (self.especialidad == especialidad or 
                self.especialidad == 'MULTIUSO') and self.obtener_disponibilidad()


class OcupacionManual(models.Model):
    """
    Modelo para registrar ocupaciones manuales de boxes sin atención médica.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    box = models.ForeignKey(
        'Box',
        on_delete=models.CASCADE,
        related_name='ocupaciones_manuales'
    )
    duracion_minutos = models.PositiveIntegerField(
        help_text="Duración de la ocupación en minutos"
    )
    fecha_inicio = models.DateTimeField(
        default=timezone.now,
        help_text="Momento en que se ocupó el box"
    )
    fecha_fin_programada = models.DateTimeField(
        help_text="Momento programado para liberar el box"
    )
    fecha_fin_real = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento real en que se liberó el box"
    )
    motivo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Motivo de la ocupación manual"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Si la ocupación sigue activa"
    )

    class Meta:
        db_table = 'ocupaciones_manuales'
        verbose_name = 'Ocupación Manual'
        verbose_name_plural = 'Ocupaciones Manuales'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['box', 'activa']),
            models.Index(fields=['fecha_fin_programada']),
        ]
    
    def __str__(self):
        return f"Ocupación {self.box.numero} - {self.duracion_minutos} min"
    
    def finalizar(self):
        """Finaliza la ocupación manual y libera el box"""
        if self.activa:
            self.fecha_fin_real = timezone.now()
            self.activa = False
            self.box.liberar(self.fecha_fin_real)
            self.save()
            return True
        return False
    
    def debe_finalizar(self):
        """Verifica si la ocupación debe finalizar según la hora programada"""
        return timezone.now() >= self.fecha_fin_programada and self.activa