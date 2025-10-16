# backend/rutas_clinicas/serializers.py - VERSIÓN MEJORADA
from rest_framework import serializers
from .models import RutaClinica
from pacientes.serializers import PacienteListSerializer


class RutaClinicaSerializer(serializers.ModelSerializer):
    """Serializer completo mejorado con detección de retrasos"""
    paciente = PacienteListSerializer(read_only=True)
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('pacientes.models', fromlist=['Paciente']).Paciente.objects.all(),
        source='paciente',
        write_only=True
    )
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    etapa_actual_display = serializers.CharField(source='get_etapa_actual_display', read_only=True)
    
    # Campo de selección múltiple para etapas
    etapas_seleccionadas = serializers.MultipleChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        help_text="Seleccione las etapas del proceso clínico"
    )
    
    # Información calculada
    tiempo_total_real = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    etapa_siguiente = serializers.SerializerMethodField()
    total_etapas = serializers.SerializerMethodField()
    etapas_restantes = serializers.SerializerMethodField()
    retrasos_detectados = serializers.SerializerMethodField()  # NUEVO
    
    # Choices disponibles
    etapas_disponibles = serializers.SerializerMethodField()
    
    # Estado del paciente sincronizado
    estado_paciente = serializers.CharField(
        source='paciente.estado_actual_display',
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
            'estado_paciente',  # NUEVO
            'esta_pausado',
            'motivo_pausa',
            'metadatos_adicionales',
            'historial_cambios',  # NUEVO
            'fecha_actualizacion',
            'tiempo_total_real',
            'timeline',
            'etapa_siguiente',
            'total_etapas',
            'etapas_restantes',
            'retrasos_detectados',  # NUEVO
        ]
        read_only_fields = [
            'id',
            'etapa_actual',
            'indice_etapa_actual',
            'etapas_completadas',
            'timestamps_etapas',
            'porcentaje_completado',
            'fecha_actualizacion',
            'fecha_fin_real',
            'esta_pausado',
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
        """Timeline estructurado con información de retrasos"""
        return obj.obtener_info_timeline()
    
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
        return len(obj.etapas_seleccionadas)
    
    def get_etapas_restantes(self, obj):
        return len(obj.etapas_seleccionadas) - len(obj.etapas_completadas)
    
    def get_retrasos_detectados(self, obj):
        """NUEVO: Detecta retrasos en las etapas"""
        return obj.detectar_retrasos()


class RutaClinicaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado mejorado"""
    paciente_hash = serializers.CharField(source='paciente.identificador_hash', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    paciente_edad = serializers.IntegerField(source='paciente.edad', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    etapa_actual_display = serializers.CharField(source='get_etapa_actual_display', read_only=True)
    progreso_info = serializers.SerializerMethodField()
    tiene_retrasos = serializers.SerializerMethodField()  # NUEVO
    estado_paciente = serializers.CharField(source='paciente.estado_actual_display', read_only=True)
    
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
            'estado_paciente',  # NUEVO
            'esta_pausado',
            'progreso_info',
            'tiene_retrasos',  # NUEVO
        ]
    
    def get_paciente_nombre(self, obj):
        """Obtiene el nombre del paciente si existe en metadatos"""
        return obj.paciente.metadatos_adicionales.get('nombre', f'Paciente {obj.paciente.identificador_hash[:8]}')
    
    def get_progreso_info(self, obj):
        return {
            'total': len(obj.etapas_seleccionadas),
            'completadas': len(obj.etapas_completadas),
            'porcentaje': obj.porcentaje_completado,
        }
    
    def get_tiene_retrasos(self, obj):
        """NUEVO: Indica si tiene retrasos"""
        return len(obj.detectar_retrasos()) > 0


class RutaClinicaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear rutas con validaciones mejoradas"""
    
    etapas_seleccionadas = serializers.MultipleChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        help_text="Seleccione las etapas del proceso clínico"
    )
    
    class Meta:
        model = RutaClinica
        fields = [
            'paciente',
            'etapas_seleccionadas',
            'fecha_estimada_fin',
            'metadatos_adicionales',
        ]
    
    def validate_etapas_seleccionadas(self, value):
        """Valida etapas seleccionadas"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Debe seleccionar al menos una etapa.")
        
        if not isinstance(value, list):
            value = list(value)
        
        return value
    
    def validate_paciente(self, value):
        """Valida que el paciente no tenga ya una ruta activa"""
        rutas_activas = RutaClinica.objects.filter(
            paciente=value,
            estado__in=['INICIADA', 'EN_PROGRESO']
        )
        
        if rutas_activas.exists():
            raise serializers.ValidationError(
                "Este paciente ya tiene una ruta clínica activa. "
                "Debe completarla o cancelarla antes de crear una nueva."
            )
        
        return value
    
    def create(self, validated_data):
        """Crea la ruta y calcula progreso inicial"""
        ruta = RutaClinica.objects.create(**validated_data)
        ruta.calcular_progreso()
        return ruta


class TimelineSerializer(serializers.Serializer):
    """Serializer mejorado para el timeline con retrasos"""
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
    retrasos = serializers.ListField()  # NUEVO
    
    def get_paciente(self, obj):
        """Información del paciente"""
        return {
            'id': str(obj['paciente'].id),
            'identificador_hash': obj['paciente'].identificador_hash,
            'nombre': obj['paciente'].metadatos_adicionales.get('nombre', 'N/A'),
            'edad': obj['paciente'].edad,
            'genero': obj['paciente'].get_genero_display(),
            'estado_actual': obj['paciente'].get_estado_actual_display(),
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
        }


class RutaAccionSerializer(serializers.Serializer):
    """Serializer para acciones (pausar, observaciones, etc)"""
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
