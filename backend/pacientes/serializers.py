from rest_framework import serializers
from .models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Paciente.
    Incluye todos los campos y métodos calculados.
    """
    estado_actual_display = serializers.CharField(
        source='get_estado_actual_display', 
        read_only=True
    )
    nivel_urgencia_display = serializers.CharField(
        source='get_nivel_urgencia_display', 
        read_only=True
    )
    genero_display = serializers.CharField(
        source='get_genero_display', 
        read_only=True
    )
    tiempo_total = serializers.SerializerMethodField()
    proceso_completo = serializers.SerializerMethodField()
    proceso_pausado = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'identificador_hash',
            'edad',
            'genero',
            'genero_display',
            'fecha_ingreso',
            'estado_actual',
            'estado_actual_display',
            'nivel_urgencia',
            'nivel_urgencia_display',
            'fecha_actualizacion',
            'activo',
            'metadatos_adicionales',
            'tiempo_total',
            'proceso_completo',
            'proceso_pausado',
        ]
        read_only_fields = ['id', 'fecha_ingreso', 'fecha_actualizacion']
    
    def get_tiempo_total(self, obj):
        """Retorna el tiempo total en formato legible"""
        tiempo = obj.calcular_tiempo_total()
        if tiempo:
            horas = int(tiempo.total_seconds() // 3600)
            minutos = int((tiempo.total_seconds() % 3600) // 60)
            return {
                'horas': horas,
                'minutos': minutos,
                'total_minutos': int(tiempo.total_seconds() // 60)
            }
        return None
    
    def get_proceso_completo(self, obj):
        """Indica si el proceso está completo"""
        return obj.is_proceso_completo()
    
    def get_proceso_pausado(self, obj):
        """Indica si el proceso está pausado"""
        return obj.is_proceso_pausado()


class PacienteListSerializer(serializers.ModelSerializer):
    """
    Listar pacientes
    
    """
    estado_actual_display = serializers.CharField(
        source='get_estado_actual_display', 
        read_only=True
    )
    nivel_urgencia_display = serializers.CharField(
        source='get_nivel_urgencia_display', 
        read_only=True
    )
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'identificador_hash',
            'edad',
            'genero',
            'estado_actual',
            'estado_actual_display',
            'nivel_urgencia',
            'nivel_urgencia_display',
            'fecha_ingreso',
            'activo',
        ]


class PacienteCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar pacientes.
    Solo permite modificar campos específicos.
    """
    
    class Meta:
        model = Paciente
        fields = [
            'identificador_hash',
            'edad',
            'genero',
            'estado_actual',
            'nivel_urgencia',
            'activo',
            'metadatos_adicionales',
        ]
    
    def validate_edad(self, value):
        """Valida que la edad sea razonable"""
        if value < 0 or value > 150:
            raise serializers.ValidationError("La edad debe estar entre 0 y 150 años.")
        return value
    
    def validate_identificador_hash(self, value):
        """Valida que el identificador_hash no esté vacío"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El identificador hash no puede estar vacío.")
        return value


class PacienteEstadoSerializer(serializers.Serializer):
    """
    Serializer para actualizar solo el estado del paciente.
    Útil para endpoints específicos de cambio de estado.
    """
    estado_actual = serializers.ChoiceField(choices=Paciente.ESTADO_CHOICES)
    
    def update(self, instance, validated_data):
        """Actualiza el estado del paciente"""
        instance.actualizar_estado(validated_data['estado_actual'])
        return instance