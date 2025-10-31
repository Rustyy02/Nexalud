# backend/rutas_clinicas/models.py - VERSIÓN CORREGIDA
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente


class RutaClinica(models.Model):
    """
    Modelo corregido para gestionar rutas clínicas de pacientes.
    
    ✅ CORRECCIONES IMPORTANTES:
    - Flujo lineal sin saltos de etapas
    - Manejo correcto del final de la ruta
    - Prevención de estados inconsistentes
    - Sincronización perfecta con Paciente
    """
    
    ESTADO_CHOICES = [
        ('INICIADA', 'Iniciada'),
        ('EN_PROGRESO', 'En Progreso'),
        ('PAUSADA', 'Pausada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]
    
    ETAPAS_CHOICES = [
        ('CONSULTA_MEDICA', 'Consulta Médica'),
        ('PROCESO_EXAMEN', 'Proceso del Examen'),
        ('REVISION_EXAMEN', 'Revisión del Examen'),
        ('HOSPITALIZACION', 'Hospitalización'),
        ('OPERACION', 'Operación'),
        ('ALTA', 'Alta Médica'),
    ]
    
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
    
    tiempo_pausado_acumulado = models.DurationField(
        default=timezone.timedelta(0),
        help_text="Tiempo total que la ruta ha estado en PAUSA"
    )
    
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
    # ✅ MÉTODO PRINCIPAL DE SINCRONIZACIÓN
    # ============================================
    
    def _sincronizar_etapa_paciente(self):
        """
        Sincroniza la etapa actual y el estado de la ruta con el paciente.
        """
        if self.estado == 'COMPLETADA':
            self.paciente.limpiar_etapa('ALTA_COMPLETA')
        elif self.estado == 'CANCELADA':
            self.paciente.limpiar_etapa('CANCELADA')
        elif self.estado == 'PAUSADA':
            if self.etapa_actual:
                self.paciente.actualizar_etapa(self.etapa_actual, 'PAUSADA')
            else:
                self.paciente.limpiar_etapa('PAUSADA')
        elif self.estado == 'EN_PROGRESO' and self.etapa_actual:
            self.paciente.actualizar_etapa(self.etapa_actual, 'EN_PROGRESO')
        elif not self.etapa_actual:
            self.paciente.limpiar_etapa('EN_ESPERA')
    
    # ============================================
    # ✅ MÉTODOS PRINCIPALES CORREGIDOS
    # ============================================
    
    def iniciar_ruta(self, usuario=None, etapa_inicial=None):
        """
        ✅ CORREGIDO: Inicia la ruta respetando el flujo lineal
        """
        # Usar todas las etapas en orden si no hay seleccionadas
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        
        if not self.etapas_seleccionadas or len(self.etapas_seleccionadas) == 0:
            self.etapas_seleccionadas = todas_etapas
        else:
            # Asegurar orden correcto según ETAPAS_CHOICES
            self.etapas_seleccionadas = sorted(
                self.etapas_seleccionadas,
                key=lambda x: todas_etapas.index(x) if x in todas_etapas else 999
            )
        
        # Determinar etapa inicial
        if etapa_inicial and etapa_inicial in todas_etapas:
            etapa_a_iniciar = etapa_inicial
        elif self.etapas_seleccionadas:
            etapa_a_iniciar = self.etapas_seleccionadas[0]
        else:
            etapa_a_iniciar = todas_etapas[0]
        
        # Encontrar índice en las etapas seleccionadas
        if etapa_a_iniciar in self.etapas_seleccionadas:
            self.indice_etapa_actual = self.etapas_seleccionadas.index(etapa_a_iniciar)
        else:
            # Si la etapa inicial no está en las seleccionadas, añadirla
            self.etapas_seleccionadas.append(etapa_a_iniciar)
            self.etapas_seleccionadas = sorted(
                self.etapas_seleccionadas,
                key=lambda x: todas_etapas.index(x) if x in todas_etapas else 999
            )
            self.indice_etapa_actual = self.etapas_seleccionadas.index(etapa_a_iniciar)
        
        # Configurar estado
        self.estado = 'EN_PROGRESO'
        self.etapa_actual = etapa_a_iniciar
        self.esta_pausado = False
        
        ahora = timezone.now()
        
        # Marcar etapas anteriores como completadas automáticamente
        for i in range(self.indice_etapa_actual):
            etapa_previa = self.etapas_seleccionadas[i]
            
            if etapa_previa not in self.etapas_completadas:
                self.etapas_completadas.append(etapa_previa)
            
            self.timestamps_etapas[etapa_previa] = {
                'fecha_inicio': ahora.isoformat(),
                'fecha_fin': ahora.isoformat(),
                'duracion_real': 0,
                'duracion_estimada': self.DURACIONES_ESTIMADAS.get(etapa_previa, 30),
                'observaciones': 'Etapa marcada como completada al iniciar la ruta',
                'usuario_inicio': 'Sistema',
                'auto_completada': True,
            }
        
        # Registrar inicio de la etapa actual
        self.timestamps_etapas[self.etapa_actual] = {
            'fecha_inicio': ahora.isoformat(),
            'fecha_fin': None,
            'duracion_real': None,
            'duracion_estimada': self.DURACIONES_ESTIMADAS.get(self.etapa_actual, 30),
            'observaciones': '',
            'usuario_inicio': str(usuario) if usuario else 'Sistema',
        }
        
        # Registrar en historial
        self._agregar_al_historial('INICIO_RUTA', self.etapa_actual, usuario)
        
        # Sincronizar con paciente
        self._sincronizar_etapa_paciente()
        
        # Calcular fecha estimada de fin
        self._calcular_fecha_estimada_fin()
        
        # Calcular progreso
        self.calcular_progreso()
        
        self.save()
        return True
    
    def avanzar_etapa(self, observaciones="", usuario=None):
        """
        ✅ CORREGIDO: Avanza linealmente sin saltos
        """
        # Validaciones iniciales
        if self.estado != 'EN_PROGRESO':
            return False
        
        if not self.etapa_actual:
            return False
        
        # Usar etapas seleccionadas o todas
        etapas = self.etapas_seleccionadas if self.etapas_seleccionadas else [key for key, _ in self.ETAPAS_CHOICES]
        
        # Verificar que no estamos al final
        if self.indice_etapa_actual >= len(etapas):
            return False
        
        # Marcar etapa actual como completada
        ahora = timezone.now()
        
        # Completar timestamp de etapa actual
        if self.etapa_actual in self.timestamps_etapas:
            etapa_info = self.timestamps_etapas[self.etapa_actual]
            etapa_info['fecha_fin'] = ahora.isoformat()
            
            if etapa_info.get('fecha_inicio'):
                inicio = timezone.datetime.fromisoformat(etapa_info['fecha_inicio'].replace('Z', '+00:00'))
                duracion = ahora - inicio
                etapa_info['duracion_real'] = int(duracion.total_seconds() / 60)
            
            if observaciones:
                etapa_info['observaciones'] = observaciones
            
            self.timestamps_etapas[self.etapa_actual] = etapa_info
        
        # Agregar a completadas si no está
        if self.etapa_actual not in self.etapas_completadas:
            self.etapas_completadas.append(self.etapa_actual)
        
        etapa_anterior = self.etapa_actual
        
        # Avanzar al siguiente índice
        self.indice_etapa_actual += 1
        
        # Verificar si llegamos al final
        if self.indice_etapa_actual >= len(etapas):
            # ✅ COMPLETAR LA RUTA
            self.estado = 'COMPLETADA'
            self.fecha_fin_real = ahora
            self.etapa_actual = None
            self.porcentaje_completado = 100.0
            
            # Limpiar etapa del paciente
            self.paciente.etapa_actual = None
            self.paciente.estado_actual = 'ALTA_COMPLETA'
            self.paciente.save(update_fields=['etapa_actual', 'estado_actual', 'fecha_actualizacion'])
            
            # Registrar en historial
            self._agregar_al_historial('COMPLETAR_RUTA', None, usuario, {
                'desde': etapa_anterior,
                'observaciones': observaciones,
            })
        else:
            # Configurar nueva etapa
            self.etapa_actual = etapas[self.indice_etapa_actual]
            
            # Iniciar timestamp de nueva etapa
            self.timestamps_etapas[self.etapa_actual] = {
                'fecha_inicio': ahora.isoformat(),
                'fecha_fin': None,
                'duracion_real': None,
                'duracion_estimada': self.DURACIONES_ESTIMADAS.get(self.etapa_actual, 30),
                'observaciones': '',
                'usuario_inicio': str(usuario) if usuario else 'Sistema',
            }
            
            # Sincronizar con paciente
            self._sincronizar_etapa_paciente()
            
            # Registrar en historial
            self._agregar_al_historial('AVANZAR', self.etapa_actual, usuario, {
                'desde': etapa_anterior,
                'hacia': self.etapa_actual,
                'observaciones': observaciones,
            })
        
        # Recalcular progreso
        self.calcular_progreso()
        
        self.save()
        return True
    
    def retroceder_etapa(self, motivo='', usuario=None):
        """
        ✅ CORREGIDO: Retrocede correctamente y reactiva el estado
        """
        etapas = self.etapas_seleccionadas if self.etapas_seleccionadas else [key for key, _ in self.ETAPAS_CHOICES]
        
        # No se puede retroceder desde la primera etapa
        if self.indice_etapa_actual <= 0:
            return False
        
        # Si la ruta está completada, reactivarla
        if self.estado == 'COMPLETADA':
            self.estado = 'EN_PROGRESO'
            self.fecha_fin_real = None
            
            # Configurar la última etapa
            self.indice_etapa_actual = len(etapas) - 1
            self.etapa_actual = etapas[self.indice_etapa_actual]
            
            # Remover de completadas
            if self.etapa_actual in self.etapas_completadas:
                self.etapas_completadas.remove(self.etapa_actual)
            
            # Limpiar timestamp
            if self.etapa_actual in self.timestamps_etapas:
                del self.timestamps_etapas[self.etapa_actual]
            
            # Reiniciar timestamp
            self.timestamps_etapas[self.etapa_actual] = {
                'fecha_inicio': timezone.now().isoformat(),
                'fecha_fin': None,
                'duracion_real': None,
                'duracion_estimada': self.DURACIONES_ESTIMADAS.get(self.etapa_actual, 30),
                'observaciones': 'Reactivado desde estado completado',
                'usuario_inicio': str(usuario) if usuario else 'Sistema',
            }
        else:
            # Retroceso normal
            # Remover etapa actual de completadas si está
            if self.etapa_actual in self.etapas_completadas:
                self.etapas_completadas.remove(self.etapa_actual)
            
            # Limpiar timestamp de etapa actual
            if self.etapa_actual in self.timestamps_etapas:
                del self.timestamps_etapas[self.etapa_actual]
            
            etapa_anterior = self.etapa_actual
            
            # Retroceder índice
            self.indice_etapa_actual -= 1
            self.etapa_actual = etapas[self.indice_etapa_actual]
            
            # Si la etapa anterior está marcada como completada, removerla
            if self.etapa_actual in self.etapas_completadas:
                self.etapas_completadas.remove(self.etapa_actual)
            
            # Reiniciar timestamp de la etapa a la que retrocedemos
            self.timestamps_etapas[self.etapa_actual] = {
                'fecha_inicio': timezone.now().isoformat(),
                'fecha_fin': None,
                'duracion_real': None,
                'duracion_estimada': self.DURACIONES_ESTIMADAS.get(self.etapa_actual, 30),
                'observaciones': f'Retroceso desde {etapa_anterior}',
                'usuario_inicio': str(usuario) if usuario else 'Sistema',
            }
            
            # Registrar en historial
            self._agregar_al_historial('RETROCEDER', self.etapa_actual, usuario, {
                'desde': etapa_anterior,
                'hacia': self.etapa_actual,
                'motivo': motivo,
            })
        
        # Asegurar que el estado sea EN_PROGRESO
        self.estado = 'EN_PROGRESO'
        self.esta_pausado = False
        
        # Sincronizar con paciente
        self._sincronizar_etapa_paciente()
        
        # Recalcular progreso
        self.calcular_progreso()
        
        self.save()
        return True
    
    def pausar_ruta(self, motivo='', usuario=None):
        """Pausa la ruta y actualiza estado del paciente"""
        if self.estado != 'EN_PROGRESO':
            return False
        
        self.estado = 'PAUSADA'
        self.esta_pausado = True
        self.motivo_pausa = motivo
        self.metadatos_adicionales['fecha_pausa'] = timezone.now().isoformat()
        
        # Sincronizar estado pausado con paciente
        self._sincronizar_etapa_paciente()
        
        self._agregar_al_historial('PAUSAR', self.etapa_actual, usuario, {
            'motivo': motivo
        })
        
        self.save()
        return True
    
    def reanudar_ruta(self, usuario=None):
        """Reanuda la ruta y actualiza estado del paciente"""
        if self.estado != 'PAUSADA':
            return False
        
        self.estado = 'EN_PROGRESO'
        self.esta_pausado = False
        self.motivo_pausa = ''
        self.metadatos_adicionales['fecha_reanudacion'] = timezone.now().isoformat()
        
        # Sincronizar con paciente
        self._sincronizar_etapa_paciente()
        
        self._agregar_al_historial('REANUDAR', self.etapa_actual, usuario)
        
        self.save()
        return True
    
    # ============================================
    # MÉTODOS DE CÁLCULO Y ANÁLISIS
    # ============================================
    
    def calcular_progreso(self):
        """Calcula el porcentaje de progreso basado en etapas seleccionadas"""
        if not self.etapas_seleccionadas:
            self.porcentaje_completado = 0.0
            return 0.0
        
        total_etapas = len(self.etapas_seleccionadas)
        
        # Contar solo las etapas completadas que están en las seleccionadas
        etapas_completadas_validas = [
            etapa for etapa in self.etapas_completadas 
            if etapa in self.etapas_seleccionadas
        ]
        
        progreso = (len(etapas_completadas_validas) / total_etapas) * 100 if total_etapas > 0 else 0
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
                inicio = timezone.datetime.fromisoformat(etapa_data['fecha_inicio'].replace('Z', '+00:00'))
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
        """
        ✅ CORREGIDO: Timeline que muestra correctamente el flujo lineal
        """
        timeline = []
        
        # Usar etapas seleccionadas o todas
        etapas_a_mostrar = self.etapas_seleccionadas if self.etapas_seleccionadas else [key for key, _ in self.ETAPAS_CHOICES]
        
        for i, etapa_key in enumerate(etapas_a_mostrar):
            etapa_label = dict(self.ETAPAS_CHOICES).get(etapa_key, etapa_key)
            
            # Determinar estado de la etapa
            if etapa_key in self.etapas_completadas:
                estado = 'COMPLETADA'
            elif etapa_key == self.etapa_actual:
                estado = 'EN_CURSO'
            elif i < self.indice_etapa_actual:
                # Etapa anterior a la actual debería estar completada
                estado = 'COMPLETADA'
            else:
                estado = 'PENDIENTE'
            
            # Obtener timestamps y detalles
            etapa_data = self.timestamps_etapas.get(etapa_key, {})
            
            # Calcular si está retrasada
            retrasada = False
            if estado == 'EN_CURSO' and etapa_data.get('fecha_inicio'):
                try:
                    inicio = timezone.datetime.fromisoformat(
                        etapa_data['fecha_inicio'].replace('Z', '+00:00')
                    )
                    duracion_actual = (timezone.now() - inicio).total_seconds() / 60
                    duracion_estimada = etapa_data.get(
                        'duracion_estimada',
                        self.DURACIONES_ESTIMADAS.get(etapa_key, 30)
                    )
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
                'duracion_estimada': etapa_data.get(
                    'duracion_estimada',
                    self.DURACIONES_ESTIMADAS.get(etapa_key, 30)
                ),
                'observaciones': etapa_data.get('observaciones', ''),
                'es_actual': es_actual,
                'retrasada': retrasada,
                'es_requerida': True,
                'auto_completada': etapa_data.get('auto_completada', False),
            })
        
        return timeline
    
    def obtener_info_timeline(self):
        """Retorna información estructurada para el timeline"""
        return self.obtener_timeline_completo()
    
    def obtener_etapa_siguiente(self):
        """Retorna la siguiente etapa"""
        etapas = self.etapas_seleccionadas if self.etapas_seleccionadas else [key for key, _ in self.ETAPAS_CHOICES]
        
        if self.indice_etapa_actual + 1 < len(etapas):
            return etapas[self.indice_etapa_actual + 1]
        
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
        if not self.etapas_seleccionadas:
            return
        
        # Calcular solo para las etapas restantes
        etapas_restantes = self.etapas_seleccionadas[self.indice_etapa_actual:]
        duracion_total = sum(
            self.DURACIONES_ESTIMADAS.get(etapa, 30)
            for etapa in etapas_restantes
        )
        
        self.fecha_estimada_fin = timezone.now() + timezone.timedelta(minutes=duracion_total)