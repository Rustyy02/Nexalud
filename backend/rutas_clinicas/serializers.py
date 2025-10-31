# backend/rutas_clinicas/serializers.py - VERSIÓN CORREGIDA
from rest_framework import serializers
from .models import RutaClinica
from pacientes.serializers import PacienteListSerializer


class RutaClinicaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer corregido para crear rutas con validaciones mejoradas
    """
    
    etapas_seleccionadas = serializers.MultipleChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        help_text="✓ Seleccione las etapas del proceso clínico (se ordenarán automáticamente)",
        required=False,
        style={'base_template': 'checkbox_multiple.html'}
    )
    
    etapa_inicial = serializers.ChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        required=False,
        allow_null=True,
        help_text="Etapa inicial de la ruta (opcional). Si el paciente ya completó etapas previas, indique desde dónde iniciar."
    )
    
    class Meta:
        model = RutaClinica
        fields = [
            'paciente',
            'etapas_seleccionadas',
            'etapa_inicial',
            'fecha_estimada_fin',
            'metadatos_adicionales',
        ]
    
    def validate_etapas_seleccionadas(self, value):
        """Valida y ordena las etapas seleccionadas"""
        if not value or len(value) == 0:
            # Si no hay etapas, usar todas
            return [key for key, _ in RutaClinica.ETAPAS_CHOICES]
        
        if not isinstance(value, list):
            value = list(value)
        
        # Ordenar según el orden fijo de ETAPAS_CHOICES
        todas_etapas = [key for key, _ in RutaClinica.ETAPAS_CHOICES]
        value_ordenado = sorted(
            value,
            key=lambda x: todas_etapas.index(x) if x in todas_etapas else 999
        )
        
        return value_ordenado
    
    def validate(self, attrs):
        """Validación cruzada"""
        etapa_inicial = attrs.get('etapa_inicial')
        etapas_seleccionadas = attrs.get('etapas_seleccionadas', [])
        
        # Si no hay etapas seleccionadas, usar todas
        if not etapas_seleccionadas:
            todas_etapas = [key for key, _ in RutaClinica.ETAPAS_CHOICES]
            attrs['etapas_seleccionadas'] = todas_etapas
            etapas_seleccionadas = todas_etapas
        
        # Si se especifica etapa inicial, asegurar que esté en las seleccionadas
        if etapa_inicial:
            if etapa_inicial not in etapas_seleccionadas:
                # Añadir la etapa inicial a las seleccionadas
                etapas_seleccionadas.append(etapa_inicial)
                # Re-ordenar
                todas_etapas = [key for key, _ in RutaClinica.ETAPAS_CHOICES]
                etapas_seleccionadas = sorted(
                    etapas_seleccionadas,
                    key=lambda x: todas_etapas.index(x) if x in todas_etapas else 999
                )
                attrs['etapas_seleccionadas'] = etapas_seleccionadas
        
        return attrs
    
    def validate_paciente(self, value):
        """Valida que el paciente no tenga ya una ruta activa"""
        rutas_activas = RutaClinica.objects.filter(
            paciente=value,
            estado__in=['INICIADA', 'EN_PROGRESO', 'PAUSADA']
        )
        
        if rutas_activas.exists():
            raise serializers.ValidationError(
                "Este paciente ya tiene una ruta clínica activa. "
                "Debe completarla o cancelarla antes de crear una nueva."
            )
        
        return value
    
    def create(self, validated_data):
        """Crea la ruta con etapa inicial personalizada si se proporciona"""
        etapa_inicial = validated_data.pop('etapa_inicial', None)
        
        # Crear la ruta
        ruta = RutaClinica.objects.create(**validated_data)
        
        # Iniciar la ruta con la etapa especificada
        ruta.iniciar_ruta(etapa_inicial=etapa_inicial)
        
        return ruta


class RutaClinicaSerializer(serializers.ModelSerializer):
    """Serializer completo con todas las validaciones"""
    paciente = PacienteListSerializer(read_only=True)
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('pacientes.models', fromlist=['Paciente']).Paciente.objects.all(),
        source='paciente',
        write_only=True
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    etapa_actual_display = serializers.CharField(source='get_etapa_actual_display', read_only=True)
    
    # Información calculada
    tiempo_total_real = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    etapa_siguiente = serializers.SerializerMethodField()
    total_etapas = serializers.SerializerMethodField()
    etapas_restantes = serializers.SerializerMethodField()
    retrasos_detectados = serializers.SerializerMethodField()
    puede_avanzar = serializers.SerializerMethodField()
    puede_retroceder = serializers.SerializerMethodField()
    
    # Choices disponibles
    etapas_disponibles = serializers.SerializerMethodField()
    
    # Estado del paciente sincronizado
    estado_paciente = serializers.CharField(
        source='paciente.estado_actual_display',
        read_only=True
    )
    etapa_paciente = serializers.CharField(
        source='paciente.etapa_actual_display',
        read_only=True
    )
    
    class Meta:
        model = RutaClinica
        fields = [
            'id',
            'paciente',
            'paciente_id',
            'etapas_seleccionadas',
            'etapas_disponibles',
            'etapa_actual',
            'etapa_actual_display',
            'indice_etapa_actual',
            'etapas_completadas',
            'timestamps_etapas',
            'fecha_inicio',
            'fecha_estimada_fin',
            'fecha_fin_real',
            'porcentaje_completado',
            'estado',
            'estado_display',
            'estado_paciente',
            'etapa_paciente',
            'esta_pausado',
            'motivo_pausa',
            'metadatos_adicionales',
            'historial_cambios',
            'fecha_actualizacion',
            'tiempo_total_real',
            'timeline',
            'etapa_siguiente',
            'total_etapas',
            'etapas_restantes',
            'retrasos_detectados',
            'puede_avanzar',
            'puede_retroceder',
        ]
        read_only_fields = [
            'id',
            'indice_etapa_actual',
            'etapas_completadas',
            'timestamps_etapas',
            'porcentaje_completado',
            'fecha_actualizacion',
            'fecha_fin_real',
            'historial_cambios',
        ]
    
    def get_etapas_disponibles(self, obj):
        """Retorna etapas disponibles con duraciones"""
        return [
            {
                'key': key,
                'label': label,
                'duracion_estimada': RutaClinica.DURACIONES_ESTIMADAS.get(key, 30)
            }
            for key, label in RutaClinica.ETAPAS_CHOICES
        ]
    
    def get_tiempo_total_real(self, obj):
        """Tiempo real transcurrido"""
        tiempo = obj.obtener_tiempo_total_real()
        minutos = int(tiempo.total_seconds() / 60)
        horas = int(tiempo.total_seconds() / 3600)
        return {
            'minutos': minutos,
            'horas': horas,
            'formateado': f"{horas}h {minutos % 60}m"
        }
    
    def get_timeline(self, obj):
        """Timeline estructurado con todas las etapas"""
        return obj.obtener_timeline_completo()
    
    def get_etapa_siguiente(self, obj):
        """Siguiente etapa"""
        siguiente = obj.obtener_etapa_siguiente()
        if siguiente:
            label = dict(RutaClinica.ETAPAS_CHOICES).get(siguiente, siguiente)
            return {
                'key': siguiente,
                'label': label,
                'duracion_estimada': RutaClinica.DURACIONES_ESTIMADAS.get(siguiente, 30)
            }
        return None
    
    def get_total_etapas(self, obj):
        """Total de etapas seleccionadas"""
        return len(obj.etapas_seleccionadas) if obj.etapas_seleccionadas else 0
    
    def get_etapas_restantes(self, obj):
        """Etapas restantes"""
        if not obj.etapas_seleccionadas:
            return 0
        
        completadas = len([e for e in obj.etapas_completadas if e in obj.etapas_seleccionadas])
        return len(obj.etapas_seleccionadas) - completadas
    
    def get_retrasos_detectados(self, obj):
        """Detecta retrasos en las etapas"""
        try:
            return obj.detectar_retrasos()
        except Exception:
            return []
    
    def get_puede_avanzar(self, obj):
        """Indica si se puede avanzar a la siguiente etapa"""
        if obj.estado != 'EN_PROGRESO':
            return False
        
        if not obj.etapa_actual:
            return False
        
        etapas = obj.etapas_seleccionadas if obj.etapas_seleccionadas else [key for key, _ in RutaClinica.ETAPAS_CHOICES]
        return obj.indice_etapa_actual < len(etapas)
    
    def get_puede_retroceder(self, obj):
        """Indica si se puede retroceder a la etapa anterior"""
        # Se puede retroceder si:
        # 1. Está completada (para reactivar)
        # 2. Está en progreso y no es la primera etapa
        
        if obj.estado == 'COMPLETADA':
            return True
        
        if obj.estado == 'EN_PROGRESO':
            return obj.indice_etapa_actual > 0
        
        return False


class RutaClinicaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    paciente_hash = serializers.CharField(source='paciente.identificador_hash', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    paciente_edad = serializers.IntegerField(source='paciente.edad', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    etapa_actual_display = serializers.CharField(source='get_etapa_actual_display', read_only=True)
    progreso_info = serializers.SerializerMethodField()
    tiene_retrasos = serializers.SerializerMethodField()
    estado_paciente = serializers.CharField(source='paciente.estado_actual_display', read_only=True)
    etapa_paciente = serializers.CharField(source='paciente.etapa_actual_display', read_only=True)
    
    class Meta:
        model = RutaClinica
        fields = [
            'id',
            'paciente_hash',
            'paciente_nombre',
            'paciente_edad',
            'etapa_actual',
            'etapa_actual_display',
            'fecha_inicio',
            'porcentaje_completado',
            'estado',
            'estado_display',
            'estado_paciente',
            'etapa_paciente',
            'esta_pausado',
            'progreso_info',
            'tiene_retrasos',
        ]
    
    def get_paciente_nombre(self, obj):
        """Obtiene el nombre del paciente con validación robusta"""
        metadatos = obj.paciente.metadatos_adicionales
        
        if not isinstance(metadatos, dict):
            return f'Paciente {obj.paciente.identificador_hash[:8]}'
        
        return metadatos.get('nombre', f'Paciente {obj.paciente.identificador_hash[:8]}')
    
    def get_progreso_info(self, obj):
        """Información de progreso"""
        total = len(obj.etapas_seleccionadas) if obj.etapas_seleccionadas else 0
        completadas = len([e for e in obj.etapas_completadas if e in obj.etapas_seleccionadas]) if obj.etapas_seleccionadas else 0
        
        return {
            'total': total,
            'completadas': completadas,
            'porcentaje': obj.porcentaje_completado,
        }
    
    def get_tiene_retrasos(self, obj):
        """Indica si tiene retrasos"""
        try:
            retrasos = obj.detectar_retrasos()
            return len(retrasos) > 0
        except Exception:
            return False


class TimelineSerializer(serializers.Serializer):
    """Serializer para el timeline completo"""
    paciente = serializers.SerializerMethodField()
    ruta_clinica = serializers.SerializerMethodField()
    timeline = serializers.ListField()
    progreso_general = serializers.FloatField()
    etapas_completadas = serializers.IntegerField()
    etapas_totales = serializers.IntegerField()
    tiempo_transcurrido_minutos = serializers.IntegerField()
    estado_actual = serializers.CharField()
    esta_pausado = serializers.BooleanField()
    alertas = serializers.ListField()
    retrasos = serializers.ListField()
    puede_avanzar = serializers.BooleanField()
    puede_retroceder = serializers.BooleanField()
    
    def get_paciente(self, obj):
        """Información del paciente"""
        metadatos = obj['paciente'].metadatos_adicionales
        
        if isinstance(metadatos, dict):
            nombre = metadatos.get('nombre', 'N/A')
        else:
            nombre = f'Paciente {obj["paciente"].identificador_hash[:8]}'
        
        return {
            'id': str(obj['paciente'].id),
            'identificador_hash': obj['paciente'].identificador_hash,
            'nombre': nombre,
            'edad': obj['paciente'].edad,
            'genero': obj['paciente'].get_genero_display(),
            'estado_actual': obj['paciente'].get_estado_actual_display(),
            'etapa_actual': obj['paciente'].get_etapa_actual_display() if obj['paciente'].etapa_actual else None,
            'nivel_urgencia': obj['paciente'].get_nivel_urgencia_display(),
        }
    
    def get_ruta_clinica(self, obj):
        """Información de la ruta"""
        return {
            'id': str(obj['ruta_clinica'].id),
            'estado': obj['ruta_clinica'].estado,
            'estado_display': obj['ruta_clinica'].get_estado_display(),
            'porcentaje_completado': obj['ruta_clinica'].porcentaje_completado,
            'fecha_inicio': obj['ruta_clinica'].fecha_inicio,
            'fecha_estimada_fin': obj['ruta_clinica'].fecha_estimada_fin,
            'fecha_fin_real': obj['ruta_clinica'].fecha_fin_real,
            'etapa_actual': obj['ruta_clinica'].etapa_actual,
            'etapa_actual_display': obj['ruta_clinica'].get_etapa_actual_display(),
            'indice_etapa_actual': obj['ruta_clinica'].indice_etapa_actual,
            'puede_avanzar': obj.get('puede_avanzar', False),
            'puede_retroceder': obj.get('puede_retroceder', False),
        }


class RutaAccionSerializer(serializers.Serializer):
    """Serializer para acciones sobre la ruta"""
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=500)
    observaciones = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class HistorialCambiosSerializer(serializers.Serializer):
    """Serializer para el historial de cambios"""
    timestamp = serializers.DateTimeField()
    accion = serializers.CharField()
    etapa = serializers.CharField(allow_null=True)
    usuario = serializers.CharField()
    desde = serializers.CharField(required=False)
    hacia = serializers.CharField(required=False)
    motivo = serializers.CharField(required=False)
    observaciones = serializers.CharField(required=False)