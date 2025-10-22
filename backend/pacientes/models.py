# backend/pacientes/models.py - VERSIÓN COMPLETA ACTUALIZADA
import uuid
import re
import hashlib
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator
from datetime import date


class Paciente(models.Model):
    """
    Modelo completo para gestionar pacientes en el sistema Nexalud.
    Incluye información personal, médica, contacto y seguro médico chileno.
    """
    
    ESTADO_CHOICES = [
        ('EN_ESPERA', 'En Espera'),
        ('EN_CONSULTA', 'En Consulta'),
        ('EN_EXAMEN', 'En Exámen'),
        ('PROCESO_PAUSADO', 'Proceso Pausado'),
        ('ALTA_COMPLETA', 'Alta Completa'),
        ('PROCESO_INCOMPLETO', 'Proceso Incompleto'),
    ]
    
    URGENCIA_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
        ('NE', 'No Especifica'),
    ]
    
    TIPO_SANGRE_CHOICES = [
        ('A+', 'A Positivo'),
        ('A-', 'A Negativo'),
        ('B+', 'B Positivo'),
        ('B-', 'B Negativo'),
        ('AB+', 'AB Positivo'),
        ('AB-', 'AB Negativo'),
        ('O+', 'O Positivo'),
        ('O-', 'O Negativo'),
        ('DESCONOCIDO', 'Desconocido'),
    ]
    
    SEGURO_MEDICO_CHOICES = [
        ('FONASA_A', 'FONASA Tramo A'),
        ('FONASA_B', 'FONASA Tramo B'),
        ('FONASA_C', 'FONASA Tramo C'),
        ('FONASA_D', 'FONASA Tramo D'),
        ('ISAPRE_BANMEDICA', 'Isapre Banmédica'),
        ('ISAPRE_COLMENA', 'Isapre Colmena'),
        ('ISAPRE_CONSALUD', 'Isapre Consalud'),
        ('ISAPRE_CRUZBANCA', 'Isapre Cruz Blanca'),
        ('ISAPRE_VIDATRES', 'Isapre Vida Tres'),
        ('ISAPRE_NUEVA_MASVIDA', 'Isapre Nueva Masvida'),
        ('ISAPRE_ESENCIAL', 'Isapre Esencial'),
        ('PARTICULAR', 'Particular (Sin Previsión)'),
        ('OTRO', 'Otro'),
    ]
    
    REGION_CHOICES = [
        ('XV', 'Región de Arica y Parinacota'),
        ('I', 'Región de Tarapacá'),
        ('II', 'Región de Antofagasta'),
        ('III', 'Región de Atacama'),
        ('IV', 'Región de Coquimbo'),
        ('V', 'Región de Valparaíso'),
        ('RM', 'Región Metropolitana de Santiago'),
        ('VI', "Región del Libertador General Bernardo O'Higgins"),
        ('VII', 'Región del Maule'),
        ('XVI', 'Región de Ñuble'),
        ('VIII', 'Región del Biobío'),
        ('IX', 'Región de La Araucanía'),
        ('XIV', 'Región de Los Ríos'),
        ('X', 'Región de Los Lagos'),
        ('XI', 'Región Aysén del General Carlos Ibáñez del Campo'),
        ('XII', 'Región de Magallanes y de la Antártica Chilena'),
    ]
    
    # Validadores personalizados
    rut_validator = RegexValidator(
        regex=r'^\d{1,2}\.\d{3}\.\d{3}-[0-9kK]$',
        message='El RUT debe estar en formato chileno: XX.XXX.XXX-X (ejemplo: 12.345.678-9)'
    )
    
    telefono_validator = RegexValidator(
        regex=r'^\+56\d{9}$',
        message='El teléfono debe estar en formato chileno: +56912345678'
    )
    
    # ============================================
    # IDENTIFICADORES
    # ============================================
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # RUT Chileno (con formato y dígito verificador)
    rut = models.CharField(
        max_length=12,
        unique=True,
        validators=[rut_validator],
        default='',
        help_text="RUT en formato chileno XX.XXX.XXX-X"
    )
    
    # Hash del RUT (para búsquedas rápidas y privacidad)
    identificador_hash = models.CharField(
        max_length=64, 
        unique=True,
        db_index=True,
        editable=False,
        default='',
        help_text="Hash SHA-256 del RUT para proteger privacidad"
    )
    
    # ============================================
    # DATOS PERSONALES
    # ============================================
    
    nombre = models.CharField(
        max_length=100,
        null=True,
        help_text="Nombre(s) del paciente"
    )
    
    apellido_paterno = models.CharField(
        max_length=100,
        null=True,
        help_text="Apellido paterno del paciente"
    )
    
    apellido_materno = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Apellido materno del paciente (opcional)"
    )
    
    fecha_nacimiento = models.DateField(
        null=True,
        help_text="Fecha de nacimiento del paciente"
    )
    
    edad = models.PositiveIntegerField(
        editable=False,
        help_text="Edad calculada automáticamente desde fecha de nacimiento"
    )
    
    genero = models.CharField(
        max_length=2, 
        choices=GENERO_CHOICES, 
        default='NE'
    )
    
    # ============================================
    # DATOS DE CONTACTO
    # ============================================
    
    correo = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        validators=[EmailValidator()],
        help_text="Correo electrónico del paciente"
    )
    
    telefono = models.CharField(
        max_length=13,
        null=True,
        validators=[telefono_validator],
        help_text="Teléfono celular en formato +56912345678"
    )
    
    telefono_emergencia = models.CharField(
        max_length=13,
        blank=True,
       null=True,
        validators=[telefono_validator],
        help_text="Teléfono de contacto de emergencia (opcional)"
    )
    
    nombre_contacto_emergencia = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre del contacto de emergencia"
    )
    
    # ============================================
    # DIRECCIÓN
    # ============================================
    
    direccion_calle = models.CharField(
        max_length=255,
        null=True,
        help_text="Calle y número"
    )
    
    direccion_comuna = models.CharField(
        max_length=100,
        null=True,
        help_text="Comuna"
    )
    
    direccion_ciudad = models.CharField(
        max_length=100,
        null=True,
        help_text="Ciudad"
    )
    
    direccion_region = models.CharField(
        max_length=5,
        null=True,
        choices=REGION_CHOICES,
        help_text="Región de Chile"
    )
    
    direccion_codigo_postal = models.CharField(
        max_length=10,
        blank=True,
        default='Sin proporcionar',
        help_text="Código postal (opcional)"
    )
    
    # ============================================
    # SEGURO MÉDICO Y PREVISIÓN
    # ============================================
    
    seguro_medico = models.CharField(
        max_length=30,
        choices=SEGURO_MEDICO_CHOICES,
        default='PARTICULAR',
        help_text="Sistema de salud al que pertenece"
    )
    
    numero_beneficiario = models.CharField(
        max_length=50,
        blank=True,
        default='Sin proporcionar',
        help_text="Número de beneficiario o afiliado (opcional)"
    )
    
    # ============================================
    # INFORMACIÓN MÉDICA
    # ============================================
    
    tipo_sangre = models.CharField(
        max_length=15, 
        choices=TIPO_SANGRE_CHOICES,
        default='DESCONOCIDO',
        help_text="Tipo de sangre del paciente"
    )
    
    peso = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        default='DESCONOCIDO',
        blank=True,
        help_text="Peso en kilogramos"
    )
    
    altura = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Altura en centímetros"
    )
    
    alergias = models.TextField(
        blank=True,
        help_text="Alergias conocidas del paciente"
    )
    
    condiciones_preexistentes = models.TextField(
        blank=True,
        help_text="Condiciones médicas preexistentes"
    )
    
    medicamentos_actuales = models.TextField(
        blank=True,
        help_text="Medicamentos que toma actualmente"
    )
    
    # ============================================
    # ESTADO Y SEGUIMIENTO
    # ============================================
    
    fecha_ingreso = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de ingreso al sistema"
    )
    
    estado_actual = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES,
        default='EN_ESPERA'
    )
    
    nivel_urgencia = models.CharField(
        max_length=10, 
        choices=URGENCIA_CHOICES,
        default='MEDIA'
    )
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    # ============================================
    # METADATOS
    # ============================================
    
    metadatos_adicionales = models.JSONField(
        default=dict,
        blank=True,
        help_text="Información adicional en formato JSON (dict)"
    )
    
    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['rut']),
            models.Index(fields=['identificador_hash']),
            models.Index(fields=['estado_actual']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['nivel_urgencia']),
            models.Index(fields=['apellido_paterno', 'apellido_materno']),
        ]
    
    def __str__(self):
        return f"{self.nombre_completo} - RUT: {self.rut} - {self.get_estado_actual_display()}"
    
    # ============================================
    # PROPIEDADES Y MÉTODOS CALCULADOS
    # ============================================
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del paciente"""
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"
    
    @property
    def direccion_completa(self):
        """Retorna la dirección completa formateada"""
        direccion = f"{self.direccion_calle}, {self.direccion_comuna}, {self.direccion_ciudad}"
        if self.direccion_codigo_postal:
            direccion += f", {self.direccion_codigo_postal}"
        direccion += f", {self.get_direccion_region_display()}"
        return direccion
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar RUT chileno
        if self.rut:
            if not self.validar_rut(self.rut):
                raise ValidationError({
                    'rut': 'El RUT ingresado no es válido. Verifique el dígito verificador.'
                })
        
        # Asegurar que metadatos_adicionales sea dict
        if not isinstance(self.metadatos_adicionales, dict):
            raise ValidationError({
                'metadatos_adicionales': 'Debe ser un diccionario (dict), no una lista'
            })
        
        # Validar edad vs fecha de nacimiento
        if self.fecha_nacimiento:
            edad_calculada = self.calcular_edad_desde_fecha()
            if edad_calculada < 0 or edad_calculada > 150:
                raise ValidationError({
                    'fecha_nacimiento': 'La fecha de nacimiento no es válida'
                })
        
        # Validar peso si está presente
        if self.peso and (self.peso < 0 or self.peso > 500):
            raise ValidationError({
                'peso': 'El peso debe estar entre 0 y 500 kg'
            })
        
        # Validar altura si está presente
        if self.altura and (self.altura < 0 or self.altura > 300):
            raise ValidationError({
                'altura': 'La altura debe estar entre 0 y 300 cm'
            })
    
    def save(self, *args, **kwargs):
        """Override save para calcular campos automáticos"""
        # Generar hash del RUT si no existe
        if self.rut and not self.identificador_hash:
            self.identificador_hash = self.generar_hash_rut(self.rut)
        
        # Calcular edad desde fecha de nacimiento
        if self.fecha_nacimiento:
            self.edad = self.calcular_edad_desde_fecha()
        
        # Asegurar que metadatos_adicionales sea dict
        if not isinstance(self.metadatos_adicionales, dict):
            self.metadatos_adicionales = {}
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    # ============================================
    # MÉTODOS DE VALIDACIÓN RUT CHILENO
    # ============================================
    
    @staticmethod
    def validar_rut(rut):
        """
        Valida un RUT chileno con su dígito verificador.
        Formato esperado: XX.XXX.XXX-X
        """
        # Limpiar el RUT
        rut_limpio = rut.replace('.', '').replace('-', '')
        
        if len(rut_limpio) < 2:
            return False
        
        # Separar cuerpo y dígito verificador
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1].upper()
        
        # Validar que el cuerpo sea numérico
        if not cuerpo.isdigit():
            return False
        
        # Calcular dígito verificador
        suma = 0
        multiplicador = 2
        
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplicador
            multiplicador += 1
            if multiplicador == 8:
                multiplicador = 2
        
        resto = suma % 11
        dv_calculado = 11 - resto
        
        # Convertir a formato string
        if dv_calculado == 11:
            dv_calculado = '0'
        elif dv_calculado == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(dv_calculado)
        
        return dv == dv_calculado
    
    @staticmethod
    def formatear_rut(rut_sin_formato):
        """
        Formatea un RUT sin puntos ni guión al formato chileno XX.XXX.XXX-X
        Ejemplo: 12345678K -> 12.345.678-K
        """
        # Limpiar el RUT
        rut_limpio = rut_sin_formato.replace('.', '').replace('-', '').upper()
        
        if len(rut_limpio) < 2:
            return rut_sin_formato
        
        # Separar cuerpo y dígito verificador
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        
        # Formatear con puntos
        cuerpo_formateado = ""
        for i, digito in enumerate(reversed(cuerpo)):
            if i > 0 and i % 3 == 0:
                cuerpo_formateado = "." + cuerpo_formateado
            cuerpo_formateado = digito + cuerpo_formateado
        
        return f"{cuerpo_formateado}-{dv}"
    
    @staticmethod
    def generar_hash_rut(rut):
        """Genera un hash SHA-256 del RUT para proteger privacidad"""
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        return hashlib.sha256(rut_limpio.encode()).hexdigest()
    
    # ============================================
    # MÉTODOS DE CÁLCULO
    # ============================================
    
    def calcular_edad_desde_fecha(self):
        """Calcula la edad desde la fecha de nacimiento"""
        if not self.fecha_nacimiento:
            return 0
        
        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year
        
        # Ajustar si aún no ha cumplido años este año
        if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        
        return edad
    
    def calcular_imc(self):
        """Calcula el Índice de Masa Corporal si hay datos disponibles"""
        if self.peso and self.altura:
            altura_metros = self.altura / 100
            imc = float(self.peso) / (altura_metros ** 2)
            return round(imc, 2)
        return None
    
    def obtener_categoria_imc(self):
        """Retorna la categoría del IMC"""
        imc = self.calcular_imc()
        if not imc:
            return "No disponible"
        
        if imc < 18.5:
            return "Bajo peso"
        elif 18.5 <= imc < 25:
            return "Peso normal"
        elif 25 <= imc < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"
    
    def calcular_tiempo_total(self):
        """Calcula el tiempo total desde el ingreso hasta ahora"""
        if self.fecha_ingreso:
            return timezone.now() - self.fecha_ingreso
        return None
    
    # ============================================
    # MÉTODOS DE ESTADO
    # ============================================
    
    def actualizar_estado(self, nuevo_estado):
        """Actualiza el estado del paciente con validación"""
        if nuevo_estado in dict(self.ESTADO_CHOICES):
            self.estado_actual = nuevo_estado
            self.save()
            return True
        return False
    
    def is_proceso_completo(self):
        """Verifica si el proceso del paciente está completo"""
        return self.estado_actual == 'ALTA_COMPLETA'
    
    def is_proceso_pausado(self):
        """Verifica si el proceso está pausado"""
        return self.estado_actual == 'PROCESO_PAUSADO'
    
    # ============================================
    # MÉTODOS DE INFORMACIÓN MÉDICA
    # ============================================
    
    def tiene_alergias(self):
        """Verifica si el paciente tiene alergias registradas"""
        return bool(self.alergias and self.alergias.strip())
    
    def tiene_condiciones_preexistentes(self):
        """Verifica si el paciente tiene condiciones preexistentes"""
        return bool(self.condiciones_preexistentes and self.condiciones_preexistentes.strip())
    
    def obtener_informacion_completa(self):
        """Retorna un diccionario con toda la información del paciente"""
        return {
            # Identificación
            'id': str(self.id),
            'rut': self.rut,
            'identificador_hash': self.identificador_hash[:12],
            
            # Datos personales
            'nombre_completo': self.nombre_completo,
            'nombre': self.nombre,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'fecha_nacimiento': self.fecha_nacimiento,
            'edad': self.edad,
            'genero': self.get_genero_display(),
            
            # Contacto
            'correo': self.correo,
            'telefono': self.telefono,
            'telefono_emergencia': self.telefono_emergencia,
            'nombre_contacto_emergencia': self.nombre_contacto_emergencia,
            
            # Dirección
            'direccion_completa': self.direccion_completa,
            'direccion_calle': self.direccion_calle,
            'direccion_comuna': self.direccion_comuna,
            'direccion_ciudad': self.direccion_ciudad,
            'direccion_region': self.get_direccion_region_display(),
            'direccion_codigo_postal': self.direccion_codigo_postal,
            
            # Seguro médico
            'seguro_medico': self.get_seguro_medico_display(),
            'numero_beneficiario': self.numero_beneficiario,
            
            # Información médica
            'tipo_sangre': self.get_tipo_sangre_display(),
            'peso': float(self.peso) if self.peso else None,
            'altura': self.altura,
            'imc': self.calcular_imc(),
            'categoria_imc': self.obtener_categoria_imc(),
            'alergias': self.alergias if self.tiene_alergias() else "Sin alergias registradas",
            'condiciones_preexistentes': self.condiciones_preexistentes if self.tiene_condiciones_preexistentes() else "Sin condiciones registradas",
            'medicamentos': self.medicamentos_actuales if self.medicamentos_actuales else "Sin medicamentos registrados",
            
            # Estado
            'estado_actual': self.get_estado_actual_display(),
            'nivel_urgencia': self.get_nivel_urgencia_display(),
            'fecha_ingreso': self.fecha_ingreso,
            'tiempo_en_sistema': self.calcular_tiempo_total(),
            'activo': self.activo,
        }
    
    def obtener_nombre_display(self):
        """Método para compatibilidad con código anterior"""
        return self.nombre_completo