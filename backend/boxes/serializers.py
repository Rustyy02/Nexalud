
from rest_framework import serializers
from .models import Box


class BoxSerializer(serializers.ModelSerializer):
    """Serializer completo para Box"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    disponibilidad = serializers.SerializerMethodField()
    ocupacion_actual = serializers.SerializerMethodField()
    porcentaje_ocupacion_hoy = serializers.SerializerMethodField()
    
    class Meta:
        model = Box
        fields = '__all__'
        read_only_fields = ['id', 'tiempo_ocupado_hoy', 'ultima_ocupacion', 'ultima_liberacion']
    
    def get_disponibilidad(self, obj):
        return obj.obtener_disponibilidad()
    
    def get_ocupacion_actual(self, obj):
        return obj.obtener_ocupacion_actual()
    
    def get_porcentaje_ocupacion_hoy(self, obj):
        return round(obj.calcular_tiempo_ocupacion_hoy(), 2)


class BoxListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para lista de boxes"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    disponible = serializers.SerializerMethodField()
    
    class Meta:
        model = Box
        fields = ['id', 'numero', 'nombre', 'especialidad', 'estado', 'estado_display', 'disponible', 'activo']
    
    def get_disponible(self, obj):
        return obj.obtener_disponibilidad()