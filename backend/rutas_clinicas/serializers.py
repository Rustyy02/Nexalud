# backend/rutas_clinicas/serializers.py - ACTUALIZADO PARA MOSTRAR TODAS LAS ETAPAS
from rest_framework import serializers
from .models import RutaClinica
from pacientes.serializers import PacienteListSerializer


class RutaClinicaSerializer(serializers.ModelSerializer):
    """Serializer completo mejorado con todas las etapas"""
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
        help_text="Seleccione las etapas del proceso clínico",
        style={'base_template': 'checkbox_multiple.html'}
    )
    
    # Campo editable para etapa_actual
    etapa_actual = serializers.ChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        required=False,
        allow_null=True,
        help_text="Etapa actual del proceso"
    )
    
    # Información calculada
    tiempo_total_real = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    etapa_siguiente = serializers.SerializerMethodField()
    total_etapas = serializers.SerializerMethodField()
    etapas_restantes = serializers.SerializerMethodField()
    retrasos_detectados = serializers.SerializerMethodField()
    
    # Choices disponibles
    etapas_disponibles = serializers.SerializerMethodField()
    
    # Estado del paciente sincronizado
    estado_paciente = serializers.CharField(
        source='paciente.estado_actual_display',
        read_only=True
    )
    
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
            'estado_paciente',
            'esta_pausado',
            'motivo_pausa',
            'metadatos_adicionales',
            'historial_cambios',
            'fecha_actualizacion',
            'tiempo_total_real',
            'timeline',
            'etapa_siguiente',
            'total_etapas',
            'etapas_restantes',
            'retrasos_detectados',
        ]
        read_only_fields = [
            'id',
            'indice_etapa_actual',
            'etapas_completadas',
            'timestamps_etapas',
            'porcentaje_completado',
            'fecha_actualizacion',
            'fecha_fin_real',
            'esta_pausado',
            'historial_cambios',
        ]
    
    def update(self, instance, validated_data):
        """Permite actualizar etapa_actual manualmente"""
        etapa_actual_nueva = validated_data.get('etapa_actual', instance.etapa_actual)
        
        # Si cambia la etapa_actual, actualizar el índice
        if etapa_actual_nueva and etapa_actual_nueva != instance.etapa_actual:
            etapas_seleccionadas = instance.etapas_seleccionadas or [key for key, _ in RutaClinica.ETAPAS_CHOICES]
            try:
                nuevo_indice = etapas_seleccionadas.index(etapa_actual_nueva)
                instance.indice_etapa_actual = nuevo_indice
                instance.etapa_actual = etapa_actual_nueva
                
                # Actualizar etapas completadas
                instance.etapas_completadas = etapas_seleccionadas[:nuevo_indice]
                
                # Sincronizar con paciente
                instance._sincronizar_etapa_paciente()
            except ValueError:
                pass
        
        # Actualizar el resto de campos
        for attr, value in validated_data.items():
            if attr not in ['etapa_actual', 'paciente']:
                setattr(instance, attr, value)
        
        instance.calcular_progreso()
        instance.save()
        
        return instance
    
    # ... resto de métodos igual que antes ...
    def get_etapas_disponibles(self, obj):
        """Retorna etapas disponibles con duraciones"""
        return [
            {
                'key': key,
                'label': label,
                'duracion_estimada': RutaClinica.DURACIONES_ESTIMADAS.get(key, 30)
            }
            for key, label in RutaClinica.ETAPAS_CHOICES
        ]
    
    def get_tiempo_total_real(self, obj):
        """Tiempo real transcurrido"""
        tiempo = obj.obtener_tiempo_total_real()
        minutos = int(tiempo.total_seconds() / 60)
        horas = int(tiempo.total_seconds() / 3600)
        return {
            'minutos': minutos,
            'horas': horas,
            'formateado': f"{horas}h {minutos % 60}m"
        }
    
    def get_timeline(self, obj):
        """Timeline estructurado con TODAS las etapas"""
        return obj.obtener_timeline_completo()
    
    def get_etapa_siguiente(self, obj):
        """Siguiente etapa"""
        siguiente = obj.obtener_etapa_siguiente()
        if siguiente:
            label = dict(RutaClinica.ETAPAS_CHOICES).get(siguiente, siguiente)
            return {
                'key': siguiente,
                'label': label,
                'duracion_estimada': RutaClinica.DURACIONES_ESTIMADAS.get(siguiente, 30)
            }
        return None
    
    def get_total_etapas(self, obj):
        """Total de TODAS las etapas disponibles"""
        return len(RutaClinica.ETAPAS_CHOICES)
    
    def get_etapas_restantes(self, obj):
        """Etapas restantes"""
        total = len(RutaClinica.ETAPAS_CHOICES)
        completadas = len(obj.etapas_completadas) if isinstance(obj.etapas_completadas, list) else 0
        return total - completadas
    
    def get_retrasos_detectados(self, obj):
        """Detecta retrasos en las etapas"""
        try:
            return obj.detectar_retrasos()
        except Exception:
            return []


class RutaClinicaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado mejorado"""
    paciente_hash = serializers.CharField(source='paciente.identificador_hash', read_only=True)
    paciente_nombre = serializers.SerializerMethodField()
    paciente_edad = serializers.IntegerField(source='paciente.edad', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    etapa_actual_display = serializers.CharField(source='get_etapa_actual_display', read_only=True)
    progreso_info = serializers.SerializerMethodField()
    tiene_retrasos = serializers.SerializerMethodField()
    estado_paciente = serializers.CharField(source='paciente.estado_actual_display', read_only=True)
    
    class Meta:
        model = RutaClinica
        fields = [
            'id',
            'paciente_hash',
            'paciente_nombre',
            'paciente_edad',
            'etapa_actual',
            'etapa_actual_display',
            'fecha_inicio',
            'porcentaje_completado',
            'estado',
            'estado_display',
            'estado_paciente',
            'esta_pausado',
            'progreso_info',
            'tiene_retrasos',
        ]
    
    def get_paciente_nombre(self, obj):
        """Obtiene el nombre del paciente con validación robusta"""
        metadatos = obj.paciente.metadatos_adicionales
        
        # Validar que sea un diccionario
        if not isinstance(metadatos, dict):
            return f'Paciente {obj.paciente.identificador_hash[:8]}'
        
        return metadatos.get('nombre', f'Paciente {obj.paciente.identificador_hash[:8]}')
    
    def get_progreso_info(self, obj):
        """🆕 ACTUALIZADO: Información de progreso con todas las etapas"""
        total = len(RutaClinica.ETAPAS_CHOICES)
        completadas = len(obj.etapas_completadas) if isinstance(obj.etapas_completadas, list) else 0
        
        return {
            'total': total,
            'completadas': completadas,
            'porcentaje': obj.porcentaje_completado,
        }
    
    def get_tiene_retrasos(self, obj):
        """Indica si tiene retrasos"""
        try:
            retrasos = obj.detectar_retrasos()
            return len(retrasos) > 0
        except Exception:
            return False


class RutaClinicaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear rutas con validaciones mejoradas"""
    
    etapas_seleccionadas = serializers.MultipleChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        help_text="✓ Seleccione las etapas del proceso clínico (checkbox múltiple)",
        required=False,
        style={'base_template': 'checkbox_multiple.html'}
    )
    
    etapa_actual = serializers.ChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        required=False,
        allow_null=True,
        help_text="Etapa inicial de la ruta (opcional, se seleccionará automáticamente si no se especifica)"
    )
    
    class Meta:
        model = RutaClinica
        fields = [
            'paciente',
            'etapas_seleccionadas',
            'etapa_actual',
            'fecha_estimada_fin',
            'metadatos_adicionales',
        ]
    
    def validate_etapas_seleccionadas(self, value):
        """Valida etapas seleccionadas"""
        if not value or len(value) == 0:
            return [key for key, _ in RutaClinica.ETAPAS_CHOICES]
        
        if not isinstance(value, list):
            value = list(value)
        
        return value
    
    def validate(self, attrs):
        """Validación cruzada de etapa_actual con etapas_seleccionadas"""
        etapa_actual = attrs.get('etapa_actual')
        etapas_seleccionadas = attrs.get('etapas_seleccionadas', [])
        
        # Si no hay etapas seleccionadas, usar todas
        if not etapas_seleccionadas:
            etapas_seleccionadas = [key for key, _ in RutaClinica.ETAPAS_CHOICES]
            attrs['etapas_seleccionadas'] = etapas_seleccionadas
        
        # Si se especifica etapa_actual, verificar que esté en las seleccionadas
        if etapa_actual and etapa_actual not in etapas_seleccionadas:
            raise serializers.ValidationError({
                'etapa_actual': f'La etapa actual debe estar incluida en las etapas seleccionadas'
            })
        
        return attrs
    
    def validate_paciente(self, value):
        """Valida que el paciente no tenga ya una ruta activa"""
        rutas_activas = RutaClinica.objects.filter(
            paciente=value,
            estado__in=['INICIADA', 'EN_PROGRESO']
        )
        
        if rutas_activas.exists():
            raise serializers.ValidationError(
                "Este paciente ya tiene una ruta clínica activa. "
                "Debe completarla o cancelarla antes de crear una nueva."
            )
        
        return value
    
    def create(self, validated_data):
        """Crea la ruta con etapa_actual personalizada si se proporciona"""
        etapa_actual = validated_data.pop('etapa_actual', None)
        
        ruta = RutaClinica.objects.create(**validated_data)
        
        # Si se especificó una etapa_actual, configurarla antes de iniciar
        if etapa_actual:
            etapas_seleccionadas = ruta.etapas_seleccionadas or [key for key, _ in RutaClinica.ETAPAS_CHOICES]
            try:
                indice = etapas_seleccionadas.index(etapa_actual)
                ruta.indice_etapa_actual = indice
                ruta.etapa_actual = etapa_actual
                
                # Marcar etapas anteriores como completadas
                ruta.etapas_completadas = etapas_seleccionadas[:indice]
                
                ruta.save()
            except ValueError:
                pass
        
        ruta.calcular_progreso()
        
        # Solo iniciar si no se especificó etapa_actual
        if not etapa_actual:
            ruta.iniciar_ruta()
        else:
            # Sincronizar con paciente manualmente
            ruta._sincronizar_etapa_paciente()
            ruta.estado = 'EN_PROGRESO'
            ruta.save()
        
        return ruta

class TimelineSerializer(serializers.Serializer):
    """Serializer mejorado para el timeline con todas las etapas"""
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
    retrasos = serializers.ListField()
    
    def get_paciente(self, obj):
        """Información del paciente con validación"""
        metadatos = obj['paciente'].metadatos_adicionales
        
        # Validar que sea dict
        if isinstance(metadatos, dict):
            nombre = metadatos.get('nombre', 'N/A')
        else:
            nombre = f'Paciente {obj["paciente"].identificador_hash[:8]}'
        
        return {
            'id': str(obj['paciente'].id),
            'identificador_hash': obj['paciente'].identificador_hash,
            'nombre': nombre,
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
    """Serializer para acciones"""
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=500)
    observaciones = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class HistorialCambiosSerializer(serializers.Serializer):
    """Serializer para el historial de cambios"""
    timestamp = serializers.DateTimeField()
    accion = serializers.CharField()
    etapa = serializers.CharField(allow_null=True)
    usuario = serializers.CharField()
    desde = serializers.CharField(required=False)
    hacia = serializers.CharField(required=False)
    motivo = serializers.CharField(required=False)