# backend/rutas_clinicas/models.py - VERSIÓN ACTUALIZADA CON SINCRONIZACIÓN
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from pacientes.models import Paciente


class RutaClinica(models.Model):
    """
    Modelo mejorado para gestionar rutas clínicas de pacientes.
    
    ✅ CAMBIO IMPORTANTE:
    - Sincroniza automáticamente paciente.etapa_actual con ruta.etapa_actual
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
        help_text="Tiempo total que la ruta ha estado en PAUSA (para cálculos de precisión)."
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
            # Determinar el estado que debe reflejar el paciente
            if self.estado == 'COMPLETADA':
                self.paciente.limpiar_etapa('ALTA_COMPLETA')
            elif self.estado == 'CANCELADA':
                self.paciente.limpiar_etapa('CANCELADA')
            elif self.estado == 'PAUSADA':
                # Mantiene la etapa, pero cambia el estado general a PROCESO_PAUSADO
                if self.etapa_actual:
                    self.paciente.actualizar_etapa(self.etapa_actual, 'PAUSADA')
                else:
                    self.paciente.limpiar_etapa('PAUSADA')
            elif self.estado == 'EN_PROGRESO' and self.etapa_actual:
                # Sincroniza la etapa y establece el estado general a ACTIVO
                self.paciente.actualizar_etapa(self.etapa_actual, 'EN_PROGRESO')
            elif not self.etapa_actual:
                # Caso raro o justo antes de iniciar, limpia.
                self.paciente.limpiar_etapa('EN_ESPERA')
    
    # ============================================
    # MÉTODOS PRINCIPALES (ACTUALIZADOS)
    # ============================================
    
    def iniciar_ruta(self, usuario=None):
        """
        ✅ CORREGIDO: Inicia la ruta con manejo correcto de etapas previas
        """
        # Si no hay etapas seleccionadas, usar todas
        if not self.etapas_seleccionadas or len(self.etapas_seleccionadas) == 0:
            todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
            self.etapas_seleccionadas = todas_etapas
        
        # ✅ NUEVO: Ordenar etapas según el orden fijo del sistema
        orden_fijo = [key for key, _ in self.ETAPAS_CHOICES]
        self.etapas_seleccionadas = sorted(
            self.etapas_seleccionadas, 
            key=lambda x: orden_fijo.index(x)
        )
        
        # Configurar primera etapa
        self.estado = 'EN_PROGRESO'
        self.indice_etapa_actual = 0
        self.etapa_actual = self.etapas_seleccionadas[0]
        
        # ✅ NUEVO: Marcar automáticamente como completadas las etapas anteriores
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        indice_primera_etapa = todas_etapas.index(self.etapa_actual)
        
        # Completar etapas anteriores a la etapa inicial
        ahora = timezone.now()
        for i in range(indice_primera_etapa):
            etapa_previa = todas_etapas[i]
            
            # Agregar a completadas
            if etapa_previa not in self.etapas_completadas:
                self.etapas_completadas.append(etapa_previa)
            
            # Registrar timestamp (marcada como completada automáticamente)
            self.timestamps_etapas[etapa_previa] = {
                'fecha_inicio': ahora.isoformat(),
                'fecha_fin': ahora.isoformat(),
                'duracion_real': 0,
                'duracion_estimada': self.DURACIONES_ESTIMADAS.get(etapa_previa, 30),
                'observaciones': 'Etapa completada automáticamente (anterior a etapa inicial)',
                'usuario_inicio': 'Sistema',
                'auto_completada': True,
            }
        
        # Registrar inicio de primera etapa activa
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
        
        # Sincronizar con paciente
        self._sincronizar_etapa_paciente()
        
        # Calcular fecha estimada de fin
        self._calcular_fecha_estimada_fin()
        
        self.save()
        return True

    
    def avanzar_etapa(self, observaciones="", usuario=None):
        """
        ✅ CORREGIDO: Avanza a la siguiente etapa y sincroniza correctamente
        """
        if self.estado != 'EN_PROGRESO':
            return False
        
        # ✅ USAR ETAPAS SELECCIONADAS
        etapas = self.etapas_seleccionadas if self.etapas_seleccionadas else [key for key, _ in self.ETAPAS_CHOICES]
        
        # ✅ BUG FIX: Eliminada validación que impedía avanzar desde la última etapa
        # Antes había: if self.indice_etapa_actual >= len(etapas) - 1: return False
        # Esto impedía completar la ruta. Ahora el flujo natural maneja correctamente
        # el avance a través de todas las etapas y la completitud final.
        
        
        # Marcar etapa actual como completada
        if self.etapa_actual:
            ahora = timezone.now()
            
            # Completar timestamp de etapa actual
            if self.etapa_actual in self.timestamps_etapas:
                etapa_info = self.timestamps_etapas[self.etapa_actual]
                etapa_info['fecha_fin'] = ahora.isoformat()
                
                # Calcular duración real
                if etapa_info.get('fecha_inicio'):
                    inicio = timezone.datetime.fromisoformat(etapa_info['fecha_inicio'].replace('Z', '+00:00'))
                    duracion = ahora - inicio
                    etapa_info['duracion_real'] = int(duracion.total_seconds() / 60)
                
                # Agregar observaciones
                if observaciones:
                    etapa_info['observaciones'] = observaciones
                
                self.timestamps_etapas[self.etapa_actual] = etapa_info
            
            # Agregar a completadas
            if self.etapa_actual not in self.etapas_completadas:
                self.etapas_completadas.append(self.etapa_actual)
        
        # Avanzar al siguiente índice
        self.indice_etapa_actual += 1
        etapa_anterior = self.etapa_actual
        
        # Actualizar la etapa actual
        if self.indice_etapa_actual < len(etapas):
            self.etapa_actual = etapas[self.indice_etapa_actual]
            
            # Iniciar timestamp de nueva etapa
            self.timestamps_etapas[self.etapa_actual] = {
                'fecha_inicio': timezone.now().isoformat(),
                'fecha_fin': None,
                'duracion_real': None,
                'duracion_estimada': self.DURACIONES_ESTIMADAS.get(self.etapa_actual, 30),
                'observaciones': '',
                'usuario_inicio': str(usuario) if usuario else None,
            }
            
            # ✅ SINCRONIZAR CON PACIENTE (etapa intermedia)
            self._sincronizar_etapa_paciente()
            
        else:
            # ✅ CORRECCIÓN CRÍTICA: Si llegamos al final, completar la ruta
            self.estado = 'COMPLETADA'
            self.fecha_fin_real = timezone.now()
            self.etapa_actual = None  # Ya no hay etapa actual
            
            # ✅ LIMPIAR ETAPA DEL PACIENTE AL COMPLETAR
            self.paciente.etapa_actual = None
            self.paciente.estado_actual = 'ALTA_COMPLETA'
            self.paciente.save(update_fields=['etapa_actual', 'estado_actual', 'fecha_actualizacion'])
        
        # Recalcular progreso
        self.calcular_progreso()
        
        # Registrar en historial
        self._agregar_al_historial('AVANZAR', self.etapa_actual, usuario, {
            'desde': etapa_anterior,
            'hacia': self.etapa_actual if self.etapa_actual else 'COMPLETADA',
            'observaciones': observaciones,
        })
        
        self.save()
        return True
    
    def retroceder_etapa(self, motivo='', usuario=None):
        """
        ✅ CORREGIDO: Retrocede a la etapa anterior SELECCIONADA
        """
        # ✅ USAR ETAPAS SELECCIONADAS
        etapas = self.etapas_seleccionadas if self.etapas_seleccionadas else [key for key, _ in self.ETAPAS_CHOICES]
        
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
        self.etapa_actual = etapas[self.indice_etapa_actual]  # ← CORRECCIÓN AQUÍ
        
        # Registrar en historial
        self._agregar_al_historial('RETROCEDER', self.etapa_actual, usuario, {
            'desde': etapa_anterior,
            'hacia': self.etapa_actual,
            'motivo': motivo,
        })
        
        # ✅ SINCRONIZAR CON PACIENTE
        self._sincronizar_etapa_paciente()
        
        self.calcular_progreso()
        self.save()
        return True
    
    def pausar_ruta(self, motivo='', usuario=None):
        """
        ✅ ACTUALIZADO: Pausa la ruta y actualiza estado del paciente
        """
        self.estado = 'PAUSADA'
        self.esta_pausado = True
        self.motivo_pausa = motivo
        self.metadatos_adicionales['fecha_pausa'] = timezone.now().isoformat()
        
        # ✅ SINCRONIZAR ESTADO PAUSADO CON PACIENTE
        self._sincronizar_etapa_paciente()

        
        self._agregar_al_historial('PAUSAR', self.etapa_actual, usuario, {
            'motivo': motivo
        })
        
        self.save()
    
    def reanudar_ruta(self, usuario=None):
        """
        ✅ ACTUALIZADO: Reanuda la ruta y actualiza estado del paciente
        """
        if self.estado == 'PAUSADA':
            self.estado = 'EN_PROGRESO'
            self.esta_pausado = False
            self.motivo_pausa = ''
            self.metadatos_adicionales['fecha_reanudacion'] = timezone.now().isoformat()
            
            # ✅ SINCRONIZAR CON PACIENTE (restaura estado ACTIVO)
            self._sincronizar_etapa_paciente()
            
            self._agregar_al_historial('REANUDAR', self.etapa_actual, usuario)
            
            self.save()
            return True
        return False
    
    # ============================================
    # MÉTODOS DE CÁLCULO Y ANÁLISIS
    # ============================================
    
    def calcular_progreso(self):
        """Calcula el porcentaje de progreso basado en TODAS las etapas"""
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
        """
        ✅ CORREGIDO: Timeline que respeta el orden fijo de etapas
        """
        timeline = []
        
        # ✅ ORDEN FIJO de todas las etapas del sistema
        todas_etapas = [key for key, _ in self.ETAPAS_CHOICES]
        
        # Asegurar que son listas
        if not isinstance(self.etapas_completadas, list):
            self.etapas_completadas = []
        
        if not isinstance(self.etapas_seleccionadas, list):
            self.etapas_seleccionadas = []
        
        # ✅ NUEVO: Encontrar el índice de la primera etapa seleccionada
        indice_primera_seleccionada = float('inf')
        if self.etapas_seleccionadas:
            indice_primera_seleccionada = min(
                todas_etapas.index(etapa) 
                for etapa in self.etapas_seleccionadas
            )
        
        for i, etapa_key in enumerate(todas_etapas):
            etapa_label = dict(self.ETAPAS_CHOICES).get(etapa_key, etapa_key)
            
            # ✅ LÓGICA CORREGIDA: Determinar estado basado en posición
            if i < indice_primera_seleccionada:
                # Etapas anteriores a la primera seleccionada
                estado = 'COMPLETADA'
            elif etapa_key in self.etapas_completadas:
                # Etapas explícitamente completadas
                estado = 'COMPLETADA'
            elif etapa_key == self.etapa_actual and self.estado == 'EN_PROGRESO':
                # Etapa actual en proceso
                estado = 'EN_CURSO'
            elif etapa_key in self.etapas_seleccionadas:
                # Etapa seleccionada pero pendiente
                if i > todas_etapas.index(self.etapa_actual):
                    estado = 'PENDIENTE'
                else:
                    estado = 'COMPLETADA'
            else:
                # Etapa no seleccionada
                estado = 'NO_REQUERIDA'
            
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
                'es_requerida': etapa_key in self.etapas_seleccionadas if self.etapas_seleccionadas else True,
                'auto_completada': etapa_data.get('auto_completada', False),
            })
        
        return timeline

    def obtener_info_timeline(self):
        """Retorna información estructurada para el timeline (método legacy)"""
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