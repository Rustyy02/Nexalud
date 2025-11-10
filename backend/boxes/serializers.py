from rest_framework import serializers
from .models import Box, OcupacionManual


class BoxSerializer(serializers.ModelSerializer):
    # Serializer completo para Box con información calculada
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    disponibilidad = serializers.SerializerMethodField()
    ocupacion_actual = serializers.SerializerMethodField()
    porcentaje_ocupacion_hoy = serializers.SerializerMethodField()
    tiempo_ocupado_formateado = serializers.SerializerMethodField()
    ocupacion_manual_activa = serializers.SerializerMethodField()
    
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
            'ocupacion_manual_activa',
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
        # Indica si el box está disponible
        return obj.obtener_disponibilidad()
    
    def get_ocupacion_actual(self, obj):
        # Información de ocupación actual
        ocupacion = obj.obtener_ocupacion_actual()
        if ocupacion['ocupado'] and ocupacion['tiempo_ocupacion']:
            ocupacion['tiempo_ocupacion_minutos'] = int(
                ocupacion['tiempo_ocupacion'].total_seconds() / 60
            )
        return ocupacion
    
    def get_porcentaje_ocupacion_hoy(self, obj):
        # Porcentaje de ocupación del día
        return round(obj.calcular_tiempo_ocupacion_hoy(), 2)
    
    def get_tiempo_ocupado_formateado(self, obj):
        # Tiempo ocupado en formato legible
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

    def get_ocupacion_manual_activa(self, obj):
        
            # Información de ocupación manual activa
            
            from django.utils import timezone
            
            ocupacion = OcupacionManual.objects.filter(
                box=obj,
                activa=True
            ).first()
            
            if ocupacion:
                ahora = timezone.now()
                tiempo_restante = ocupacion.fecha_fin_programada - ahora
                minutos_restantes = max(0, tiempo_restante.total_seconds() / 60)
                
                return {
                    'id': str(ocupacion.id),
                    'duracion_minutos': ocupacion.duracion_minutos,
                    'fecha_inicio': ocupacion.fecha_inicio,
                    'fecha_fin_programada': ocupacion.fecha_fin_programada,
                    'motivo': ocupacion.motivo,
                    'minutos_restantes': round(minutos_restantes, 1),
                }
            return None

class BoxListSerializer(serializers.ModelSerializer):
    
    # Serializer simplificado para lista de boxes
    
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
    
    # Serializer para crear y actualizar boxes
    
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
        # Valida que el número no esté vacío
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("El número del box no puede estar vacío.")
        return value.strip().upper()
    
    def validate_capacidad_maxima(self, value):
        # Valida que la capacidad sea mayor a 0
        if value < 1:
            raise serializers.ValidationError("La capacidad máxima debe ser al menos 1.")
        return value
    
    def validate_equipamiento(self, value):
        # Valida que equipamiento sea una lista
        if not isinstance(value, list):
            raise serializers.ValidationError("El equipamiento debe ser una lista.")
        return value


class BoxEstadisticasSerializer(serializers.Serializer):
    
    # Serializer para estadísticas agregadas de boxes
    
    total = serializers.IntegerField()
    disponibles = serializers.IntegerField()
    ocupados = serializers.IntegerField()
    mantenimiento = serializers.IntegerField()
    fuera_servicio = serializers.IntegerField()
    por_especialidad = serializers.DictField()
    tasa_ocupacion_promedio = serializers.FloatField()


class BoxOcupacionSerializer(serializers.Serializer):
    
    # Serializer para acciones de ocupar/liberar
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    
    class Meta:
        fields = ['timestamp']
        
class BoxConAtencionesSerializer(serializers.ModelSerializer):
    # Serializer de Box con información de atenciones programadas
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    disponible = serializers.SerializerMethodField()
    atencion_actual = serializers.SerializerMethodField()
    ocupado_por_atencion = serializers.SerializerMethodField()
    
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
            'atencion_actual',
            'ocupado_por_atencion',
        ]
    
    def get_disponible(self, obj):
        return obj.obtener_disponibilidad()
    
    def get_atencion_actual(self, obj):
        # Obtiene la atención que está ocupando el box actualmente
        from django.utils import timezone
        from atenciones.models import Atencion
        
        ahora = timezone.now()
        
        # Buscar atención en curso en este box
        atencion_en_curso = Atencion.objects.filter(
            box=obj,
            estado__in=['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO'],
            fecha_hora_inicio__lte=ahora,
        ).order_by('fecha_hora_inicio').first()
        
        if atencion_en_curso:
            # Calcular si la atención todavía debería estar ocupando el box
            tiempo_transcurrido = (ahora - atencion_en_curso.fecha_hora_inicio).total_seconds() / 60
            
            # Si está dentro del tiempo planificado
            if tiempo_transcurrido <= atencion_en_curso.duracion_planificada + 15:  # +15 min de margen
                return {
                    'id': str(atencion_en_curso.id),
                    'paciente': atencion_en_curso.paciente.identificador_hash[:12],
                    'medico': atencion_en_curso.medico.nombre_completo,
                    'fecha_hora_inicio': atencion_en_curso.fecha_hora_inicio,
                    'duracion_planificada': atencion_en_curso.duracion_planificada,
                    'estado': atencion_en_curso.estado,
                    'tipo_atencion': atencion_en_curso.get_tipo_atencion_display(),
                }
        
        return None
    
    def get_ocupado_por_atencion(self, obj):
        # Verifica si el box está ocupado por una atención programada
        return self.get_atencion_actual(obj) is not None
    
class OcupacionManualSerializer(serializers.ModelSerializer):
    # Serializer para ocupaciones manuales
    tiempo_restante_minutos = serializers.SerializerMethodField()
    
    class Meta:
        model = OcupacionManual
        fields = [
            'id',
            'box',
            'duracion_minutos',
            'fecha_inicio',
            'fecha_fin_programada',
            'fecha_fin_real',
            'motivo',
            'activa',
            'tiempo_restante_minutos',
        ]
        read_only_fields = ['id', 'fecha_inicio', 'fecha_fin_real']
    
    def get_tiempo_restante_minutos(self, obj):
        # Calcula el tiempo restante para la ocupación
        if obj.activa:
            from django.utils import timezone
            ahora = timezone.now()
            if ahora < obj.fecha_fin_programada:
                diferencia = obj.fecha_fin_programada - ahora
                return max(0, round(diferencia.total_seconds() / 60, 1))
        return 0