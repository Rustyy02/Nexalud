import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente

class RutaClinica(models.Model):
    """
    Modelo para gestionar las rutas clínicas de los pacientes.
    Representa el timeline completo del proceso de atención.
    """
    
    ESTADO_CHOICES = [
        ('INICIADA', 'Iniciada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('PAUSADA', 'Pausada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE,
        related_name='rutas_clinicas'
    )
    
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_estimada_fin = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha estimada de finalización del proceso"
    )
    fecha_fin_real = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha real de finalización del proceso"
    )
    
    porcentaje_completado = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Porcentaje de completitud del proceso (0-100)"
    )
    
    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_CHOICES,
        default='INICIADA'
    )
    
    # Metadatos adicionales para flexibilidad
    metadatos_adicionales = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Información adicional del proceso en formato JSON"
    )
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rutas_clinicas'
        verbose_name = 'Ruta Clínica'
        verbose_name_plural = 'Rutas Clínicas'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['paciente']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['porcentaje_completado']),
        ]
    
    def __str__(self):
        return f"Ruta {self.paciente} - {self.porcentaje_completado:.1f}%"
    
    def calcular_progreso(self):
        """
        Calcula el porcentaje de progreso basado en las etapas completadas.
        """
        etapas_totales = self.etapas.count()
        if etapas_totales == 0:
            return 0.0
        
        etapas_completadas = self.etapas.filter(estado='COMPLETADA').count()
        progreso = (etapas_completadas / etapas_totales) * 100
        
        # Actualizar el porcentaje en la base de datos
        self.porcentaje_completado = progreso
        self.save(update_fields=['porcentaje_completado'])
        
        return progreso
    
    def obtener_proxima_etapa(self):
        """
        Retorna la próxima etapa a ejecutar en la ruta.
        """
        return self.etapas.filter(
            estado__in=['PENDIENTE', 'EN_PROCESO']
        ).order_by('orden').first()
    
    def obtener_etapa_actual(self):
        """
        Retorna la etapa que está actualmente en proceso.
        """
        return self.etapas.filter(estado='EN_PROCESO').first()
    
    def marcar_etapa_completada(self, etapa_id):
        """
        Marca una etapa específica como completada y recalcula el progreso.
        """
        try:
            etapa = self.etapas.get(id=etapa_id)
            etapa.finalizar_etapa()
            self.calcular_progreso()
            
            # Si todas las etapas están completadas, marcar ruta como completada
            if self.porcentaje_completado >= 100.0:
                self.estado = 'COMPLETADA'
                self.fecha_fin_real = timezone.now()
                self.save()
            
            return True
        except:
            return False
    
    def detectar_retrasos(self):
        """
        Detecta etapas que están retrasadas respecto a su tiempo estimado.
        """
        etapas_retrasadas = []
        for etapa in self.etapas.all():
            if etapa.detectar_retraso():
                etapas_retrasadas.append(etapa)
        return etapas_retrasadas
    
    def obtener_tiempo_total_estimado(self):
        """
        Calcula el tiempo total estimado sumando todas las etapas.
        """
        total_minutos = self.etapas.aggregate(
            total=models.Sum('duracion_estimada')
        )['total'] or 0
        return timezone.timedelta(minutes=total_minutos)
    
    def obtener_tiempo_total_real(self):
        """
        Calcula el tiempo real transcurrido hasta ahora.
        """
        if self.fecha_fin_real:
            return self.fecha_fin_real - self.fecha_inicio
        return timezone.now() - self.fecha_inicio
    
    def pausar_ruta(self, motivo=""):
        """
        Pausa toda la ruta clínica.
        """
        self.estado = 'PAUSADA'
        self.metadatos_adicionales['motivo_pausa'] = motivo
        self.metadatos_adicionales['fecha_pausa'] = timezone.now().isoformat()
        self.save()
        
        # Pausar la etapa activa
        etapa_activa = self.obtener_etapa_actual()
        if etapa_activa:
            etapa_activa.pausar_etapa(motivo)
    
    def reanudar_ruta(self):
        """
        Reanuda la ruta clínica pausada.
        """
        if self.estado == 'PAUSADA':
            self.estado = 'EN_PROGRESO'
            self.metadatos_adicionales['fecha_reanudacion'] = timezone.now().isoformat()
            self.save()
            
            # Reanudar etapas pausadas
            for etapa in self.etapas.filter(estado='PAUSADA'):
                etapa.reanudar_etapa()

