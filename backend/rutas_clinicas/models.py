# backend/rutas_clinicas/models.py - VERSIÓN ACTUALIZADA CON TODAS LAS ETAPAS
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente


class RutaClinica(models.Model):
    """
    Modelo mejorado para gestionar rutas clínicas de pacientes.
    Ahora muestra TODAS las etapas disponibles, no solo las seleccionadas.
    """
    
    ESTADO_CHOICES = [
        ('INICIADA', 'Iniciada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('PAUSADA', 'Pausada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    # Etapas predefinidas con mapeo a estados de paciente
    ETAPAS_CHOICES = [
        ('CONSULTA_MEDICA', 'Consulta Médica'),
        ('PROCESO_EXAMEN', 'Proceso del Examen'),
        ('REVISION_EXAMEN', 'Revisión del Examen'),
        ('HOSPITALIZACION', 'Hospitalización'),
        ('OPERACION', 'Operación'),
        ('ALTA', 'Alta Médica'),
    ]
    
    # Mapeo de etapas a estados de paciente
    ETAPA_A_ESTADO_PACIENTE = {
        'CONSULTA_MEDICA': 'EN_CONSULTA',
        'PROCESO_EXAMEN': 'EN_EXAMEN',
        'REVISION_EXAMEN': 'EN_EXAMEN',
        'HOSPITALIZACION': 'EN_CONSULTA',
        'OPERACION': 'EN_CONSULTA',
        'ALTA': 'ALTA_COMPLETA',
    }
    
    # Duraciones estimadas por etapa (en minutos)
    DURACIONES_ESTIMADAS = {
        'CONSULTA_MEDICA': 30,
        'PROCESO_EXAMEN': 45,
        'REVISION_EXAMEN': 20,
        'HOSPITALIZACION': 1440,  # 24 horas
        'OPERACION': 120,
        'ALTA': 15,
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE,
        related_name='rutas_clinicas'
    )
    
    # Etapas y progreso
    etapas_seleccionadas = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de etapas en orden"
    )
    etapa_actual = models.CharField(
        max_length=30,
        choices=ETAPAS_CHOICES,
        null=True,
        blank=True,
    )
    indice_etapa_actual = models.PositiveIntegerField(default=0)
    etapas_completadas = models.JSONField(default=list)
    
    # Información detallada por etapa
    timestamps_etapas = models.JSONField(
        default=dict,
        help_text="Timestamps y detalles de cada etapa"
    )
    
    # Control temporal
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_estimada_fin = models.DateTimeField(null=True, blank=True)
    fecha_fin_real = models.DateTimeField(null=True, blank=True)
    
    # Progreso y estado
    porcentaje_completado = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='INICIADA')
    esta_pausado = models.BooleanField(default=False)
    motivo_pausa = models.TextField(blank=True)
    
    # Metadatos
    metadatos_adicionales = models.JSONField(default=dict, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Historial de cambios
    historial_cambios = models.JSONField(
        default=list,
        help_text="Registro de todos los cambios de etapa"
    )
    
    class Meta:
        db_table = 'rutas_clinicas'
        verbose_name = 'Ruta Clínica'
        verbose_name_plural = 'Rutas Clínicas'
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['paciente']),
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['etapa_actual']),
        ]
    
    def __str__(self):
        return f"Ruta {self.paciente} - {self.porcentaje_completado:.1f}% - {self.get_etapa_actual_display() or 'No iniciada'}"
    
    # ============================================
    # MÉTODOS PRINCIPALES
    # ============================================
    
    def iniciar_ruta(self, usuario=None):
        """Inicia la ruta clínica con la primera etapa"""
        # Obtener todas las etapas disponibles
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        
        # Si no hay etapas seleccionadas, usar todas
        if not self.etapas_seleccionadas:
            self.etapas_seleccionadas = todas_etapas
        
        self.estado = 'EN_PROGRESO'
        self.indice_etapa_actual = 0
        self.etapa_actual = todas_etapas[0]  # Siempre empezar con la primera etapa
        
        # Registrar inicio de primera etapa
        ahora = timezone.now()
        self.timestamps_etapas[self.etapa_actual] = {
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': None,
            'duracion_real': None,
            'duracion_estimada': self.DURACIONES_ESTIMADAS.get(self.etapa_actual, 30),
            'observaciones': '',
            'usuario_inicio': str(usuario) if usuario else None,
        }
        
        # Registrar en historial
        self._agregar_al_historial('INICIO_RUTA', self.etapa_actual, usuario)
        
        # Sincronizar estado del paciente
        self._sincronizar_estado_paciente()
        
        # Calcular fecha estimada de fin
        self._calcular_fecha_estimada_fin()
        
        self.save()
        return True
    
    def avanzar(self, observaciones=""):
        """
        Avanza a la siguiente etapa de la ruta clínica.
        """
        if self.estado != 'EN_PROGRESO':
            return False
        
        etapas = self.etapas_timeline.all().order_by('orden')
        total_etapas = etapas.count()
        
        # Verificar que no estemos en la última etapa
        if self.indice_etapa_actual >= total_etapas - 1:
            return False
        
        # Obtener la etapa actual
        etapa_actual = etapas[self.indice_etapa_actual]
        
        # Marcar la etapa actual como completada
        if not etapa_actual.fecha_fin:
            etapa_actual.fecha_fin = timezone.now()
            if etapa_actual.observaciones:
                etapa_actual.observaciones += f"\n{observaciones}"
            else:
                etapa_actual.observaciones = observaciones
            etapa_actual.save()
        
        # Avanzar al siguiente índice
        self.indice_etapa_actual += 1
        
        # Actualizar la etapa actual
        if self.indice_etapa_actual < total_etapas:
            siguiente_etapa = etapas[self.indice_etapa_actual]
            self.etapa_actual = siguiente_etapa.etapa
            
            # Iniciar la siguiente etapa si aún no tiene fecha de inicio
            if not siguiente_etapa.fecha_inicio:
                siguiente_etapa.fecha_inicio = timezone.now()
                siguiente_etapa.save()
        else:
            # Si llegamos al final, completar la ruta
            self.estado = 'COMPLETADA'
            self.etapa_actual = None
        
        # Recalcular progreso
        self.recalcular_progreso()
        
        self.save()
        
        # Registrar en el historial
        self.registrar_en_historial(
            accion='AVANZAR',
            usuario=None,
            desde=etapa_actual.get_etapa_display(),
            hacia=self.get_etapa_actual_display() if self.etapa_actual else 'Completada',
            motivo=observaciones
        )
        
        return True
    
    def retroceder_etapa(self, motivo='', usuario=None):
        """Retrocede a la etapa anterior"""
        # Obtener todas las etapas
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        
        if self.indice_etapa_actual <= 0:
            return False
        
        # Remover de completadas
        if self.etapa_actual in self.etapas_completadas:
            self.etapas_completadas.remove(self.etapa_actual)
        
        # Limpiar timestamps de etapa actual
        if self.etapa_actual in self.timestamps_etapas:
            del self.timestamps_etapas[self.etapa_actual]
        
        # Retroceder
        etapa_anterior = self.etapa_actual
        self.indice_etapa_actual -= 1
        self.etapa_actual = todas_etapas[self.indice_etapa_actual]
        
        # Registrar en historial
        self._agregar_al_historial('RETROCEDER', self.etapa_actual, usuario, {
            'desde': etapa_anterior,
            'hacia': self.etapa_actual,
            'motivo': motivo,
        })
        
        # Sincronizar estado del paciente
        self._sincronizar_estado_paciente()
        
        self.calcular_progreso()
        self.save()
        return True
    
    def pausar_ruta(self, motivo='', usuario=None):
        """Pausa la ruta clínica"""
        self.estado = 'PAUSADA'
        self.esta_pausado = True
        self.motivo_pausa = motivo
        self.metadatos_adicionales['fecha_pausa'] = timezone.now().isoformat()
        
        # Actualizar estado del paciente
        self.paciente.estado_actual = 'PROCESO_PAUSADO'
        self.paciente.save()
        
        self._agregar_al_historial('PAUSAR', self.etapa_actual, usuario, {
            'motivo': motivo
        })
        
        self.save()
    
    def reanudar_ruta(self, usuario=None):
        """Reanuda la ruta pausada"""
        if self.estado == 'PAUSADA':
            self.estado = 'EN_PROGRESO'
            self.esta_pausado = False
            self.motivo_pausa = ''
            self.metadatos_adicionales['fecha_reanudacion'] = timezone.now().isoformat()
            
            # Sincronizar estado del paciente
            self._sincronizar_estado_paciente()
            
            self._agregar_al_historial('REANUDAR', self.etapa_actual, usuario)
            
            self.save()
            return True
        return False
    
    # ============================================
    # MÉTODOS DE CÁLCULO Y ANÁLISIS
    # ============================================
    
    def calcular_progreso(self):
        """Calcula el porcentaje de progreso basado en TODAS las etapas"""
        # Obtener todas las etapas disponibles
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        total_etapas = len(todas_etapas)
        
        etapas_completadas = len(self.etapas_completadas)
        
        progreso = (etapas_completadas / total_etapas) * 100
        self.porcentaje_completado = progreso
        
        if not self._state.adding:
            self.save(update_fields=['porcentaje_completado'])
        
        return progreso
    
    def obtener_tiempo_total_real(self):
        """Calcula el tiempo real transcurrido"""
        if self.fecha_fin_real:
            return self.fecha_fin_real - self.fecha_inicio
        return timezone.now() - self.fecha_inicio
    
    def detectar_retrasos(self):
        """Detecta si alguna etapa está retrasada"""
        retrasos = []
        ahora = timezone.now()
        
        for etapa_key, etapa_data in self.timestamps_etapas.items():
            if etapa_data.get('fecha_fin'):
                continue  # Etapa completada
            
            if etapa_data.get('fecha_inicio'):
                inicio = timezone.datetime.fromisoformat(etapa_data['fecha_inicio'])
                duracion_actual = (ahora - inicio).total_seconds() / 60
                duracion_estimada = etapa_data.get('duracion_estimada', 30)
                
                if duracion_actual > duracion_estimada * 1.2:  # 20% de margen
                    retrasos.append({
                        'etapa': etapa_key,
                        'etapa_label': dict(self.ETAPAS_CHOICES).get(etapa_key),
                        'duracion_actual': int(duracion_actual),
                        'duracion_estimada': duracion_estimada,
                        'retraso_minutos': int(duracion_actual - duracion_estimada),
                    })
        
        return retrasos
    
    def obtener_timeline_completo(self):

        timeline = []
        
        # SIEMPRE usar TODAS las etapas disponibles
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        
        # Asegurar que etapas_completadas es una lista
        if not isinstance(self.etapas_completadas, list):
            self.etapas_completadas = []
        
        # Asegurar que etapas_seleccionadas es una lista
        if not isinstance(self.etapas_seleccionadas, list):
            self.etapas_seleccionadas = []
        
        for i, etapa_key in enumerate(todas_etapas):
            etapa_label = dict(self.ETAPAS_CHOICES).get(etapa_key, etapa_key)
            
            # ✅ CORRECCIÓN: Determinar estado con prioridad correcta
            # PRIORIDAD 1: Etapas completadas
            if etapa_key in self.etapas_completadas:
                estado = 'COMPLETADA'
            # PRIORIDAD 2: Etapa actual
            elif etapa_key == self.etapa_actual:
                estado = 'EN_PROCESO'
            # PRIORIDAD 3: Verificar si está en la lista de seleccionadas
            elif etapa_key in self.etapas_seleccionadas:
                estado = 'PENDIENTE'
            # PRIORIDAD 4: No está seleccionada, es opcional
            else:
                estado = 'NO_REQUERIDA'
            
            # Obtener timestamps y detalles
            etapa_data = self.timestamps_etapas.get(etapa_key, {})
            
            # Calcular si está retrasada
            retrasada = False
            if estado == 'EN_PROCESO' and etapa_data.get('fecha_inicio'):
                try:
                    inicio = timezone.datetime.fromisoformat(etapa_data['fecha_inicio'])
                    duracion_actual = (timezone.now() - inicio).total_seconds() / 60
                    duracion_estimada = etapa_data.get('duracion_estimada', self.DURACIONES_ESTIMADAS.get(etapa_key, 30))
                    retrasada = duracion_actual > duracion_estimada * 1.2
                except Exception:
                    retrasada = False
            
            # ✅ es_actual debe ser booleano explícito
            es_actual = (etapa_key == self.etapa_actual and self.estado == 'EN_PROGRESO')
            
            timeline.append({
                'orden': i + 1,
                'etapa_key': etapa_key,
                'etapa_label': etapa_label,
                'estado': estado,
                'fecha_inicio': etapa_data.get('fecha_inicio'),
                'fecha_fin': etapa_data.get('fecha_fin'),
                'duracion_real': etapa_data.get('duracion_real'),
                'duracion_estimada': etapa_data.get('duracion_estimada', self.DURACIONES_ESTIMADAS.get(etapa_key, 30)),
                'observaciones': etapa_data.get('observaciones', ''),
                'es_actual': es_actual,  # ✅ CORRECCIÓN: Verificación más robusta
                'retrasada': retrasada,
                'es_requerida': etapa_key in self.etapas_seleccionadas if self.etapas_seleccionadas else True,
            })
        
        return timeline
    
    def obtener_info_timeline(self):
        """Retorna información estructurada para el timeline (método legacy)"""
        # Ahora simplemente llama al nuevo método
        return self.obtener_timeline_completo()
    
    def obtener_etapa_siguiente(self):
        """Retorna la siguiente etapa"""
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        
        if not self.etapa_actual:
            return todas_etapas[0] if todas_etapas else None
        
        try:
            indice_actual = todas_etapas.index(self.etapa_actual)
            siguiente_indice = indice_actual + 1
            if siguiente_indice < len(todas_etapas):
                return todas_etapas[siguiente_indice]
        except ValueError:
            pass
        
        return None
    
    # ============================================
    # MÉTODOS PRIVADOS (HELPERS)
    # ============================================
    
    def _sincronizar_estado_paciente(self):
        """Sincroniza el estado del paciente con la etapa actual"""
        if self.etapa_actual:
            nuevo_estado = self.ETAPA_A_ESTADO_PACIENTE.get(
                self.etapa_actual,
                'EN_CONSULTA'
            )
            self.paciente.estado_actual = nuevo_estado
            self.paciente.save()
    
    def _agregar_al_historial(self, accion, etapa, usuario=None, data_extra=None):
        """Agrega una entrada al historial de cambios"""
        entrada = {
            'timestamp': timezone.now().isoformat(),
            'accion': accion,
            'etapa': etapa,
            'usuario': str(usuario) if usuario else 'Sistema',
        }
        
        if data_extra:
            entrada.update(data_extra)
        
        if not isinstance(self.historial_cambios, list):
            self.historial_cambios = []
        
        self.historial_cambios.append(entrada)
    
    def _calcular_fecha_estimada_fin(self):
        """Calcula la fecha estimada de finalización"""
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        duracion_total = sum(
            self.DURACIONES_ESTIMADAS.get(etapa, 30)
            for etapa in todas_etapas
        )
        self.fecha_estimada_fin = self.fecha_inicio + timezone.timedelta(minutes=duracion_total)
        