# backend/pacientes/models.py - VERSIÓN MEJORADA
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class Paciente(models.Model):
    """
    Modelo mejorado para gestionar pacientes en el sistema Nexalud.
    Usa hash del identificador para proteger privacidad.
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identificador_hash = models.CharField(
        max_length=64, 
        unique=True, 
        help_text="Hash del RUT/identificador para proteger privacidad"
    )
    
    # Datos básicos
    edad = models.PositiveIntegerField(help_text="Edad del paciente en años")
    genero = models.CharField(max_length=2, choices=GENERO_CHOICES, default='NE')
    
    # NUEVO: Campos médicos adicionales
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
    
    # Estado y seguimiento
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
    
    # Metadatos adicionales para flexibilidad - CORREGIDO
    metadatos_adicionales = models.JSONField(
        default=dict,  # IMPORTANTE: Debe ser dict, no list
        blank=True,
        help_text="Información adicional en formato JSON (dict)"
    )
    
    class Meta:
        db_table = 'pacientes'
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['identificador_hash']),
            models.Index(fields=['estado_actual']),
            models.Index(fields=['fecha_ingreso']),
            models.Index(fields=['nivel_urgencia']),
        ]
    
    def __str__(self):
        nombre = self.obtener_nombre_display()
        return f"{nombre} - {self.get_estado_actual_display()}"
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # VALIDACIÓN CRÍTICA: Asegurar que metadatos_adicionales sea dict
        if not isinstance(self.metadatos_adicionales, dict):
            raise ValidationError({
                'metadatos_adicionales': 'Debe ser un diccionario (dict), no una lista'
            })
        
        # Validar edad razonable
        if self.edad < 0 or self.edad > 150:
            raise ValidationError({
                'edad': 'La edad debe estar entre 0 y 150 años'
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
        """Override save para asegurar metadatos_adicionales correctos"""
        # CRÍTICO: Asegurar que metadatos_adicionales sea dict
        if not isinstance(self.metadatos_adicionales, dict):
            self.metadatos_adicionales = {}
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def obtener_nombre_display(self):
        """Obtiene el nombre del paciente de forma segura"""
        if isinstance(self.metadatos_adicionales, dict):
            return self.metadatos_adicionales.get(
                'nombre', 
                f'Paciente {self.identificador_hash[:8]}'
            )
        return f'Paciente {self.identificador_hash[:8]}'
    
    def obtener_estado_actual(self):
        """Retorna el estado actual del paciente"""
        return self.estado_actual
    
    def actualizar_estado(self, nuevo_estado):
        """Actualiza el estado del paciente con validación"""
        if nuevo_estado in dict(self.ESTADO_CHOICES):
            self.estado_actual = nuevo_estado
            self.save()
            return True
        return False
    
    def calcular_tiempo_total(self):
        """Calcula el tiempo total desde el ingreso hasta ahora"""
        if self.fecha_ingreso:
            return timezone.now() - self.fecha_ingreso
        return None
    
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
    
    def is_proceso_completo(self):
        """Verifica si el proceso del paciente está completo"""
        return self.estado_actual == 'ALTA_COMPLETA'
    
    def is_proceso_pausado(self):
        """Verifica si el proceso está pausado"""
        return self.estado_actual == 'PROCESO_PAUSADO'
    
    def tiene_alergias(self):
        """Verifica si el paciente tiene alergias registradas"""
        return bool(self.alergias and self.alergias.strip())
    
    def tiene_condiciones_preexistentes(self):
        """Verifica si el paciente tiene condiciones preexistentes"""
        return bool(self.condiciones_preexistentes and self.condiciones_preexistentes.strip())
    
    def obtener_informacion_medica_completa(self):
        """Retorna un diccionario con toda la información médica"""
        return {
            'identificador': self.identificador_hash[:12],
            'nombre': self.obtener_nombre_display(),
            'edad': self.edad,
            'genero': self.get_genero_display(),
            'tipo_sangre': self.get_tipo_sangre_display(),
            'peso': float(self.peso) if self.peso else None,
            'altura': self.altura,
            'imc': self.calcular_imc(),
            'categoria_imc': self.obtener_categoria_imc(),
            'alergias': self.alergias if self.tiene_alergias() else "Sin alergias registradas",
            'condiciones_preexistentes': self.condiciones_preexistentes if self.tiene_condiciones_preexistentes() else "Sin condiciones registradas",
            'medicamentos': self.medicamentos_actuales if self.medicamentos_actuales else "Sin medicamentos registrados",
            'estado_actual': self.get_estado_actual_display(),
            'nivel_urgencia': self.get_nivel_urgencia_display(),
            'fecha_ingreso': self.fecha_ingreso,
            'tiempo_en_sistema': self.calcular_tiempo_total(),
        }