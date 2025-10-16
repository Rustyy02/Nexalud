# backend/pacientes/serializers.py - ACTUALIZADO CON NUEVOS CAMPOS
from rest_framework import serializers
from .models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el modelo Paciente.
    Incluye todos los campos nuevos y métodos calculados.
    """
    # Campos display
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
    tipo_sangre_display = serializers.CharField(
        source='get_tipo_sangre_display',
        read_only=True
    )
    
    # Campos calculados
    tiempo_total = serializers.SerializerMethodField()
    proceso_completo = serializers.SerializerMethodField()
    proceso_pausado = serializers.SerializerMethodField()
    imc = serializers.SerializerMethodField()
    categoria_imc = serializers.SerializerMethodField()
    tiene_alergias = serializers.SerializerMethodField()
    tiene_condiciones = serializers.SerializerMethodField()
    informacion_medica = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'identificador_hash',
            'edad',
            'genero',
            'genero_display',
            # NUEVOS CAMPOS MÉDICOS
            'tipo_sangre',
            'tipo_sangre_display',
            'peso',
            'altura',
            'alergias',
            'condiciones_preexistentes',
            'medicamentos_actuales',
            # Estado y seguimiento
            'fecha_ingreso',
            'estado_actual',
            'estado_actual_display',
            'nivel_urgencia',
            'nivel_urgencia_display',
            'fecha_actualizacion',
            'activo',
            'metadatos_adicionales',
            # Campos calculados
            'tiempo_total',
            'proceso_completo',
            'proceso_pausado',
            'imc',
            'categoria_imc',
            'tiene_alergias',
            'tiene_condiciones',
            'informacion_medica',
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
    
    def get_imc(self, obj):
        """Calcula el IMC"""
        return obj.calcular_imc()
    
    def get_categoria_imc(self, obj):
        """Retorna la categoría del IMC"""
        return obj.obtener_categoria_imc()
    
    def get_tiene_alergias(self, obj):
        """Indica si tiene alergias registradas"""
        return obj.tiene_alergias()
    
    def get_tiene_condiciones(self, obj):
        """Indica si tiene condiciones preexistentes"""
        return obj.tiene_condiciones_preexistentes()
    
    def get_informacion_medica(self, obj):
        """Retorna información médica completa"""
        return obj.obtener_informacion_medica_completa()


class PacienteListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar pacientes.
    """
    estado_actual_display = serializers.CharField(
        source='get_estado_actual_display', 
        read_only=True
    )
    nivel_urgencia_display = serializers.CharField(
        source='get_nivel_urgencia_display', 
        read_only=True
    )
    tipo_sangre_display = serializers.CharField(
        source='get_tipo_sangre_display',
        read_only=True
    )
    tiene_alergias = serializers.SerializerMethodField()
    imc = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'identificador_hash',
            'edad',
            'genero',
            'tipo_sangre',
            'tipo_sangre_display',
            'estado_actual',
            'estado_actual_display',
            'nivel_urgencia',
            'nivel_urgencia_display',
            'fecha_ingreso',
            'activo',
            'tiene_alergias',
            'imc',
        ]
    
    def get_tiene_alergias(self, obj):
        return obj.tiene_alergias()
    
    def get_imc(self, obj):
        return obj.calcular_imc()


class PacienteCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar pacientes.
    Incluye todos los campos editables.
    """
    
    class Meta:
        model = Paciente
        fields = [
            'identificador_hash',
            'edad',
            'genero',
            # NUEVOS CAMPOS MÉDICOS
            'tipo_sangre',
            'peso',
            'altura',
            'alergias',
            'condiciones_preexistentes',
            'medicamentos_actuales',
            # Estado
            'estado_actual',
            'nivel_urgencia',
            'activo',
            'metadatos_adicionales',
        ]
    
    def validate_edad(self, value):
        """Valida que la edad sea razonable"""
        if value < 0 or value > 150:
            raise serializers.ValidationError(
                "La edad debe estar entre 0 y 150 años."
            )
        return value
    
    def validate_identificador_hash(self, value):
        """Valida que el identificador_hash no esté vacío"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError(
                "El identificador hash no puede estar vacío."
            )
        return value
    
    def validate_peso(self, value):
        """Valida que el peso sea razonable"""
        if value is not None:
            if value < 0 or value > 500:
                raise serializers.ValidationError(
                    "El peso debe estar entre 0 y 500 kg."
                )
        return value
    
    def validate_altura(self, value):
        """Valida que la altura sea razonable"""
        if value is not None:
            if value < 0 or value > 300:
                raise serializers.ValidationError(
                    "La altura debe estar entre 0 y 300 cm."
                )
        return value
    
    def validate_metadatos_adicionales(self, value):
        """Valida que metadatos_adicionales sea un dict"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "metadatos_adicionales debe ser un diccionario (dict), no una lista."
            )
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


class PacienteIMCSerializer(serializers.Serializer):
    """
    Serializer para calcular y retornar el IMC del paciente.
    """
    paciente_id = serializers.UUIDField()
    nombre = serializers.CharField()
    peso = serializers.DecimalField(max_digits=5, decimal_places=2)
    altura = serializers.IntegerField()
    imc = serializers.FloatField()
    categoria_imc = serializers.CharField()
    
    class Meta:
        fields = ['paciente_id', 'nombre', 'peso', 'altura', 'imc', 'categoria_imc']


class PacienteDatosMedicosSerializer(serializers.ModelSerializer):
    """
    Serializer específico para datos médicos del paciente.
    Útil para actualizar solo información médica.
    """
    imc = serializers.SerializerMethodField()
    categoria_imc = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'tipo_sangre',
            'peso',
            'altura',
            'imc',
            'categoria_imc',
            'alergias',
            'condiciones_preexistentes',
            'medicamentos_actuales',
        ]
    
    def get_imc(self, obj):
        return obj.calcular_imc()
    
    def get_categoria_imc(self, obj):
        return obj.obtener_categoria_imc()