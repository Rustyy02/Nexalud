# backend/pacientes/models.py - VERSIÓN MEJORADA CON ESTADOS SEPARADOS
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
    Modelo mejorado para pacientes con separación clara de:
    - estado_sistema: Estado administrativo en el sistema
    - etapa_actual: Etapa clínica en la que se encuentra (vinculado a RutaClinica)
    """
    
    # ============================================
    # ESTADOS DEL SISTEMA (Administrativos)
    # ============================================
    ESTADO_SISTEMA_CHOICES = [
        ('ACTIVO', 'Activo en el Sistema'),
        ('PAUSADO', 'Proceso Pausado'),
        ('INACTIVO', 'Inactivo'),
        ('DADO_ALTA', 'Dado de Alta'),
        ('DERIVADO', 'Derivado a Otro Centro'),
        ('FALLECIDO', 'Fallecido'),
    ]
    
    # ============================================
    # ETAPAS CLÍNICAS (Sincronizadas con RutaClinica)
    # ============================================
    ETAPA_CLINICA_CHOICES = [
        ('ADMISION', 'Admisión/Recepción'),
        ('TRIAJE', 'Triaje'),
        ('CONSULTA_MEDICA', 'Consulta Médica'),
        ('PROCESO_EXAMEN', 'Proceso del Examen'),
        ('REVISION_EXAMEN', 'Revisión del Examen'),
        ('HOSPITALIZACION', 'Hospitalización'),
        ('OPERACION', 'Operación'),
        ('RECUPERACION', 'Recuperación'),
        ('ALTA', 'Alta Médica'),
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
    
    # Validadores
    rut_validator = RegexValidator(
        regex=r'^\d{1,2}\.?\d{3}\.?\d{3}-[0-9kK]$',
        message='El RUT debe estar en formato chileno: XX.XXX.XXX-X'
    )
    
    telefono_validator = RegexValidator(
        regex=r'^\+56\d{9}$',
        message='El teléfono debe estar en formato chileno: +56912345678'
    )
    
    # ============================================
    # CAMPOS DEL MODELO
    # ============================================
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    rut = models.CharField(
        max_length=16,
        unique=True,
        validators=[rut_validator],
        default='',
        help_text="RUT en formato chileno XX.XXX.XXX-X"
    )
    
    identificador_hash = models.CharField(
        max_length=64, 
        unique=True,
        db_index=True,
        editable=False,
        default='',
        help_text="Hash SHA-256 del RUT para proteger privacidad"
    )
    
    # Datos Personales
    nombre = models.CharField(max_length=100, null=True, blank=True, default='')
    apellido_paterno = models.CharField(max_length=100, null=True, blank=True, default='')
    apellido_materno = models.CharField(max_length=100, blank=True, null=True, default='')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    edad = models.PositiveIntegerField(editable=False)
    genero = models.CharField(max_length=2, choices=GENERO_CHOICES, default='NE')
    
    # Contacto
    correo = models.EmailField(
        max_length=254, blank=True, null=True, default='',
        validators=[EmailValidator()]
    )
    telefono = models.CharField(
        max_length=13, null=True, blank=True, default='',
        validators=[telefono_validator]
    )
    telefono_emergencia = models.CharField(
        max_length=13, blank=True, null=True,
        validators=[telefono_validator]
    )
    nombre_contacto_emergencia = models.CharField(
        max_length=200, blank=True, null=True
    )
    
    # Dirección
    direccion_calle = models.CharField(max_length=255, null=True, blank=True, default='')
    direccion_comuna = models.CharField(max_length=100, null=True, blank=True, default='')
    direccion_ciudad = models.CharField(max_length=100, null=True, blank=True, default='')
    direccion_region = models.CharField(
        max_length=5, null=True, blank=True, default='',
        choices=REGION_CHOICES
    )
    direccion_codigo_postal = models.CharField(
        max_length=10, blank=True, null=True, default='Sin proporcionar'
    )
    
    # Seguro Médico
    seguro_medico = models.CharField(
        max_length=30, choices=SEGURO_MEDICO_CHOICES, default='PARTICULAR'
    )
    numero_beneficiario = models.CharField(
        max_length=50, blank=True, default='Sin proporcionar'
    )
    
    # Información Médica
    tipo_sangre = models.CharField(
        max_length=15, choices=TIPO_SANGRE_CHOICES, default='DESCONOCIDO'
    )
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, default=None, blank=True
    )
    altura = models.PositiveIntegerField(null=True, blank=True)
    alergias = models.TextField(blank=True)
    condiciones_preexistentes = models.TextField(blank=True)
    medicamentos_actuales = models.TextField(blank=True)
    
    # ============================================
    # CAMPOS MEJORADOS: Estado y Etapa Separados
    # ============================================
    
    # Estado del Sistema (Administrativo)
    estado_sistema = models.CharField(
        max_length=20,
        choices=ESTADO_SISTEMA_CHOICES,
        default='ACTIVO',
        db_index=True,
        help_text="Estado administrativo del paciente en el sistema"
    )
    
    # Etapa Clínica Actual (Sincronizada con RutaClinica)
    etapa_actual = models.CharField(
        max_length=30,
        choices=ETAPA_CLINICA_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Etapa clínica actual del paciente (vinculada a su ruta clínica)"
    )
    
    # Nivel de Urgencia
    nivel_urgencia = models.CharField(
        max_length=10,
        choices=URGENCIA_CHOICES,
        default='MEDIA'
    )
    
    # Control de Pausa
    esta_pausado = models.BooleanField(
        default=False,
        help_text="Indica si el proceso del paciente está pausado"
    )
    motivo_pausa = models.TextField(
        blank=True,
        help_text="Motivo por el cual se pausó el proceso"
    )
    fecha_pausa = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se pausó el proceso"
    )
    
    # Timestamps
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    # Metadatos
    metadatos_adicionales = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['rut']),
            models.Index(fields=['identificador_hash']),
            models.Index(fields=['estado_sistema']),
            models.Index(fields=['etapa_actual']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['nivel_urgencia']),
            models.Index(fields=['apellido_paterno', 'apellido_materno']),
        ]
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.get_estado_sistema_display()} - {self.get_etapa_actual_display() or 'Sin etapa'}"
    
    # ============================================
    # PROPIEDADES
    # ============================================
    
    @property
    def nombre_completo(self):
        if self.apellido_materno:
            return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}"
        return f"{self.nombre} {self.apellido_paterno}"
    
    @property
    def direccion_completa(self):
        direccion = f"{self.direccion_calle}, {self.direccion_comuna}, {self.direccion_ciudad}"
        if self.direccion_codigo_postal:
            direccion += f", {self.direccion_codigo_postal}"
        direccion += f", {self.get_direccion_region_display()}"
        return direccion
    
    # ============================================
    # MÉTODOS DE ESTADO
    # ============================================
    
    def pausar_proceso(self, motivo=''):
        """Pausa el proceso del paciente"""
        self.esta_pausado = True
        self.estado_sistema = 'PAUSADO'
        self.motivo_pausa = motivo
        self.fecha_pausa = timezone.now()
        self.save()
    
    def reanudar_proceso(self):
        """Reanuda el proceso del paciente"""
        self.esta_pausado = False
        self.estado_sistema = 'ACTIVO'
        self.motivo_pausa = ''
        self.fecha_pausa = None
        self.save()
    
    def actualizar_etapa(self, nueva_etapa):
        """
        Actualiza la etapa clínica del paciente.
        Este método es llamado automáticamente por RutaClinica.
        """
        if nueva_etapa in dict(self.ETAPA_CLINICA_CHOICES):
            self.etapa_actual = nueva_etapa
            self.save(update_fields=['etapa_actual', 'fecha_actualizacion'])
            return True
        return False
    
    def dar_alta(self):
        """Da de alta al paciente"""
        self.estado_sistema = 'DADO_ALTA'
        self.etapa_actual = 'ALTA'
        self.save()
    
    # ============================================
    # MÉTODOS DE VALIDACIÓN Y CÁLCULO
    # ============================================
    
    def clean(self):
        super().clean()
        if self.rut:
            if not self.validar_rut(self.rut):
                raise ValidationError({
                    'rut': 'El RUT ingresado no es válido.'
                })
        if not isinstance(self.metadatos_adicionales, dict):
            raise ValidationError({
                'metadatos_adicionales': 'Debe ser un diccionario'
            })
    
    def save(self, *args, **kwargs):
        if self.rut and not self.identificador_hash:
            self.identificador_hash = self.generar_hash_rut(self.rut)
        elif not self.identificador_hash:
            temp_id = str(uuid.uuid4())
            self.identificador_hash = hashlib.sha256(temp_id.encode()).hexdigest()
        
        if self.fecha_nacimiento:
            self.edad = self.calcular_edad_desde_fecha()
        else:
            self.edad = 0
        
        if not isinstance(self.metadatos_adicionales, dict):
            self.metadatos_adicionales = {}
        
        # Sincronizar estado pausado con estado_sistema
        if self.esta_pausado and self.estado_sistema != 'PAUSADO':
            self.estado_sistema = 'PAUSADO'
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def validar_rut(rut):
        rut_limpio = rut.replace('.', '').replace('-', '').replace(' ', '').upper()
        if len(rut_limpio) < 2:
            return False
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        if not cuerpo.isdigit():
            return False
        suma = 0
        multiplicador = 2
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplicador
            multiplicador += 1
            if multiplicador > 7:
                multiplicador = 2
        resto = suma % 11
        dv_calculado = 11 - resto
        if dv_calculado == 11:
            dv_esperado = '0'
        elif dv_calculado == 10:
            dv_esperado = 'K'
        else:
            dv_esperado = str(dv_calculado)
        return dv_esperado == dv.upper()
    
    @staticmethod
    def formatear_rut(rut_sin_formato):
        rut_limpio = rut_sin_formato.replace('.', '').replace('-', '').upper()
        if len(rut_limpio) < 2:
            return rut_sin_formato
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        cuerpo_formateado = ""
        for i, digito in enumerate(reversed(cuerpo)):
            if i > 0 and i % 3 == 0:
                cuerpo_formateado = "." + cuerpo_formateado
            cuerpo_formateado = digito + cuerpo_formateado
        return f"{cuerpo_formateado}-{dv}"
    
    @staticmethod
    def generar_hash_rut(rut):
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        return hashlib.sha256(rut_limpio.encode()).hexdigest()
    
    def calcular_edad_desde_fecha(self):
        if not self.fecha_nacimiento:
            return 0
        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        return edad
    
    def calcular_imc(self):
        if self.peso and self.altura:
            altura_metros = self.altura / 100
            imc = float(self.peso) / (altura_metros ** 2)
            return round(imc, 2)
        return None
    
    def obtener_categoria_imc(self):
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
        if self.fecha_ingreso:
            return timezone.now() - self.fecha_ingreso
        return None
    
    def tiene_alergias(self):
        return bool(self.alergias and self.alergias.strip())
    
    def tiene_condiciones_preexistentes(self):
        return bool(self.condiciones_preexistentes and self.condiciones_preexistentes.strip())
    
    def obtener_informacion_completa(self):
        return {
            'id': str(self.id),
            'rut': self.rut,
            'identificador_hash': self.identificador_hash[:12],
            'nombre_completo': self.nombre_completo,
            'nombre': self.nombre,
            'apellido_paterno': self.apellido_paterno,
            'apellido_materno': self.apellido_materno,
            'fecha_nacimiento': self.fecha_nacimiento,
            'edad': self.edad,
            'genero': self.get_genero_display(),
            'correo': self.correo,
            'telefono': self.telefono,
            'telefono_emergencia': self.telefono_emergencia,
            'nombre_contacto_emergencia': self.nombre_contacto_emergencia,
            'direccion_completa': self.direccion_completa,
            'direccion_calle': self.direccion_calle,
            'direccion_comuna': self.direccion_comuna,
            'direccion_ciudad': self.direccion_ciudad,
            'direccion_region': self.get_direccion_region_display(),
            'direccion_codigo_postal': self.direccion_codigo_postal,
            'seguro_medico': self.get_seguro_medico_display(),
            'numero_beneficiario': self.numero_beneficiario,
            'tipo_sangre': self.get_tipo_sangre_display(),
            'peso': float(self.peso) if self.peso else None,
            'altura': self.altura,
            'imc': self.calcular_imc(),
            'categoria_imc': self.obtener_categoria_imc(),
            'alergias': self.alergias if self.tiene_alergias() else "Sin alergias",
            'condiciones_preexistentes': self.condiciones_preexistentes if self.tiene_condiciones_preexistentes() else "Sin condiciones",
            'medicamentos': self.medicamentos_actuales if self.medicamentos_actuales else "Sin medicamentos",
            'estado_sistema': self.get_estado_sistema_display(),
            'etapa_actual': self.get_etapa_actual_display() if self.etapa_actual else 'Sin etapa asignada',
            'nivel_urgencia': self.get_nivel_urgencia_display(),
            'fecha_ingreso': self.fecha_ingreso,
            'tiempo_en_sistema': self.calcular_tiempo_total(),
            'activo': self.activo,
            'esta_pausado': self.esta_pausado,
            'motivo_pausa': self.motivo_pausa if self.esta_pausado else None,
        }
    
    def obtener_nombre_display(self):
        return self.nombre_completo
    
    # backend/pacientes/models.py - ACTUALIZADO CON TIPO DE ATENCIÓN
# (Solo mostrando los cambios necesarios)

# ... (código anterior se mantiene igual) ...

class Paciente(models.Model):
    # ... (todos los campos anteriores se mantienen) ...
    
    # ============================================
    # NUEVO: TIPO DE ATENCIÓN
    # ============================================
    
    tipo_atencion = models.ForeignKey(
        'tipos_atencion.TipoAtencion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pacientes',
        help_text="Tipo de atención asignado al paciente"
    )
    
    motivo_consulta = models.TextField(
        blank=True,
        help_text="Motivo principal de la consulta/atención"
    )
    
    diagnostico_presuntivo = models.TextField(
        blank=True,
        help_text="Diagnóstico presuntivo o inicial"
    )
    
    requiere_especialista = models.BooleanField(
        default=False,
        help_text="Indica si requiere atención por especialista"
    )
    
    # ... (resto del código se mantiene igual) ...
    
    def asignar_tipo_atencion_automatico(self):
        """
        Asigna automáticamente el tipo de atención más apropiado
        según el nivel de urgencia y requerimientos.
        """
        from tipos_atencion.models import TipoAtencion
        
        tipo_sugerido = TipoAtencion.obtener_tipo_sugerido(
            nivel_urgencia=self.nivel_urgencia,
            especialista_requerido=self.requiere_especialista
        )
        
        if tipo_sugerido:
            self.tipo_atencion = tipo_sugerido
            self.save(update_fields=['tipo_atencion'])
            return True
        
        return False
    
    def obtener_informacion_completa(self):
        """Versión actualizada con tipo de atención"""
        info = super().obtener_informacion_completa()  # Llamar al método original
        
        # Añadir información del tipo de atención
        if self.tipo_atencion:
            info['tipo_atencion'] = {
                'codigo': self.tipo_atencion.codigo,
                'nombre': self.tipo_atencion.nombre,
                'nivel': self.tipo_atencion.get_nivel_display(),
                'complejidad': self.tipo_atencion.nivel_complejidad,
            }
        else:
            info['tipo_atencion'] = None
        
        info['motivo_consulta'] = self.motivo_consulta
        info['diagnostico_presuntivo'] = self.diagnostico_presuntivo
        
        return info