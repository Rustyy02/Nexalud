from rest_framework import serializers
from .models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    # Campos display
    estado_actual_display = serializers.CharField(
        source='get_estado_actual_display', 
        read_only=True
    )
    etapa_actual_display = serializers.CharField(
        source='get_etapa_actual_display', 
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
    seguro_medico_display = serializers.CharField(
        source='get_seguro_medico_display',
        read_only=True
    )
    direccion_region_display = serializers.CharField(
        source='get_direccion_region_display',
        read_only=True
    )
    
    # Campos calculados y propiedades
    nombre_completo = serializers.CharField(read_only=True)
    direccion_completa = serializers.CharField(read_only=True)
    tiempo_total = serializers.SerializerMethodField()
    proceso_completo = serializers.SerializerMethodField()
    proceso_pausado = serializers.SerializerMethodField()
    imc = serializers.SerializerMethodField()
    categoria_imc = serializers.SerializerMethodField()
    tiene_alergias = serializers.SerializerMethodField()
    tiene_condiciones = serializers.SerializerMethodField()
    informacion_completa = serializers.SerializerMethodField()
    esta_en_proceso_clinico = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Paciente
        fields = [
            # Identificadores
            'id',
            'rut',
            'identificador_hash',
            
            # Datos Personales
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'fecha_nacimiento',
            'edad',
            'genero',
            'genero_display',
            
            # Contacto
            'correo',
            'telefono',
            'telefono_emergencia',
            'nombre_contacto_emergencia',
            
            # Dirección
            'direccion_calle',
            'direccion_comuna',
            'direccion_ciudad',
            'direccion_region',
            'direccion_region_display',
            'direccion_codigo_postal',
            'direccion_completa',
            
            # Seguro Médico
            'seguro_medico',
            'seguro_medico_display',
            'numero_beneficiario',
            
            # Información Médica
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
            'etapa_actual',  
            'etapa_actual_display',  
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
            'informacion_completa',
            'esta_en_proceso_clinico',  
        ]
        read_only_fields = [
            'id',
            'identificador_hash',
            'edad',
            'fecha_ingreso',
            'fecha_actualizacion',
            'etapa_actual',  
        ]
    
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
        return obj.is_proceso_completo()
    
    def get_proceso_pausado(self, obj):
        return obj.is_proceso_pausado()
    
    def get_imc(self, obj):
        return obj.calcular_imc()
    
    def get_categoria_imc(self, obj):
        return obj.obtener_categoria_imc()
    
    def get_tiene_alergias(self, obj):
        return obj.tiene_alergias()
    
    def get_tiene_condiciones(self, obj):
        return obj.tiene_condiciones_preexistentes()
    
    def get_informacion_completa(self, obj):
        return obj.obtener_informacion_completa()


class PacienteListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar pacientes.
    Incluye etapa_actual para visualización rápida.
    """
    estado_actual_display = serializers.CharField(
        source='get_estado_actual_display', 
        read_only=True
    )
    etapa_actual_display = serializers.CharField(
        source='get_etapa_actual_display', 
        read_only=True
    )
    nivel_urgencia_display = serializers.CharField(
        source='get_nivel_urgencia_display', 
        read_only=True
    )
    seguro_medico_display = serializers.CharField(
        source='get_seguro_medico_display',
        read_only=True
    )
    nombre_completo = serializers.CharField(read_only=True)
    tiene_alergias = serializers.SerializerMethodField()
    imc = serializers.SerializerMethodField()
    esta_en_proceso_clinico = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'rut',
            'identificador_hash',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'nombre_completo',
            'edad',
            'genero',
            'telefono',
            'correo',
            'seguro_medico',
            'seguro_medico_display',
            'estado_actual',
            'estado_actual_display',
            'etapa_actual',  
            'etapa_actual_display',  
            'nivel_urgencia',
            'nivel_urgencia_display',
            'fecha_ingreso',
            'activo',
            'tiene_alergias',
            'imc',
            'metadatos_adicionales',
            'esta_en_proceso_clinico',  
        ]
    
    def get_tiene_alergias(self, obj):
        return obj.tiene_alergias()
    
    def get_imc(self, obj):
        return obj.calcular_imc()


class PacienteCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar pacientes"""
    
    class Meta:
        model = Paciente
        fields = [
            'rut',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'fecha_nacimiento',
            'genero',
            'correo',
            'telefono',
            'telefono_emergencia',
            'nombre_contacto_emergencia',
            'direccion_calle',
            'direccion_comuna',
            'direccion_ciudad',
            'direccion_region',
            'direccion_codigo_postal',
            'seguro_medico',
            'numero_beneficiario',
            'tipo_sangre',
            'peso',
            'altura',
            'alergias',
            'condiciones_preexistentes',
            'medicamentos_actuales',
            'estado_actual',
            'nivel_urgencia',
            'activo',
            'metadatos_adicionales',
        ]
    
    def validate_rut(self, value):
        """Valida el RUT chileno"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El RUT no puede estar vacío.")
        
        rut_limpio = value.replace('.', '').replace('-', '').replace(' ', '').upper()
        
        if len(rut_limpio) >= 2:
            cuerpo = rut_limpio[:-1]
            dv = rut_limpio[-1]
            
            cuerpo_formateado = ""
            for i, digito in enumerate(reversed(cuerpo)):
                if i > 0 and i % 3 == 0:
                    cuerpo_formateado = "." + cuerpo_formateado
                cuerpo_formateado = digito + cuerpo_formateado
            
            value = f"{cuerpo_formateado}-{dv}"
        
        if not Paciente.validar_rut(value):
            raise serializers.ValidationError(
                "El RUT ingresado no es válido. Verifique el dígito verificador."
            )
        
        if self.instance is None:
            if Paciente.objects.filter(rut=value).exists():
                raise serializers.ValidationError(
                    "Ya existe un paciente registrado con este RUT."
                )
        
        return value

    def validate_nombre(self, value):
        if value and len(value.strip()) > 0:
            return value.strip().title()
        return value if value else ''

    def validate_apellido_paterno(self, value):
        if value and len(value.strip()) > 0:
            return value.strip().title()
        return value if value else ''

    def validate_apellido_materno(self, value):
        if value and len(value.strip()) > 0:
            return value.strip().title()
        return value if value else ''

    def validate_telefono(self, value):
        if not value:
            return value
        
        value = value.replace(' ', '')
        
        if not value.startswith('+56'):
            raise serializers.ValidationError(
                "El teléfono debe comenzar con +56 (código de país de Chile)."
            )
        return value

    def validate_correo(self, value):
        if value:
            return value.lower().strip()
        return value
    
    def validate_fecha_nacimiento(self, value):
        from datetime import date
        
        if value > date.today():
            raise serializers.ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )
        
        edad = date.today().year - value.year
        if (date.today().month, date.today().day) < (value.month, value.day):
            edad -= 1
        
        if edad < 0 or edad > 150:
            raise serializers.ValidationError(
                "La fecha de nacimiento no es válida. La edad debe estar entre 0 y 150 años."
            )
        
        return value
    
    def validate_peso(self, value):
        if value is not None:
            if value < 0 or value > 500:
                raise serializers.ValidationError(
                    "El peso debe estar entre 0 y 500 kg."
                )
        return value
    
    def validate_altura(self, value):
        if value is not None:
            if value < 0 or value > 300:
                raise serializers.ValidationError(
                    "La altura debe estar entre 0 y 300 cm."
                )
        return value
    
    def validate_metadatos_adicionales(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "metadatos_adicionales debe ser un diccionario (dict), no una lista."
            )
        return value
    
    def validate(self, data):
        if data.get('telefono_emergencia') and not data.get('nombre_contacto_emergencia'):
            raise serializers.ValidationError({
                'nombre_contacto_emergencia': 'Debe proporcionar el nombre del contacto de emergencia.'
            })
        
        return data


class PacienteEstadoSerializer(serializers.Serializer):
    """
    Serializer para actualizar solo el estado del paciente.
    NO incluye etapa_actual (se actualiza desde RutaClinica).
    """
    estado_actual = serializers.ChoiceField(choices=Paciente.ESTADO_CHOICES)
    
    def update(self, instance, validated_data):
        instance.actualizar_estado(validated_data['estado_actual'])
        return instance

class PacienteIMCSerializer(serializers.Serializer):
    """
    Serializer para calcular y retornar el IMC del paciente.
    """
    paciente_id = serializers.UUIDField()
    nombre = serializers.CharField()
    rut = serializers.CharField()
    peso = serializers.DecimalField(max_digits=5, decimal_places=2)
    altura = serializers.IntegerField()
    imc = serializers.FloatField()
    categoria_imc = serializers.CharField()


class PacienteDatosMedicosSerializer(serializers.ModelSerializer):
    """Serializer específico para datos médicos del paciente."""
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

class PacienteDatosContactoSerializer(serializers.ModelSerializer):
    """
    Serializer específico para datos de contacto.
    """
    direccion_completa = serializers.CharField(read_only=True)
    direccion_region_display = serializers.CharField(
        source='get_direccion_region_display',
        read_only=True
    )
    
    class Meta:
        model = Paciente
        fields = [
            'correo',
            'telefono',
            'telefono_emergencia',
            'nombre_contacto_emergencia',
            'direccion_calle',
            'direccion_comuna',
            'direccion_ciudad',
            'direccion_region',
            'direccion_region_display',
            'direccion_codigo_postal',
            'direccion_completa',
        ]


class PacienteSeguroMedicoSerializer(serializers.ModelSerializer):
    """
    Serializer específico para información del seguro médico.
    """
    seguro_medico_display = serializers.CharField(
        source='get_seguro_medico_display',
        read_only=True
    )
    
    class Meta:
        model = Paciente
        fields = [
            'seguro_medico',
            'seguro_medico_display',
            'numero_beneficiario',
        ]


class PacienteResumenSerializer(serializers.ModelSerializer):
    """Serializer resumido con información básica para displays rápidos."""
    nombre_completo = serializers.CharField(read_only=True)
    etapa_actual_display = serializers.CharField(
        source='get_etapa_actual_display',
        read_only=True
    )
    
    class Meta:
        model = Paciente
        fields = [
            'id',
            'rut',
            'nombre_completo',
            'edad',
            'telefono',
            'estado_actual',
            'etapa_actual',  
            'etapa_actual_display',  
        ]
