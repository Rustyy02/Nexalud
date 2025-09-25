import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator
from django.contrib.auth.models import User

class IntegracionExterna(models.Model):
    """
    Modelo para gestionar integraciones con sistemas externos como Rayen, Fonendo, etc.
    Intentamos incluir casi todos los tipos de sistemas que pueden existir.
    """
    
    TIPO_SISTEMA_CHOICES = [
        ('HIS', 'Sistema de Información Hospitalaria'),
        ('EMR', 'Registro Médico Electrónico'),
        ('LIS', 'Sistema de Información de Laboratorio'),
        ('RIS', 'Sistema de Información Radiológica'),
        ('PACS', 'Sistema de Archivo y Comunicación de Imágenes'),
        ('API_EXTERNA', 'API Externa'),
        ('WEBHOOK', 'Webhook'),
        ('OTRO', 'Otro Sistema'),
    ]
    
    METODO_AUTH_CHOICES = [
        ('API_KEY', 'API Key'),
        ('BEARER_TOKEN', 'Bearer Token'),
        ('BASIC_AUTH', 'Autenticación Básica'),
        ('OAUTH2', 'OAuth 2.0'),
        ('JWT', 'JSON Web Token'),
        ('CUSTOM', 'Método Personalizado'),
    ]
    
    ESTADO_CONEXION_CHOICES = [
        ('ACTIVA', 'Conexión Activa'),
        ('INACTIVA', 'Conexión Inactiva'),
        ('ERROR', 'Error de Conexión'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('CONFIGURACION', 'En Configuración'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre_sistema = models.CharField(
        max_length=100,
        help_text="Nombre del sistema externo (ej: Rayen, Fonendo)"
    )
    tipo_sistema = models.CharField(
        max_length=15,
        choices=TIPO_SISTEMA_CHOICES,
        default='HIS'
    )
    
    # Configuración de conexión
    endpoint_base_url = models.URLField(
        validators=[URLValidator()],
        help_text="URL base del sistema externo"
    )
    metodo_autenticacion = models.CharField(
        max_length=15,
        choices=METODO_AUTH_CHOICES,
        default='API_KEY'
    )
    token_acceso_encrypted = models.TextField(
        help_text="Token de acceso encriptado para seguridad"
    )
    
    # Estado y sincronización
    ultima_sincronizacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Última sincronización exitosa"
    )
    estado_conexion = models.CharField(
        max_length=15,
        choices=ESTADO_CONEXION_CHOICES,
        default='CONFIGURACION'
    )
    
    # Configuración de mapeo de datos
    configuracion_mapeo = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapeo de campos entre sistemas"
    )
    
    # Configuración de sincronización
    intervalo_sincronizacion = models.PositiveIntegerField(
        default=300,  # 5 minutos
        help_text="Intervalo de sincronización en segundos"
    )
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Usuario responsable de la configuración
    usuario_configuracion = models.ForeignKey(
        'users.User',  # Referencia al modelo User personalizado
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='integraciones_configuradas'
    )
    
    class Meta:
        db_table = 'integraciones_externas'
        verbose_name = 'Integración Externa'
        verbose_name_plural = 'Integraciones Externas'
        ordering = ['nombre_sistema']
        indexes = [
            models.Index(fields=['nombre_sistema']),
            models.Index(fields=['estado_conexion']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.nombre_sistema} ({self.get_estado_conexion_display()})"
    
    def sincronizar_datos(self):
        """
        Ejecuta la sincronización de datos con el sistema externo.
        """
        try:
            # Aquí iría la lógica específica de sincronización
            # Por ahora, simulamos una sincronización exitosa
            
            if self.validar_conexion():
                self.ultima_sincronizacion = timezone.now()
                self.estado_conexion = 'ACTIVA'
                self.save()
                
                # Crear log de sincronización exitosa
                LogSincronizacion.objects.create(
                    integracion=self,
                    estado='EXITOSA',
                    mensaje='Sincronización completada correctamente'
                )
                return True
            else:
                self.estado_conexion = 'ERROR'
                self.save()
                return False
                
        except Exception as e:
            self.estado_conexion = 'ERROR'
            self.save()
            
            # Crear log de error
            LogSincronizacion.objects.create(
                integracion=self,
                estado='ERROR',
                mensaje=f'Error en sincronización: {str(e)}'
            )
            return False
    
    def validar_conexion(self):
        """
        Valida que la conexión con el sistema externo esté funcionando.
        """
        try:
            # Aquí iría la lógica de validación específica
            # Por ejemplo, hacer un ping al endpoint
            return True  # Simulado por ahora
        except:
            return False
    
    def procesar_webhook(self, datos_webhook):
        """
        Procesa un webhook recibido desde el sistema externo.
        """
        try:
            # Validar formato de datos
            if not self._validar_formato_webhook(datos_webhook):
                return False
            
            # Procesar según configuración de mapeo
            datos_procesados = self._mapear_datos(datos_webhook)
            
            # Crear log de webhook procesado
            LogSincronizacion.objects.create(
                integracion=self,
                estado='WEBHOOK_PROCESADO',
                mensaje='Webhook procesado correctamente',
                datos_adicionales=datos_procesados
            )
            
            return True
            
        except Exception as e:
            LogSincronizacion.objects.create(
                integracion=self,
                estado='ERROR',
                mensaje=f'Error procesando webhook: {str(e)}',
                datos_adicionales=datos_webhook
            )
            return False
    
    def _validar_formato_webhook(self, datos):
        """Valida el formato de los datos del webhook"""
        # Implementar validaciones específicas según el sistema
        return isinstance(datos, dict)
    
    def _mapear_datos(self, datos_originales):
        """Mapea los datos según la configuración de mapeo"""
        if not self.configuracion_mapeo:
            return datos_originales
        
        datos_mapeados = {}
        for campo_local, campo_externo in self.configuracion_mapeo.items():
            if campo_externo in datos_originales:
                datos_mapeados[campo_local] = datos_originales[campo_externo]
        
        return datos_mapeados
    
    def obtener_datos_paciente(self, identificador_externo):
        """
        Obtiene datos de un paciente desde el sistema externo.
        """
        # Implementación específica según el sistema
        pass
    
    def obtener_disponibilidad_box(self, box_externo_id):
        """
        Obtiene la disponibilidad de un box desde el sistema externo.
        """
        # Implementación específica según el sistema
        pass
    
    def sincronizar_agenda(self, fecha_desde, fecha_hasta):
        """
        Sincroniza la agenda desde el sistema externo.
        """
        # Implementación específica según el sistema
        pass

class LogSincronizacion(models.Model):
    """
    Modelo para registrar logs de sincronización con sistemas externos.
    """
    
    ESTADO_CHOICES = [
        ('EXITOSA', 'Exitosa'),
        ('ERROR', 'Error'),
        ('ADVERTENCIA', 'Advertencia'),
        ('WEBHOOK_PROCESADO', 'Webhook Procesado'),
        ('TIMEOUT', 'Timeout'),
        ('DATOS_INVALIDOS', 'Datos Inválidos'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integracion = models.ForeignKey(
        IntegracionExterna,
        on_delete=models.CASCADE,
        related_name='logs_sincronizacion'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES
    )
    mensaje = models.TextField()
    
    # Datos adicionales para debugging
    datos_adicionales = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales sobre la sincronización"
    )
    
    # Métricas
    tiempo_respuesta_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tiempo de respuesta en milisegundos"
    )
    
    class Meta:
        db_table = 'logs_sincronizacion'
        verbose_name = 'Log de Sincronización'
        verbose_name_plural = 'Logs de Sincronización'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['integracion', '-timestamp']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.integracion.nombre_sistema} - {self.estado} ({self.timestamp})"

class ConfiguracionSistema(models.Model):
    """
    Modelo para configuraciones globales del sistema Nexalud.
    """
    
    TIPO_DATO_CHOICES = [
        ('STRING', 'Texto'),
        ('INTEGER', 'Número Entero'),
        ('FLOAT', 'Número Decimal'),
        ('BOOLEAN', 'Booleano'),
        ('JSON', 'JSON'),
        ('DATE', 'Fecha'),
        ('DATETIME', 'Fecha y Hora'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clave = models.CharField(
        max_length=100,
        unique=True,
        help_text="Clave única de la configuración"
    )
    valor = models.TextField(
        help_text="Valor de la configuración"
    )
    tipo_dato = models.CharField(
        max_length=10,
        choices=TIPO_DATO_CHOICES,
        default='STRING'
    )
    descripcion = models.TextField(
        help_text="Descripción de para qué sirve esta configuración"
    )
    
    # Metadatos
    usuario_modificacion = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Usuario que realizó la última modificación"
    )
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'configuraciones_sistema'
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['clave']
        indexes = [
            models.Index(fields=['clave']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.clave}: {self.valor[:50]}..."
    
    def obtener_valor_tipado(self):
        """
        Retorna el valor convertido al tipo de dato correcto.
        """
        try:
            if self.tipo_dato == 'INTEGER':
                return int(self.valor)
            elif self.tipo_dato == 'FLOAT':
                return float(self.valor)
            elif self.tipo_dato == 'BOOLEAN':
                return self.valor.lower() in ['true', '1', 'yes', 'si']
            elif self.tipo_dato == 'JSON':
                import json
                return json.loads(self.valor)
            elif self.tipo_dato == 'DATE':
                from datetime import datetime
                return datetime.strptime(self.valor, '%Y-%m-%d').date()
            elif self.tipo_dato == 'DATETIME':
                from datetime import datetime
                return datetime.fromisoformat(self.valor)
            else:
                return self.valor
        except:
            return self.valor  # Retorna string si hay error de conversión
    
    @classmethod
    def obtener_configuracion(cls, clave, valor_defecto=None):
        """
        Método de conveniencia para obtener una configuración.
        """
        try:
            config = cls.objects.get(clave=clave, activo=True)
            return config.obtener_valor_tipado()
        except cls.DoesNotExist:
            return valor_defecto
