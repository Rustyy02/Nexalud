from rest_framework import serializers
from .models import Medico, Atencion
from pacientes.serializers import PacienteListSerializer
from boxes.serializers import BoxListSerializer


# ==================== SERIALIZERS DE MÉDICO (LEGACY) ====================

class MedicoSerializer(serializers.ModelSerializer):
    """Serializer completo para Medico (legacy)"""
    especialidad_principal_display = serializers.CharField(
        source='get_especialidad_principal_display',
        read_only=True
    )
    nombre_completo = serializers.CharField(read_only=True)
    tiempo_promedio_atencion = serializers.SerializerMethodField()
    eficiencia = serializers.SerializerMethodField()
    atenciones_hoy_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Medico
        fields = [
            'id',
            'codigo_medico',
            'nombre',
            'apellido',
            'nombre_completo',
            'especialidad_principal',
            'especialidad_principal_display',
            'especialidades_secundarias',
            'horarios_atencion',
            'activo',
            'fecha_ingreso',
            'configuraciones_personales',
            'tiempo_promedio_atencion',
            'eficiencia',
            'atenciones_hoy_count',
        ]
        read_only_fields = ['id', 'fecha_ingreso']
    
    def get_tiempo_promedio_atencion(self, obj):
        return round(obj.calcular_tiempo_promedio_atencion(), 2)
    
    def get_eficiencia(self, obj):
        return obj.obtener_eficiencia()
    
    def get_atenciones_hoy_count(self, obj):
        return obj.obtener_atenciones_dia().count()


class MedicoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar médicos (legacy)"""
    especialidad_principal_display = serializers.CharField(
        source='get_especialidad_principal_display',
        read_only=True
    )
    nombre_completo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Medico
        fields = [
            'id',
            'codigo_medico',
            'nombre_completo',
            'especialidad_principal',
            'especialidad_principal_display',
            'activo',
        ]


class MedicoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar médicos (legacy)"""
    
    class Meta:
        model = Medico
        fields = [
            'codigo_medico',
            'nombre',
            'apellido',
            'especialidad_principal',
            'especialidades_secundarias',
            'horarios_atencion',
            'activo',
            'configuraciones_personales',
        ]
    
    def validate_codigo_medico(self, value):
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El código del médico no puede estar vacío.")
        return value.strip().upper()
    
    def validate_especialidades_secundarias(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Las especialidades secundarias deben ser una lista.")
        return value


# ✅ NUEVO: Serializer para Médico (User)
class MedicoUserSerializer(serializers.Serializer):
    """
    Serializer para representar usuarios con rol MEDICO como médicos.
    """
    id = serializers.UUIDField(read_only=True)
    username = serializers.CharField(read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    
    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username


# ==================== SERIALIZERS DE ATENCIÓN ====================

class AtencionSerializer(serializers.ModelSerializer):
    """Serializer completo para Atencion"""
    # Campos display
    tipo_atencion_display = serializers.CharField(
        source='get_tipo_atencion_display',
        read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    
    # Relaciones anidadas (solo lectura)
    paciente_info = PacienteListSerializer(source='paciente', read_only=True)
    # ✅ Actualizado: ahora usa MedicoUserSerializer
    medico_info = MedicoUserSerializer(source='medico', read_only=True)
    box_info = BoxListSerializer(source='box', read_only=True)
    
    # IDs para escritura
    paciente_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('pacientes.models', fromlist=['Paciente']).Paciente.objects.all(),
        source='paciente',
        write_only=True,
        required=False
    )
    # ✅ Actualizado: ahora filtra User con rol MEDICO
    medico_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('users.models', fromlist=['User']).User.objects.filter(rol='MEDICO'),
        source='medico',
        write_only=True,
        required=False
    )
    box_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('boxes.models', fromlist=['Box']).Box.objects.all(),
        source='box',
        write_only=True,
        required=False
    )
    
    # Campos calculados
    retraso_minutos = serializers.SerializerMethodField()
    tiempo_transcurrido_minutos = serializers.SerializerMethodField()
    esta_retrasada = serializers.SerializerMethodField()
    diferencia_duracion = serializers.SerializerMethodField()
    metricas = serializers.SerializerMethodField()
    tiempo_restante_minutos = serializers.SerializerMethodField()
    
    # ✅ NUEVO: Información útil para médicos
    puede_iniciar = serializers.SerializerMethodField()
    puede_finalizar = serializers.SerializerMethodField()
    minutos_hasta_inicio = serializers.SerializerMethodField()
    
    class Meta:
        model = Atencion
        fields = [
            'id',
            'paciente',
            'paciente_id',
            'paciente_info',
            'medico',
            'medico_id',
            'medico_info',
            'box',
            'box_id',
            'box_info',
            'fecha_hora_inicio',
            'fecha_hora_fin',
            'inicio_cronometro',
            'fin_cronometro',
            'duracion_planificada',
            'duracion_real',
            'tipo_atencion',
            'tipo_atencion_display',
            'estado',
            'estado_display',
            'observaciones',
            'fecha_creacion',
            'fecha_actualizacion',
            'retraso_minutos',
            'tiempo_transcurrido_minutos',
            'esta_retrasada',
            'diferencia_duracion',
            'metricas',
            'tiempo_restante_minutos',
            'puede_iniciar',  # ✅ NUEVO
            'puede_finalizar',  # ✅ NUEVO
            'minutos_hasta_inicio',  # ✅ NUEVO
        ]
        read_only_fields = [
            'id',
            'duracion_real',
            'inicio_cronometro',
            'fin_cronometro',
            'fecha_creacion',
            'fecha_actualizacion'
        ]
    
    def get_tiempo_restante_minutos(self, obj):
        """Calcula el tiempo restante para la atención"""
        if obj.estado == 'EN_CURSO' and obj.inicio_cronometro:
            from django.utils import timezone
            ahora = timezone.now()
            tiempo_transcurrido = (ahora - obj.inicio_cronometro).total_seconds() / 60
            tiempo_restante = obj.duracion_planificada - tiempo_transcurrido
            return max(0, int(tiempo_restante))
        return None
    
    def get_retraso_minutos(self, obj):
        return obj.calcular_retraso()
    
    def get_tiempo_transcurrido_minutos(self, obj):
        tiempo = obj.obtener_tiempo_transcurrido()
        if tiempo:
            return int(tiempo.total_seconds() / 60)
        return None
    
    def get_esta_retrasada(self, obj):
        return obj.is_retrasada()
    
    def get_diferencia_duracion(self, obj):
        return obj.calcular_diferencia_duracion()
    
    def get_metricas(self, obj):
        return obj.generar_metricas()
    
    # ✅ NUEVOS MÉTODOS
    def get_puede_iniciar(self, obj):
        return obj.puede_iniciar()
    
    def get_puede_finalizar(self, obj):
        return obj.puede_finalizar()
    
    def get_minutos_hasta_inicio(self, obj):
        tiempo = obj.tiempo_hasta_inicio()
        if tiempo:
            return int(tiempo.total_seconds() / 60)
        return 0


class AtencionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar atenciones"""
    # ✅ NUEVO: Mostrar nombre completo del paciente
    paciente_nombre = serializers.SerializerMethodField()
    paciente_hash = serializers.CharField(
        source='paciente.identificador_hash',
        read_only=True
    )
    # ✅ Actualizado: nombre del médico
    medico_nombre = serializers.SerializerMethodField()
    box_numero = serializers.CharField(
        source='box.numero',
        read_only=True
    )
    tipo_atencion_display = serializers.CharField(
        source='get_tipo_atencion_display',
        read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    esta_retrasada = serializers.SerializerMethodField()
    
    class Meta:
        model = Atencion
        fields = [
            'id',
            'paciente_nombre',  # ✅ NUEVO: Nombre completo
            'paciente_hash',
            'medico_nombre',
            'box_numero',
            'fecha_hora_inicio',
            'tipo_atencion',
            'tipo_atencion_display',
            'estado',
            'estado_display',
            'duracion_planificada',
            'duracion_real',
            'esta_retrasada',
        ]
    
    def get_paciente_nombre(self, obj):
        """✅ NUEVO: Retorna nombre completo del paciente"""
        try:
            # Intentar obtener nombre completo
            if hasattr(obj.paciente, 'nombre') and hasattr(obj.paciente, 'apellido_paterno'):
                nombre = f"{obj.paciente.nombre} {obj.paciente.apellido_paterno}"
                if obj.paciente.apellido_materno:
                    nombre += f" {obj.paciente.apellido_materno}"
                return nombre.strip()
            # Fallback al hash si no tiene nombre
            return obj.paciente.identificador_hash[:12] + "..."
        except Exception as e:
            return obj.paciente.identificador_hash[:12] + "..."
    
    def get_medico_nombre(self, obj):
        return obj.medico.get_full_name() or obj.medico.username
    
    def get_esta_retrasada(self, obj):
        return obj.is_retrasada()

class AtencionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear y actualizar atenciones"""
    
    class Meta:
        model = Atencion
        fields = [
            'paciente',
            'medico',  # ✅ Ahora apunta a User
            'box',
            'fecha_hora_inicio',
            'fecha_hora_fin',
            'duracion_planificada',
            'tipo_atencion',
            'estado',
            'observaciones',
        ]
    
    def validate_duracion_planificada(self, value):
        if value <= 0:
            raise serializers.ValidationError("La duración planificada debe ser mayor a 0 minutos.")
        return value
    
    def validate_medico(self, value):
        """✅ NUEVO: Validar que el médico tenga rol MEDICO"""
        if value.rol != 'MEDICO':
            raise serializers.ValidationError("El usuario seleccionado debe tener rol de médico.")
        return value
    
    def validate(self, data):
        # Validar que fecha_fin sea posterior a fecha_inicio
        if data.get('fecha_hora_fin') and data.get('fecha_hora_inicio'):
            if data['fecha_hora_fin'] <= data['fecha_hora_inicio']:
                raise serializers.ValidationError({
                    'fecha_hora_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        # Validar disponibilidad del box
        box = data.get('box')
        if box and box.estado == 'OCUPADO':
            raise serializers.ValidationError({
                'box': f'El box {box.numero} está actualmente ocupado.'
            })
        
        return data


class AtencionCronometroSerializer(serializers.Serializer):
    """Serializer para acciones de cronómetro"""
    timestamp = serializers.DateTimeField(required=False, allow_null=True)


class AtencionCancelarSerializer(serializers.Serializer):
    """Serializer para cancelar atención"""
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=500)


class AtencionReagendarSerializer(serializers.Serializer):
    """Serializer para reagendar atención"""
    nueva_fecha = serializers.DateTimeField(required=True)
    nuevo_box = serializers.PrimaryKeyRelatedField(
        queryset=__import__('boxes.models', fromlist=['Box']).Box.objects.all(),
        required=False,
        allow_null=True
    )


class AtencionEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de atenciones"""
    total = serializers.IntegerField()
    por_estado = serializers.DictField()
    por_tipo = serializers.DictField()
    promedio_duracion_real = serializers.FloatField()
    promedio_duracion_planificada = serializers.FloatField()
    tasa_cumplimiento_horario = serializers.FloatField()
    atenciones_retrasadas = serializers.IntegerField()