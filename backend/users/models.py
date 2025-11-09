from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('SECRETARIA', 'Secretaria'),
        ('MEDICO', 'Médico'),
    ]
    
    # Opciones de especialidades médicas
    ESPECIALIDAD_CHOICES = [
        ('MEDICINA_GENERAL', 'Medicina General'),
        ('PEDIATRIA', 'Pediatría'),
        ('CARDIOLOGIA', 'Cardiología'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('GINECOLOGIA', 'Ginecología'),
        ('TRAUMATOLOGIA', 'Traumatología'),
        ('OFTALMOLOGIA', 'Oftalmología'),
        ('OTORRINOLARINGOLOGIA', 'Otorrinolaringología'),
        ('NEUROLOGIA', 'Neurología'),
        ('PSIQUIATRIA', 'Psiquiatría'),
        ('URGENCIAS', 'Medicina de Urgencias'),
        ('MEDICINA_INTERNA', 'Medicina Interna'),
        ('CIRUGIA_GENERAL', 'Cirugía General'),
        ('ANESTESIOLOGIA', 'Anestesiología'),
        ('RADIOLOGIA', 'Radiología'),
    ]
    
    @property
    def nombre_completo(self):
        # Devuelve el nombre completo del usuario
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    email = models.EmailField('Correo electrónico', unique=True)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    especialidad = models.CharField(
        max_length=30, 
        choices=ESPECIALIDAD_CHOICES, 
        null=True, 
        blank=True,
        verbose_name='Especialidad Médica',
        help_text='Solo aplicable para usuarios con rol Médico'
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def _get_rol_from_email(self):
        # Determinar el rol basado en el dominio del email
        if not self.email:
            return None
        
        if '@nexalud.admin.com' in self.email:
            return 'ADMINISTRADOR'
        elif '@nexalud.secretario.com' in self.email:
            return 'SECRETARIA'
        elif '@nexalud.medico.com' in self.email:
            return 'MEDICO'
        return None
    
    def clean(self):
        super().clean()
        
        # Si es superusuario, no validar
        if self.is_superuser:
            return
        
        # Calcular el rol desde el email ANTES de validar
        if self.email and not self.rol:
            calculated_rol = self._get_rol_from_email()
            if calculated_rol:
                self.rol = calculated_rol
        
        # Ahora validar con el rol ya asignado
        if self.rol != 'MEDICO' and self.especialidad:
            raise ValidationError({
                'especialidad': 'Solo los usuarios con rol Médico pueden tener especialidad.'
            })
        
        # Validación: si es médico, debe tener especialidad
        if self.rol == 'MEDICO' and not self.especialidad:
            raise ValidationError({
                'especialidad': 'Los médicos deben tener una especialidad asignada.'
            })
        
        # Validar el correo
        if self.email:
            # Extraer dominio del correo
            dominio = self.email.split('@')[-1] if '@' in self.email else ''
            
            # Validar que el correo tenga un dominio válido
            dominios_validos = [
                'nexalud.admin.com',
                'nexalud.secretario.com',
                'nexalud.medico.com'
            ]
            
            if dominio not in dominios_validos:
                raise ValidationError({
                    'email': f'El correo debe pertenecer a uno de estos dominios: {", ".join(dominios_validos)}'
                })
    
    def save(self, *args, **kwargs):
        # Si es superusuario, asignar rol ADMINISTRADOR automáticamente
        if self.is_superuser:
            self.rol = 'ADMINISTRADOR'
            self.is_staff = True
            self.especialidad = None  # Los administradores no tienen especialidad
        else:
            # Asignar rol basado en email si no está asignado
            if not self.rol and self.email:
                self.rol = self._get_rol_from_email()
            
            # Ejecutar validaciones
            self.full_clean()
            
            # Si es administrador, debe tener is_staff=True
            if self.rol == 'ADMINISTRADOR':
                self.is_staff = True
            
            # Limpiar especialidad si no es médico
            if self.rol != 'MEDICO':
                self.especialidad = None
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        base = f"{self.username} - {self.get_rol_display() if self.rol else 'Sin rol'}"
        if self.rol == 'MEDICO' and self.especialidad:
            base += f" ({self.get_especialidad_display()})"
        return base