class EtapaRuta(models.Model):
    """
    Modelo para las etapas individuales dentro de una ruta clínica.
    Representa cada nodo del timeline horizontal.
    """
    
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADA', 'Completada'),
        ('PAUSADA', 'Pausada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    TIPO_ETAPA_CHOICES = [
        ('CHECK_IN', 'Check-in'),
        ('ESPERA_CONSULTA', 'Espera Consulta'),
        ('CONSULTA', 'Consulta Médica'),
        ('DERIVACION', 'Derivación'),
        ('ESPERA_EXAMEN', 'Espera Examen'),
        ('EXAMEN', 'Examen/Procedimiento'),
        ('RESULTADOS', 'Espera Resultados'),
        ('CONTROL', 'Control/Segunda Consulta'),
        ('ALTA', 'Alta Médica'),
        ('ADMINISTRATIVO', 'Proceso Administrativo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta_clinica = models.ForeignKey(
        RutaClinica, 
        on_delete=models.CASCADE,
        related_name='etapas'
    )
    
    nombre = models.CharField(max_length=100)
    tipo_etapa = models.CharField(
        max_length=20,
        choices=TIPO_ETAPA_CHOICES,
        default='CONSULTA'
    )
    orden = models.PositiveIntegerField(
        help_text="Orden de la etapa en la secuencia (1, 2, 3...)"
    )
    
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    duracion_estimada = models.PositiveIntegerField(
        help_text="Duración estimada en minutos"
    )
    duracion_real = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Duración real en minutos"
    )
    
    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_CHOICES,
        default='PENDIENTE'
    )
    
    # Campos para nodo estático
    es_estatico = models.BooleanField(
        default=False,
        help_text="True si la etapa está en espera de proceso externo"
    )
    motivo_pausa = models.TextField(
        blank=True,
        help_text="Motivo por el cual la etapa está pausada o es estática"
    )
    
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada de la etapa"
    )
    
    # Configuración específica de la etapa
    configuracion_etapa = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuraciones específicas de la etapa"
    )
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'etapas_ruta'
        verbose_name = 'Etapa de Ruta'
        verbose_name_plural = 'Etapas de Ruta'
        ordering = ['ruta_clinica', 'orden']
        unique_together = ['ruta_clinica', 'orden']
        indexes = [
            models.Index(fields=['ruta_clinica', 'orden']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo_etapa']),
            models.Index(fields=['es_estatico']),
        ]
    
    def __str__(self):
        return f"{self.ruta_clinica.paciente} - Etapa {self.orden}: {self.nombre}"
    
    def iniciar_etapa(self):
        """
        Inicia la etapa marcando fecha de inicio.
        """
        if self.estado == 'PENDIENTE':
            self.estado = 'EN_PROCESO'
            self.fecha_inicio = timezone.now()
            self.save()
            return True
        return False
    
    def finalizar_etapa(self):
        """
        Finaliza la etapa calculando duración real.
        """
        if self.estado == 'EN_PROCESO':
            self.estado = 'COMPLETADA'
            self.fecha_fin = timezone.now()
            
            # Calcular duración real
            if self.fecha_inicio:
                duracion = self.fecha_fin - self.fecha_inicio
                self.duracion_real = int(duracion.total_seconds() / 60)  # En minutos
            
            self.save()
            return True
        return False
    
    def pausar_etapa(self, motivo=""):
        """
        Pausa la etapa (nodo estático).
        """
        if self.estado == 'EN_PROCESO':
            self.estado = 'PAUSADA'
            self.es_estatico = True
            self.motivo_pausa = motivo
            self.save()
            return True
        return False
    
    def reanudar_etapa(self):
        """
        Reanuda la etapa pausada.
        """
        if self.estado == 'PAUSADA':
            self.estado = 'EN_PROCESO'
            self.es_estatico = False
            self.motivo_pausa = ""
            self.save()
            return True
        return False
    
    def calcular_tiempo_transcurrido(self):
        """
        Calcula el tiempo transcurrido desde el inicio de la etapa.
        """
        if self.fecha_inicio:
            fin = self.fecha_fin or timezone.now()
            return fin - self.fecha_inicio
        return None
    
    def detectar_retraso(self):
        """
        Detecta si la etapa está retrasada respecto al tiempo estimado.
        """
        if self.estado == 'EN_PROCESO' and self.fecha_inicio:
            tiempo_transcurrido = self.calcular_tiempo_transcurrido()
            if tiempo_transcurrido:
                minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
                return minutos_transcurridos > self.duracion_estimada
        return False
    
    def obtener_porcentaje_avance(self):
        """
        Calcula el porcentaje de avance de la etapa.
        """
        if self.estado == 'COMPLETADA':
            return 100.0
        elif self.estado == 'EN_PROCESO' and self.fecha_inicio:
            tiempo_transcurrido = self.calcular_tiempo_transcurrido()
            if tiempo_transcurrido:
                minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
                porcentaje = min((minutos_transcurridos / self.duracion_estimada) * 100, 100)
                return porcentaje
        return 0.0