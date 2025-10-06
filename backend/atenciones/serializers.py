from rest_framework import serializers
from .models import Medico, Atencion


class MedicoSerializer(serializers.ModelSerializer):
    """Serializer completo para Medico"""
    especialidad_principal_display = serializers.CharField(
        source='get_especialidad_principal_display',
        read_only=True
    )
    nombre_completo = serializers.CharField(read_only=True)
    tiempo_promedio = serializers.SerializerMethodField()
    
    class Meta:
        model = Medico
        fields = '__all__'
    
    def get_tiempo_promedio(self, obj):
        return round(obj.calcular_tiempo_promedio_atencion(), 2)


class AtencionSerializer(serializers.ModelSerializer):
    """Serializer completo para Atencion"""
    tipo_atencion_display = serializers.CharField(source='get_tipo_atencion_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    retraso = serializers.SerializerMethodField()
    tiempo_transcurrido = serializers.SerializerMethodField()
    esta_retrasada = serializers.SerializerMethodField()
    
    class Meta:
        model = Atencion
        fields = '__all__'
        read_only_fields = ['duracion_real', 'inicio_cronometro', 'fin_cronometro']
    
    def get_retraso(self, obj):
        return obj.calcular_retraso()
    
    def get_tiempo_transcurrido(self, obj):
        tiempo = obj.obtener_tiempo_transcurrido()
        if tiempo:
            return int(tiempo.total_seconds() / 60)
        return None
    
    def get_esta_retrasada(self, obj):
        return obj.is_retrasada()


class AtencionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar atenciones"""
    paciente_hash = serializers.CharField(source='paciente.identificador_hash', read_only=True)
    medico_nombre = serializers.CharField(source='medico.nombre_completo', read_only=True)
    box_numero = serializers.CharField(source='box.numero', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Atencion
        fields = [
            'id', 'paciente_hash', 'medico_nombre', 'box_numero',
            'fecha_hora_inicio', 'tipo_atencion', 'estado', 'estado_display',
            'duracion_planificada', 'duracion_real'
        ]