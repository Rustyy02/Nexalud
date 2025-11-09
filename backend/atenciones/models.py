import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.conf import settings
from pacientes.models import Paciente
from boxes.models import Box

class Medico(models.Model):
    
    # Modelo para gestionar médicos y prestadores de salud.
    # NOTA: Este modelo se mantiene para compatibilidad con datos históricos.
    # Las nuevas atenciones usan directamente el modelo User con rol MEDICO.
    
    ESPECIALIDAD_CHOICES = [
        ('MEDICINA_GENERAL', 'Medicina General'),
        ('MEDICINA_INTERNA', 'Medicina Interna'),
        ('CARDIOLOGIA', 'Cardiología'),
        ('NEUROLOGIA', 'Neurología'),
        ('PEDIATRIA', 'Pediatría'),
        ('GINECOLOGIA', 'Ginecología y Obstetricia'),
        ('TRAUMATOLOGIA', 'Traumatología y Ortopedia'),
        ('OFTALMOLOGIA', 'Oftalmología'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('PSIQUIATRIA', 'Psiquiatría'),
        ('RADIOLOGIA', 'Radiología'),
        ('ANESTESIOLOGIA', 'Anestesiología'),
        ('CIRUGIA_GENERAL', 'Cirugía General'),
        ('UROLOGIA', 'Urología'),
        ('OTORRINOLARINGOLOGIA', 'Otorrinolaringología'),
        ('ENFERMERIA', 'Enfermería'),
        ('KINESIOLOGO', 'Kinesiología'),
        ('PSICOLOGO', 'Psicología'),
        ('NUTRICIONISTA', 'Nutrición'),
        ('TECNICO_ENFERMERIA', 'Técnico en Enfermería'),
        ('TECNICO_RADIOLOGIA', 'Técnico en Radiología'),
        ('OTRO', 'Otra Especialidad'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_medico = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Código único del médico en el sistema hospitalario"
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    especialidad_principal = models.CharField(
        max_length=30, 
        choices=ESPECIALIDAD_CHOICES,
        default='MEDICINA_GENERAL'
    )
    
    especialidades_secundarias = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de especialidades secundarias"
    )
    
    horarios_atencion = models.JSONField(
        default=dict,
        blank=True,
        help_text="Horarios de atención por día de la semana"
    )
    
    activo = models.BooleanField(default=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    
    configuraciones_personales = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuraciones y preferencias personales del médico"
    )
    
    class Meta:
        db_table = 'medicos'
        verbose_name = 'Médico'
        verbose_name_plural = 'Médicos'
        ordering = ['apellido', 'nombre']
        indexes = [
            models.Index(fields=['codigo_medico']),
            models.Index(fields=['especialidad_principal']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"Dr. {self.nombre} {self.apellido} ({self.get_especialidad_principal_display()})"
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"
    
    def obtener_atenciones_dia(self, fecha=None):
        # Retorna las atenciones del médico para un día específico
        if fecha is None:
            fecha = timezone.now().date()
        
        return self.atenciones.filter(
            fecha_hora_inicio__date=fecha
        ).order_by('fecha_hora_inicio')
    
    def calcular_tiempo_promedio_atencion(self, dias=30):
        # Calcula el tiempo promedio de atención de los últimos N días
        desde = timezone.now() - timezone.timedelta(days=dias)
        
        atenciones = self.atenciones.filter(
            fecha_hora_inicio__gte=desde,
            estado='COMPLETADA',
            duracion_real__isnull=False
        )
        
        if atenciones.exists():
            promedio = atenciones.aggregate(
                promedio=models.Avg('duracion_real')
            )['promedio']
            return promedio or 0
        return 0
    
    def obtener_eficiencia(self):
        # Calcula métricas de eficiencia del médico
        atenciones_mes = self.obtener_atenciones_dia().count()
        tiempo_promedio = self.calcular_tiempo_promedio_atencion()
        
        return {
            'atenciones_mes': atenciones_mes,
            'tiempo_promedio': tiempo_promedio,
            'eficiencia_score': self._calcular_score_eficiencia()
        }
    
    def _calcular_score_eficiencia(self):
        # Cálculo interno del score de eficiencia
        tiempo_promedio = self.calcular_tiempo_promedio_atencion()
        if tiempo_promedio > 0:
            return min(100, (30 / tiempo_promedio) * 100)
        return 0


class Atencion(models.Model):
    
    # Modelo para gestionar las atenciones médicas.
    # Incluye cronómetro para medir tiempos reales.
    
    ESTADO_CHOICES = [
        ('PROGRAMADA', 'Programada'),
        ('EN_ESPERA', 'En Espera'),
        ('EN_CURSO', 'En Curso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
        ('NO_PRESENTADO', 'No se Presentó'),
    ]
    
    TIPO_ATENCION_CHOICES = [
        ('CONSULTA_GENERAL', 'Consulta General'),
        ('CONSULTA_ESPECIALIDAD', 'Consulta de Especialidad'),
        ('CONTROL', 'Control'),
        ('PROCEDIMIENTO', 'Procedimiento'),
        ('EXAMEN', 'Examen'),
        ('CIRUGIA_MENOR', 'Cirugía Menor'),
        ('URGENCIA', 'Atención de Urgencia'),
        ('TELEMEDICINA', 'Telemedicina'),
        ('INTERCONSULTA', 'Interconsulta'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relaciones principales
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE,
        related_name='atenciones'
    )
    
    # User con rol de medico
    medico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='atenciones_medico',
        limit_choices_to={'rol': 'MEDICO'},
        help_text="Usuario con rol de médico asignado a esta atención"
    )
    
    box = models.ForeignKey(
        Box, 
        on_delete=models.CASCADE,
        related_name='atenciones'
    )
    
    # Campos de tiempo
    fecha_hora_inicio = models.DateTimeField(
        help_text="Fecha y hora programada de inicio"
    )
    fecha_hora_fin = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha y hora programada de fin"
    )
    
    # Cronómetro - tiempos reales
    inicio_cronometro = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Momento real de inicio de la atención"
    )
    fin_cronometro = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Momento real de fin de la atención"
    )
    
    # Duraciones
    duracion_planificada = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Duración planificada en minutos"
    )
    duracion_real = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Duración real en minutos"
    )
    
    # Clasificación
    tipo_atencion = models.CharField(
        max_length=25, 
        choices=TIPO_ATENCION_CHOICES,
        default='CONSULTA_GENERAL'
    )
    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_CHOICES,
        default='PROGRAMADA'
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones adicionales sobre la atención"
    )
    
    # Control de atrasos
    atraso_reportado = models.BooleanField(
        default=False,
        help_text="Indica si el médico reportó un atraso del paciente"
    )
    fecha_reporte_atraso = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que se reportó el atraso"
    )
    motivo_atraso = models.TextField(
        blank=True,
        help_text="Motivo del atraso reportado por el médico"
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'atenciones'
        verbose_name = 'Atención'
        verbose_name_plural = 'Atenciones'
        ordering = ['-fecha_hora_inicio']
        indexes = [
            models.Index(fields=['paciente']),
            models.Index(fields=['medico']),
            models.Index(fields=['box']),
            models.Index(fields=['fecha_hora_inicio']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_atencion']),
        ]
    
    def __str__(self):
        medico_nombre = self.medico.get_full_name() or self.medico.username
        return f"{self.tipo_atencion} - {self.paciente} con {medico_nombre} ({self.estado})"
    
    # ========================================
    # FUNCIONES DE CRONÓMETRO - NO MODIFICAR
    # ========================================
    
    def iniciar_cronometro(self):
        
        # Inicia el cronómetro de la atención.
        # También marca el box como ocupado.
        
        if self.estado in ['PROGRAMADA', 'EN_ESPERA']:
            self.inicio_cronometro = timezone.now()
            self.estado = 'EN_CURSO'
            
            # Ocupar el box
            self.box.ocupar(self.inicio_cronometro)
            
            self.save()
            return True
        return False

    def finalizar_cronometro(self):
        
        # Finaliza el cronómetro y calcula la duración real.
        # También libera el box.
        
        if self.estado == 'EN_CURSO' and self.inicio_cronometro:
            self.fin_cronometro = timezone.now()
            self.estado = 'COMPLETADA'
            
            # Calcular duración real
            duracion = self.fin_cronometro - self.inicio_cronometro
            self.duracion_real = int(duracion.total_seconds() / 60)
            
            # Liberar el box
            self.box.liberar(self.fin_cronometro)
            
            self.save()
            return True
        return False
    
    def calcular_retraso(self):
        
        # Calcula el retraso en minutos respecto a la hora programada.
        
        if self.inicio_cronometro:
            retraso = self.inicio_cronometro - self.fecha_hora_inicio
            return max(0, int(retraso.total_seconds() / 60))
        return 0
    
    def calcular_diferencia_duracion(self):
        
        # Calcula la diferencia entre duración planificada y real.
        
        if self.duracion_real:
            return self.duracion_real - self.duracion_planificada
        return 0
    
    def obtener_tiempo_transcurrido(self):
        
        # Retorna el tiempo transcurrido desde el inicio (si está en curso).
        
        if self.estado == 'EN_CURSO' and self.inicio_cronometro:
            return timezone.now() - self.inicio_cronometro
        elif self.duracion_real:
            return timezone.timedelta(minutes=self.duracion_real)
        return None
    
    def generar_metricas(self):
        
        # Genera métricas de la atención para análisis.
        
        return {
            'id': str(self.id),
            'tipo': self.tipo_atencion,
            'duracion_planificada': self.duracion_planificada,
            'duracion_real': self.duracion_real,
            'retraso_inicio': self.calcular_retraso(),
            'diferencia_duracion': self.calcular_diferencia_duracion(),
            'fecha': self.fecha_hora_inicio.date(),
            'medico_id': str(self.medico.id),
            'box_id': str(self.box.id),
            'estado': self.estado,
            'completada_a_tiempo': self.duracion_real <= self.duracion_planificada if self.duracion_real else None
        }
    
    def is_retrasada(self):
        
        # Verifica si la atención está retrasada.
        
        if self.estado == 'EN_CURSO' and self.inicio_cronometro:
            tiempo_transcurrido = self.obtener_tiempo_transcurrido()
            if tiempo_transcurrido:
                return tiempo_transcurrido.total_seconds() / 60 > self.duracion_planificada
        return False
    
    def cancelar_atencion(self, motivo=""):
        
        # Cancela la atención y libera recursos.
        
        if self.estado not in ['COMPLETADA', 'CANCELADA']:
            self.estado = 'CANCELADA'
            self.observaciones += f"\nCancelada: {motivo}" if motivo else "\nCancelada"
            
            # Si estaba en curso, liberar el box
            if self.box.estado == 'OCUPADO':
                self.box.liberar()
            
            self.save()
            return True
        return False
    
    def reagendar(self, nueva_fecha, nuevo_box=None):
        
        # Reagenda la atención para una nueva fecha/hora.
        
        if self.estado in ['PROGRAMADA', 'EN_ESPERA']:
            self.fecha_hora_inicio = nueva_fecha
            if nuevo_box:
                self.box = nuevo_box
            
            self.observaciones += f"\nReagendada desde {self.fecha_hora_inicio}"
            self.save()
            return True
        return False
    
    # Estas son más funciones para médicos, no se utilizan todas.
    
    def reportar_atraso(self, motivo=""):
        
        # Reporta un atraso del paciente.
        # Inicia un timer de 5 minutos para que el paciente llegue.
        # Si no llega en 5 minutos, se marca automáticamente como NO_PRESENTADO.
        # Solo disponible cuando la atención ya está EN_CURSO.
        
        if self.estado == 'EN_CURSO' and not self.atraso_reportado:
            self.atraso_reportado = True
            self.fecha_reporte_atraso = timezone.now()
            self.motivo_atraso = motivo or "Paciente no presente a la hora programada"
            self.save()
            return True
        return False
    
    def verificar_tiempo_atraso(self):
        
        # Verifica si han pasado 5 minutos desde el reporte de atraso.
        # Retorna True si debe marcarse como NO_PRESENTADO.
        
        if self.atraso_reportado and self.fecha_reporte_atraso:
            ahora = timezone.now()
            tiempo_transcurrido = ahora - self.fecha_reporte_atraso
            minutos = tiempo_transcurrido.total_seconds() / 60
            return minutos >= 5
        return False
    
    def marcar_no_presentado(self):
        
        # Marca la atención como 'No se presentó' y libera el box.
        
        if self.estado in ['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO']:
            self.estado = 'NO_PRESENTADO'
            
            # Si el box está ocupado, liberarlo
            if self.box.estado == 'OCUPADO':
                self.box.liberar()
            
            self.save()
            return True
        return False
    
    def puede_iniciar(self):
        
        # Verifica si la atención puede ser iniciada por el médico.
        
        return self.estado in ['PROGRAMADA', 'EN_ESPERA']
    
    def puede_finalizar(self):
        
        # Verifica si la atención puede ser finalizada.
        
        return self.estado == 'EN_CURSO'
    
    def tiempo_hasta_inicio(self):
        
        # Calcula el tiempo restante hasta la hora programada.
        # Retorna None si ya pasó la hora o timedelta si falta tiempo.
        
        ahora = timezone.now()
        if ahora < self.fecha_hora_inicio:
            return self.fecha_hora_inicio - ahora
        return None