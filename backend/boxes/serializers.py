from rest_framework import serializers
from .models import Box


class BoxSerializer(serializers.ModelSerializer):
    """Serializer completo para Box con información calculada"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    disponibilidad = serializers.SerializerMethodField()
    ocupacion_actual = serializers.SerializerMethodField()
    porcentaje_ocupacion_hoy = serializers.SerializerMethodField()
    tiempo_ocupado_formateado = serializers.SerializerMethodField()
    
    class Meta:
        model = Box
        fields = [
            'id',
            'numero',
            'nombre',
            'especialidad',
            'especialidad_display',
            'estado',
            'estado_display',
            'capacidad_maxima',
            'equipamiento',
            'horarios_disponibles',
            'activo',
            'fecha_creacion',
            'fecha_actualizacion',
            'tiempo_ocupado_hoy',
            'tiempo_ocupado_formateado',
            'ultima_ocupacion',
            'ultima_liberacion',
            'disponibilidad',
            'ocupacion_actual',
            'porcentaje_ocupacion_hoy',
        ]
        read_only_fields = [
            'id',
            'tiempo_ocupado_hoy',
            'ultima_ocupacion',
            'ultima_liberacion',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
    
    def get_disponibilidad(self, obj):
        """Indica si el box está disponible"""
        return obj.obtener_disponibilidad()
    
    def get_ocupacion_actual(self, obj):
        """Información de ocupación actual"""
        ocupacion = obj.obtener_ocupacion_actual()
        if ocupacion['ocupado'] and ocupacion['tiempo_ocupacion']:
            ocupacion['tiempo_ocupacion_minutos'] = int(
                ocupacion['tiempo_ocupacion'].total_seconds() / 60
            )
        return ocupacion
    
    def get_porcentaje_ocupacion_hoy(self, obj):
        """Porcentaje de ocupación del día"""
        return round(obj.calcular_tiempo_ocupacion_hoy(), 2)
    
    def get_tiempo_ocupado_formateado(self, obj):
        """Tiempo ocupado en formato legible"""
        if obj.tiempo_ocupado_hoy:
            total_segundos = obj.tiempo_ocupado_hoy.total_seconds()
            horas = int(total_segundos // 3600)
            minutos = int((total_segundos % 3600) // 60)
            return {
                'horas': horas,
                'minutos': minutos,
                'total_minutos': int(total_segundos / 60)
            }
        return {'horas': 0, 'minutos': 0, 'total_minutos': 0}


class BoxListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para lista de boxes"""
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    disponible = serializers.SerializerMethodField()
    
    class Meta:
        model = Box
        fields = [
            'id',
            'numero',
            'nombre',
            'especialidad',
            'especialidad_display',
            'estado',
            'estado_display',
            'disponible',
            'activo',
            'capacidad_maxima',
            'ultima_ocupacion',
        ]
    
    def get_disponible(self, obj):
        return obj.obtener_disponibilidad()


class BoxCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar boxes"""
    
    class Meta:
        model = Box
        fields = [
            'numero',
            'nombre',
            'especialidad',
            'estado',
            'capacidad_maxima',
            'equipamiento',
            'horarios_disponibles',
            'activo',
        ]
    
    def validate_numero(self, value):
        """Valida que el número no esté vacío"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El número del box no puede estar vacío.")
        return value.strip().upper()
    
    def validate_capacidad_maxima(self, value):
        """Valida que la capacidad sea mayor a 0"""
        if value < 1:
            raise serializers.ValidationError("La capacidad máxima debe ser al menos 1.")
        return value
    
    def validate_equipamiento(self, value):
        """Valida que equipamiento sea una lista"""
        if not isinstance(value, list):
            raise serializers.ValidationError("El equipamiento debe ser una lista.")
        return value


class BoxEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas agregadas de boxes"""
    total = serializers.IntegerField()
    disponibles = serializers.IntegerField()
    ocupados = serializers.IntegerField()
    mantenimiento = serializers.IntegerField()
    fuera_servicio = serializers.IntegerField()
    por_especialidad = serializers.DictField()
    tasa_ocupacion_promedio = serializers.FloatField()


class BoxOcupacionSerializer(serializers.Serializer):
    """Serializer para acciones de ocupar/liberar"""
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    
    class Meta:
        fields = ['timestamp']