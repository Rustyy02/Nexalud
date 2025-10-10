# backend/rutas_clinicas/serializers.py
from rest_framework import serializers
from .models import RutaClinica
from pacientes.serializers import PacienteListSerializer


class RutaClinicaSerializer(serializers.ModelSerializer):
    """Serializer completo para RutaClinica"""
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
    
    # Choices disponibles para el frontend
    etapas_disponibles = serializers.SerializerMethodField()
    
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
            'esta_pausado',
            'motivo_pausa',
            'metadatos_adicionales',
            'fecha_actualizacion',
            'tiempo_total_real',
            'timeline',
            'etapa_siguiente',
            'total_etapas',
            'etapas_restantes',
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
        ]
    
    def get_etapas_disponibles(self, obj):
        """Retorna las opciones de etapas disponibles"""
        return [
            {'key': key, 'label': label}
            for key, label in RutaClinica.ETAPAS_CHOICES
        ]
    
    def get_tiempo_total_real(self, obj):
        """Retorna el tiempo real transcurrido"""
        tiempo = obj.obtener_tiempo_total_real()
        minutos = int(tiempo.total_seconds() / 60)
        horas = int(tiempo.total_seconds() / 3600)
        return {
            'minutos': minutos,
            'horas': horas,
            'formateado': f"{horas}h {minutos % 60}m"
        }
    
    def get_timeline(self, obj):
        """Retorna el timeline estructurado"""
        return obj.obtener_info_timeline()
    
    def get_etapa_siguiente(self, obj):
        """Retorna la siguiente etapa"""
        siguiente = obj.obtener_etapa_siguiente()
        if siguiente:
            label = dict(RutaClinica.ETAPAS_CHOICES).get(siguiente, siguiente)
            return {
                'key': siguiente,
                'label': label
            }
        return None
    
    def get_total_etapas(self, obj):
        """Total de etapas seleccionadas"""
        return len(obj.etapas_seleccionadas)
    
    def get_etapas_restantes(self, obj):
        """Cantidad de etapas restantes"""
        return len(obj.etapas_seleccionadas) - len(obj.etapas_completadas)


class RutaClinicaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar rutas"""
    paciente_hash = serializers.CharField(source='paciente.identificador_hash', read_only=True)
    paciente_edad = serializers.IntegerField(source='paciente.edad', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    etapa_actual_display = serializers.CharField(source='get_etapa_actual_display', read_only=True)
    progreso_info = serializers.SerializerMethodField()
    
    class Meta:
        model = RutaClinica
        fields = [
            'id',
            'paciente_hash',
            'paciente_edad',
            'etapa_actual',
            'etapa_actual_display',
            'fecha_inicio',
            'porcentaje_completado',
            'estado',
            'estado_display',
            'esta_pausado',
            'progreso_info',
        ]
    
    def get_progreso_info(self, obj):
        """Información resumida del progreso"""
        return {
            'total': len(obj.etapas_seleccionadas),
            'completadas': len(obj.etapas_completadas),
            'porcentaje': obj.porcentaje_completado,
        }


class RutaClinicaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear una ruta clínica"""
    
    # Campo personalizado para selección múltiple
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
        """Valida que se hayan seleccionado etapas válidas"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Debe seleccionar al menos una etapa.")
        
        # Convertir a lista si no lo es
        if not isinstance(value, list):
            value = list(value)
        
        return value
    
    def create(self, validated_data):
        """Crea la ruta clínica"""
        ruta = RutaClinica.objects.create(**validated_data)
        # Calcular progreso inicial
        ruta.calcular_progreso()
        return ruta


class TimelineSerializer(serializers.Serializer):
    """Serializer especializado para el timeline horizontal"""
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
    
    def get_paciente(self, obj):
        """Información del paciente"""
        return {
            'id': str(obj['paciente'].id),
            'identificador_hash': obj['paciente'].identificador_hash,
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
    """Serializer para acciones sobre la ruta (pausar, reanudar, etc)"""
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=500)