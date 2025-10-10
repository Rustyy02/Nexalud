# backend/rutas_clinicas/models.py
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente


class RutaClinica(models.Model):
    """
    Modelo para gestionar las rutas clínicas de los pacientes.
    Las etapas son un campo de múltiple selección dentro del mismo modelo.
    """
    
    ESTADO_CHOICES = [
        ('INICIADA', 'Iniciada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('PAUSADA', 'Pausada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    # Etapas predefinidas del proceso clínico
    ETAPAS_CHOICES = [
        ('CONSULTA_MEDICA', 'Consulta Médica'),
        ('PROCESO_EXAMEN', 'Proceso del Examen'),
        ('REVISION_EXAMEN', 'Revisión del Examen'),
        ('HOSPITALIZACION', 'Hospitalización'),
        ('OPERACION', 'Operado'),
        ('ALTA', 'Alta'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE,
        related_name='rutas_clinicas'
    )
    
    # Etapas seleccionadas (campo JSON con array de strings)
    etapas_seleccionadas = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de etapas seleccionadas en orden: ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', ...]"
    )
    
    # Etapa actual en el proceso
    etapa_actual = models.CharField(
        max_length=30,
        choices=ETAPAS_CHOICES,
        null=True,
        blank=True,
        help_text="Etapa actual en la que se encuentra el paciente"
    )
    
    # Índice de la etapa actual (posición en el array)
    indice_etapa_actual = models.PositiveIntegerField(
        default=0,
        help_text="Índice de la etapa actual en la lista de etapas"
    )
    
    # Etapas completadas (para tracking)
    etapas_completadas = models.JSONField(
        default=list,
        help_text="Lista de etapas ya completadas"
    )
    
    # Timestamps de cada etapa
    timestamps_etapas = models.JSONField(
        default=dict,
        help_text="Diccionario con fecha_inicio y fecha_fin de cada etapa"
    )
    
    # Campos de control temporal
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
    
    # Estado de pausa
    esta_pausado = models.BooleanField(
        default=False,
        help_text="Indica si la ruta está actualmente pausada"
    )
    motivo_pausa = models.TextField(
        blank=True,
        help_text="Motivo por el cual está pausada la ruta"
    )
    
    # Metadatos adicionales
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
            models.Index(fields=['etapa_actual']),
        ]
    
    def __str__(self):
        return f"Ruta {self.paciente} - {self.porcentaje_completado:.1f}% - {self.get_etapa_actual_display() or 'No iniciada'}"
    
    def iniciar_ruta(self):
        """Inicia la ruta clínica con la primera etapa"""
        if not self.etapas_seleccionadas:
            return False
        
        self.estado = 'EN_PROGRESO'
        self.indice_etapa_actual = 0
        self.etapa_actual = self.etapas_seleccionadas[0]
        
        # Registrar timestamp de inicio de la primera etapa
        self.timestamps_etapas[self.etapa_actual] = {
            'fecha_inicio': timezone.now().isoformat(),
            'fecha_fin': None
        }
        
        self.save()
        return True
    
    def avanzar_etapa(self):
        """Avanza a la siguiente etapa del proceso"""
        if not self.etapas_seleccionadas:
            return False
        
        # Marcar etapa actual como completada
        if self.etapa_actual and self.etapa_actual not in self.etapas_completadas:
            self.etapas_completadas.append(self.etapa_actual)
            
            # Registrar fecha de fin
            if self.etapa_actual in self.timestamps_etapas:
                self.timestamps_etapas[self.etapa_actual]['fecha_fin'] = timezone.now().isoformat()
        
        # Verificar si hay más etapas
        if self.indice_etapa_actual + 1 >= len(self.etapas_seleccionadas):
            # No hay más etapas, completar ruta
            self.estado = 'COMPLETADA'
            self.etapa_actual = None
            self.fecha_fin_real = timezone.now()
            self.porcentaje_completado = 100.0
            self.save()
            return True
        
        # Avanzar a siguiente etapa
        self.indice_etapa_actual += 1
        self.etapa_actual = self.etapas_seleccionadas[self.indice_etapa_actual]
        
        # Registrar timestamp de inicio de nueva etapa
        self.timestamps_etapas[self.etapa_actual] = {
            'fecha_inicio': timezone.now().isoformat(),
            'fecha_fin': None
        }
        
        # Calcular progreso
        self.calcular_progreso()
        self.save()
        return True
    
    def retroceder_etapa(self):
        """Retrocede a la etapa anterior (por si hay error)"""
        if self.indice_etapa_actual <= 0:
            return False
        
        # Remover de completadas si existe
        if self.etapa_actual in self.etapas_completadas:
            self.etapas_completadas.remove(self.etapa_actual)
        
        # Retroceder índice
        self.indice_etapa_actual -= 1
        self.etapa_actual = self.etapas_seleccionadas[self.indice_etapa_actual]
        
        # Calcular progreso
        self.calcular_progreso()
        self.save()
        return True
    
    def calcular_progreso(self):
        """Calcula el porcentaje de progreso basado en etapas completadas"""
        if not self.etapas_seleccionadas:
            self.porcentaje_completado = 0.0
            return 0.0
        
        total_etapas = len(self.etapas_seleccionadas)
        etapas_completadas = len(self.etapas_completadas)
        
        progreso = (etapas_completadas / total_etapas) * 100
        self.porcentaje_completado = progreso
        
        if not self._state.adding:  # Solo save si no es creación
            self.save(update_fields=['porcentaje_completado'])
        
        return progreso
    
    def pausar_ruta(self, motivo=""):
        """Pausa toda la ruta clínica"""
        self.estado = 'PAUSADA'
        self.esta_pausado = True
        self.motivo_pausa = motivo
        self.metadatos_adicionales['fecha_pausa'] = timezone.now().isoformat()
        self.save()
    
    def reanudar_ruta(self):
        """Reanuda la ruta clínica pausada"""
        if self.estado == 'PAUSADA':
            self.estado = 'EN_PROGRESO'
            self.esta_pausado = False
            self.motivo_pausa = ""
            self.metadatos_adicionales['fecha_reanudacion'] = timezone.now().isoformat()
            self.save()
            return True
        return False
    
    def obtener_etapa_siguiente(self):
        """Retorna la siguiente etapa en el proceso"""
        if not self.etapas_seleccionadas:
            return None
        
        siguiente_indice = self.indice_etapa_actual + 1
        if siguiente_indice < len(self.etapas_seleccionadas):
            return self.etapas_seleccionadas[siguiente_indice]
        return None
    
    def obtener_tiempo_total_real(self):
        """Calcula el tiempo real transcurrido"""
        if self.fecha_fin_real:
            return self.fecha_fin_real - self.fecha_inicio
        return timezone.now() - self.fecha_inicio
    
    def obtener_info_timeline(self):
        """Retorna información estructurada para el timeline"""
        timeline = []
        
        for i, etapa_key in enumerate(self.etapas_seleccionadas):
            # Obtener el label legible
            etapa_label = dict(self.ETAPAS_CHOICES).get(etapa_key, etapa_key)
            
            # Determinar estado
            if etapa_key in self.etapas_completadas:
                estado = 'COMPLETADA'
            elif etapa_key == self.etapa_actual:
                estado = 'EN_PROCESO'
            else:
                estado = 'PENDIENTE'
            
            # Obtener timestamps
            timestamps = self.timestamps_etapas.get(etapa_key, {})
            
            timeline.append({
                'orden': i + 1,
                'etapa_key': etapa_key,
                'etapa_label': etapa_label,
                'estado': estado,
                'fecha_inicio': timestamps.get('fecha_inicio'),
                'fecha_fin': timestamps.get('fecha_fin'),
                'es_actual': etapa_key == self.etapa_actual,
            })
        
        return timeline