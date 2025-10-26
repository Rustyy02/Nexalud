# backend/rutas_clinicas/models.py - ACTUALIZADO PARA TIPO DE ATENCIÓN
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente


class RutaClinica(models.Model):
    """
    Modelo de RutaClinica actualizado que adapta sus etapas según el tipo de atención.
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
    
    # ============================================
    # NUEVO: TIPO DE ATENCIÓN
    # ============================================
    
    tipo_atencion = models.ForeignKey(
        'tipos_atencion.TipoAtencion',
        on_delete=models.PROTECT,
        related_name='rutas',
        help_text="Tipo de atención que define las etapas de esta ruta"
    )
    
    # Etapas y progreso
    etapas_seleccionadas = models.JSONField(
        default=list,
        blank=True,
        help_text="Etapas específicas para este paciente (del tipo de atención)"
    )
    etapa_actual = models.CharField(
        max_length=50,  # Aumentado para etapas más específicas
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
            models.Index(fields=['tipo_atencion']),
        ]
    
    def __str__(self):
        return f"Ruta {self.paciente.nombre_completo} - {self.tipo_atencion.nombre} - {self.porcentaje_completado:.1f}%"
    
    # ============================================
    # MÉTODOS PRINCIPALES ACTUALIZADOS
    # ============================================
    
    def iniciar_ruta(self, usuario=None):
        """
        Inicia la ruta clínica usando las etapas del tipo de atención asignado.
        """
        # Obtener etapas del tipo de atención
        etapas_tipo_atencion = self.tipo_atencion.etapas_flujo
        
        if not etapas_tipo_atencion:
            raise ValueError(f"El tipo de atención {self.tipo_atencion.nombre} no tiene etapas configuradas")
        
        # Si no hay etapas seleccionadas, usar todas del tipo de atención
        if not self.etapas_seleccionadas:
            self.etapas_seleccionadas = etapas_tipo_atencion.copy()
        
        self.estado = 'EN_PROGRESO'
        self.indice_etapa_actual = 0
        self.etapa_actual = self.etapas_seleccionadas[0]
        
        # Obtener duración estimada del tipo de atención
        duracion_estimada = self.tipo_atencion.duraciones_estimadas.get(
            self.etapa_actual,
            30  # Default 30 minutos
        )
        
        # Registrar inicio de primera etapa
        ahora = timezone.now()
        self.timestamps_etapas[self.etapa_actual] = {
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': None,
            'duracion_real': None,
            'duracion_estimada': duracion_estimada,
            'observaciones': '',
            'usuario_inicio': str(usuario) if usuario else None,
        }
        
        # Registrar en historial
        self._agregar_al_historial('INICIO_RUTA', self.etapa_actual, usuario, {
            'tipo_atencion': self.tipo_atencion.nombre,
            'nivel': self.tipo_atencion.get_nivel_display(),
        })
        
        # Sincronizar con paciente
        self._sincronizar_con_paciente()
        
        # Calcular fecha estimada de fin
        self._calcular_fecha_estimada_fin()
        
        self.save()
        return True
    
    def avanzar_etapa(self, observaciones="", usuario=None):
        """
        Avanza a la siguiente etapa según el tipo de atención.
        """
        if self.estado != 'EN_PROGRESO':
            return False
        
        # Marcar etapa actual como completada
        if self.etapa_actual and self.etapa_actual not in self.etapas_completadas:
            self.etapas_completadas.append(self.etapa_actual)
            
            # Actualizar timestamps
            if self.etapa_actual in self.timestamps_etapas:
                ahora = timezone.now()
                self.timestamps_etapas[self.etapa_actual]['fecha_fin'] = ahora.isoformat()
                
                # Calcular duración real
                fecha_inicio_str = self.timestamps_etapas[self.etapa_actual]['fecha_inicio']
                fecha_inicio = timezone.datetime.fromisoformat(fecha_inicio_str)
                duracion_real = int((ahora - fecha_inicio).total_seconds() / 60)
                self.timestamps_etapas[self.etapa_actual]['duracion_real'] = duracion_real
                
                if observaciones:
                    self.timestamps_etapas[self.etapa_actual]['observaciones'] = observaciones
        
        # Verificar si hay más etapas
        if self.indice_etapa_actual < len(self.etapas_seleccionadas) - 1:
            etapa_anterior = self.etapa_actual
            self.indice_etapa_actual += 1
            self.etapa_actual = self.etapas_seleccionadas[self.indice_etapa_actual]
            
            # Obtener duración estimada del tipo de atención
            duracion_estimada = self.tipo_atencion.duraciones_estimadas.get(
                self.etapa_actual,
                30
            )
            
            # Iniciar nueva etapa
            ahora = timezone.now()
            self.timestamps_etapas[self.etapa_actual] = {
                'fecha_inicio': ahora.isoformat(),
                'fecha_fin': None,
                'duracion_real': None,
                'duracion_estimada': duracion_estimada,
                'observaciones': '',
                'usuario_inicio': str(usuario) if usuario else None,
            }
            
            # Registrar en historial
            self._agregar_al_historial('AVANZAR', self.etapa_actual, usuario, {
                'desde': etapa_anterior,
                'hacia': self.etapa_actual,
                'observaciones': observaciones,
            })
            
        else:
            # Ruta completada
            self.estado = 'COMPLETADA'
            self.fecha_fin_real = timezone.now()
            
            # Última etapa es siempre ALTA_MEDICA o similar
            ultima_etapa = self.etapas_seleccionadas[-1]
            if 'ALTA' in ultima_etapa:
                self.etapa_actual = ultima_etapa
            
            self._agregar_al_historial('COMPLETAR_RUTA', self.etapa_actual, usuario)
            
            # Dar de alta al paciente
            self.paciente.dar_alta()
        
        # Sincronizar con paciente
        self._sincronizar_con_paciente()
        
        self.calcular_progreso()
        self.save()
        return True
    
    def retroceder_etapa(self, motivo='', usuario=None):
        """Retrocede a la etapa anterior"""
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
        self.etapa_actual = self.etapas_seleccionadas[self.indice_etapa_actual]
        
        # Registrar en historial
        self._agregar_al_historial('RETROCEDER', self.etapa_actual, usuario, {
            'desde': etapa_anterior,
            'hacia': self.etapa_actual,
            'motivo': motivo,
        })
        
        # Sincronizar con paciente
        self._sincronizar_con_paciente()
        
        self.calcular_progreso()
        self.save()
        return True
    
    def pausar_ruta(self, motivo='', usuario=None):
        """Pausa la ruta clínica y el paciente"""
        self.estado = 'PAUSADA'
        self.esta_pausado = True
        self.motivo_pausa = motivo
        self.metadatos_adicionales['fecha_pausa'] = timezone.now().isoformat()
        
        # Pausar paciente
        self.paciente.pausar_proceso(motivo)
        
        self._agregar_al_historial('PAUSAR', self.etapa_actual, usuario, {
            'motivo': motivo
        })
        
        self.save()
    
    def reanudar_ruta(self, usuario=None):
        """Reanuda la ruta pausada y el paciente"""
        if self.estado == 'PAUSADA':
            self.estado = 'EN_PROGRESO'
            self.esta_pausado = False
            self.motivo_pausa = ''
            self.metadatos_adicionales['fecha_reanudacion'] = timezone.now().isoformat()
            
            # Reanudar paciente
            self.paciente.reanudar_proceso()
            
            self._agregar_al_historial('REANUDAR', self.etapa_actual, usuario)
            
            self.save()
            return True
        return False
    
    # ============================================
    # MÉTODOS DE SINCRONIZACIÓN Y CÁLCULO
    # ============================================
    
    def _sincronizar_con_paciente(self):
        """Sincroniza el estado de la ruta con el paciente"""
        if self.etapa_actual:
            self.paciente.actualizar_etapa(self.etapa_actual)
    
    def calcular_progreso(self):
        """Calcula el porcentaje de progreso"""
        total_etapas = len(self.etapas_seleccionadas)
        etapas_completadas = len(self.etapas_completadas)
        
        progreso = (etapas_completadas / total_etapas) * 100 if total_etapas > 0 else 0
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
                    # Obtener label de la etapa
                    etapa_label = dict(self.tipo_atencion.ETAPAS_DISPONIBLES).get(
                        etapa_key,
                        etapa_key
                    )
                    
                    retrasos.append({
                        'etapa': etapa_key,
                        'etapa_label': etapa_label,
                        'duracion_actual': int(duracion_actual),
                        'duracion_estimada': duracion_estimada,
                        'retraso_minutos': int(duracion_actual - duracion_estimada),
                    })
        
        return retrasos
    
    def obtener_timeline_completo(self):
        """Retorna el timeline completo con las etapas del tipo de atención"""
        timeline = []
        
        if not isinstance(self.etapas_completadas, list):
            self.etapas_completadas = []
        if not isinstance(self.etapas_seleccionadas, list):
            self.etapas_seleccionadas = []
        
        # Usar las etapas del tipo de atención
        etapas_tipo = self.tipo_atencion.ETAPAS_DISPONIBLES
        
        for i, etapa_key in enumerate(self.etapas_seleccionadas):
            etapa_label = dict(etapas_tipo).get(etapa_key, etapa_key)
            
            # Determinar estado
            if etapa_key in self.etapas_completadas:
                estado = 'COMPLETADA'
            elif etapa_key == self.etapa_actual:
                estado = 'EN_CURSO'
            else:
                estado = 'PENDIENTE'
            
            # Obtener timestamps
            etapa_data = self.timestamps_etapas.get(etapa_key, {})
            
            # Calcular si está retrasada
            retrasada = False
            if estado == 'EN_CURSO' and etapa_data.get('fecha_inicio'):
                try:
                    inicio = timezone.datetime.fromisoformat(etapa_data['fecha_inicio'])
                    duracion_actual = (timezone.now() - inicio).total_seconds() / 60
                    duracion_estimada = etapa_data.get('duracion_estimada', 30)
                    retrasada = duracion_actual > duracion_estimada * 1.2
                except Exception:
                    retrasada = False
            
            es_actual = (etapa_key == self.etapa_actual and self.estado == 'EN_PROGRESO')
            
            timeline.append({
                'orden': i + 1,
                'etapa_key': etapa_key,
                'etapa_label': etapa_label,
                'estado': estado,
                'fecha_inicio': etapa_data.get('fecha_inicio'),
                'fecha_fin': etapa_data.get('fecha_fin'),
                'duracion_real': etapa_data.get('duracion_real'),
                'duracion_estimada': etapa_data.get('duracion_estimada', 30),
                'observaciones': etapa_data.get('observaciones', ''),
                'es_actual': es_actual,
                'retrasada': retrasada,
                'es_requerida': True,  # Todas las etapas seleccionadas son requeridas
            })
        
        return timeline
    
    def obtener_info_timeline(self):
        """Método legacy"""
        return self.obtener_timeline_completo()
    
    def obtener_etapa_siguiente(self):
        """Retorna la siguiente etapa"""
        if not self.etapa_actual:
            return self.etapas_seleccionadas[0] if self.etapas_seleccionadas else None
        
        try:
            indice_actual = self.etapas_seleccionadas.index(self.etapa_actual)
            siguiente_indice = indice_actual + 1
            if siguiente_indice < len(self.etapas_seleccionadas):
                return self.etapas_seleccionadas[siguiente_indice]
        except ValueError:
            pass
        
        return None
    
    # ============================================
    # MÉTODOS PRIVADOS (HELPERS)
    # ============================================
    
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
        duracion_total = sum(
            self.tipo_atencion.duraciones_estimadas.get(etapa, 30)
            for etapa in self.etapas_seleccionadas
        )
        self.fecha_estimada_fin = self.fecha_inicio + timezone.timedelta(minutes=duracion_total)