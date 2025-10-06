from rest_framework import serializers
from .models import RutaClinica, EtapaRuta
from pacientes.serializers import PacienteListSerializer


class EtapaRutaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para EtapaRuta.
    Incluye información calculada del progreso y estado.
    """
    tipo_etapa_display = serializers.CharField(
        source='get_tipo_etapa_display',
        read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    tiempo_transcurrido = serializers.SerializerMethodField()
    porcentaje_avance = serializers.SerializerMethodField()
    tiene_retraso = serializers.SerializerMethodField()
    
    class Meta:
        model = EtapaRuta
        fields = [
            'id',
            'ruta_clinica',
            'nombre',
            'tipo_etapa',
            'tipo_etapa_display',
            'orden',
            'fecha_inicio',
            'fecha_fin',
            'duracion_estimada',
            'duracion_real',
            'estado',
            'estado_display',
            'es_estatico',
            'motivo_pausa',
            'descripcion',
            'configuracion_etapa',
            'fecha_actualizacion',
            'tiempo_transcurrido',
            'porcentaje_avance',
            'tiene_retraso',
        ]
        read_only_fields = ['id', 'duracion_real', 'fecha_actualizacion']
    
    def get_tiempo_transcurrido(self, obj):
        """Retorna el tiempo transcurrido de la etapa"""
        tiempo = obj.calcular_tiempo_transcurrido()
        if tiempo:
            return int(tiempo.total_seconds() / 60)  # En minutos
        return None
    
    def get_porcentaje_avance(self, obj):
        """Retorna el porcentaje de avance de la etapa"""
        return round(obj.obtener_porcentaje_avance(), 2)
    
    def get_tiene_retraso(self, obj):
        """Indica si la etapa tiene retraso"""
        return obj.detectar_retraso()


class EtapaRutaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar etapas.
    Usado en el timeline horizontal.
    """
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    tipo_etapa_display = serializers.CharField(
        source='get_tipo_etapa_display',
        read_only=True
    )
    porcentaje_avance = serializers.SerializerMethodField()
    
    class Meta:
        model = EtapaRuta
        fields = [
            'id',
            'nombre',
            'orden',
            'tipo_etapa',
            'tipo_etapa_display',
            'estado',
            'estado_display',
            'es_estatico',
            'duracion_estimada',
            'duracion_real',
            'porcentaje_avance',
        ]
    
    def get_porcentaje_avance(self, obj):
        return round(obj.obtener_porcentaje_avance(), 2)


class RutaClinicaSerializer(serializers.ModelSerializer):
    """
    Serializer completo para RutaClinica.
    Incluye las etapas anidadas para el timeline.
    """
    paciente = PacienteListSerializer(read_only=True)
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('pacientes.models', fromlist=['Paciente']).Paciente.objects.all(),
        source='paciente',
        write_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    etapas = EtapaRutaListSerializer(many=True, read_only=True)
    tiempo_total_real = serializers.SerializerMethodField()
    tiempo_total_estimado = serializers.SerializerMethodField()
    etapa_actual = serializers.SerializerMethodField()
    proxima_etapa = serializers.SerializerMethodField()
    tiene_retrasos = serializers.SerializerMethodField()
    
    class Meta:
        model = RutaClinica
        fields = [
            'id',
            'paciente',
            'paciente_id',
            'fecha_inicio',
            'fecha_estimada_fin',
            'fecha_fin_real',
            'porcentaje_completado',
            'estado',
            'estado_display',
            'metadatos_adicionales',
            'fecha_actualizacion',
            'etapas',
            'tiempo_total_real',
            'tiempo_total_estimado',
            'etapa_actual',
            'proxima_etapa',
            'tiene_retrasos',
        ]
        read_only_fields = [
            'id',
            'porcentaje_completado',
            'fecha_actualizacion',
            'fecha_fin_real'
        ]
    
    def get_tiempo_total_real(self, obj):
        """Retorna el tiempo real transcurrido en minutos"""
        tiempo = obj.obtener_tiempo_total_real()
        return int(tiempo.total_seconds() / 60)
    
    def get_tiempo_total_estimado(self, obj):
        """Retorna el tiempo estimado total en minutos"""
        tiempo = obj.obtener_tiempo_total_estimado()
        return int(tiempo.total_seconds() / 60)
    
    def get_etapa_actual(self, obj):
        """Retorna la etapa actualmente en proceso"""
        etapa = obj.obtener_etapa_actual()
        if etapa:
            return EtapaRutaListSerializer(etapa).data
        return None
    
    def get_proxima_etapa(self, obj):
        """Retorna la próxima etapa pendiente"""
        etapa = obj.obtener_proxima_etapa()
        if etapa:
            return EtapaRutaListSerializer(etapa).data
        return None
    
    def get_tiene_retrasos(self, obj):
        """Indica si hay etapas retrasadas"""
        return len(obj.detectar_retrasos()) > 0


class RutaClinicaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar rutas clínicas.
    """
    paciente_hash = serializers.CharField(
        source='paciente.identificador_hash',
        read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    
    class Meta:
        model = RutaClinica
        fields = [
            'id',
            'paciente_hash',
            'fecha_inicio',
            'porcentaje_completado',
            'estado',
            'estado_display',
        ]


class RutaClinicaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear una ruta clínica con sus etapas.
    """
    etapas = EtapaRutaSerializer(many=True, write_only=True)
    
    class Meta:
        model = RutaClinica
        fields = [
            'paciente',
            'fecha_estimada_fin',
            'etapas',
        ]
    
    def create(self, validated_data):
        """Crea la ruta clínica con sus etapas"""
        etapas_data = validated_data.pop('etapas', [])
        ruta = RutaClinica.objects.create(**validated_data)
        
        # Crear las etapas
        for etapa_data in etapas_data:
            EtapaRuta.objects.create(ruta_clinica=ruta, **etapa_data)
        
        # Calcular progreso inicial
        ruta.calcular_progreso()
        
        return ruta


class TimelineSerializer(serializers.Serializer):
    """
    Serializer especializado para el timeline del paciente.
    Optimizado para la visualización del timeline horizontal.
    """
    paciente = PacienteListSerializer(read_only=True)
    ruta_clinica = RutaClinicaSerializer(read_only=True)
    progreso_general = serializers.FloatField(read_only=True)
    etapas_completadas = serializers.IntegerField(read_only=True)
    etapas_totales = serializers.IntegerField(read_only=True)
    tiempo_transcurrido_minutos = serializers.IntegerField(read_only=True)
    estado_actual = serializers.CharField(read_only=True)