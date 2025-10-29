# backend/users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('SECRETARIA', 'Secretaria'),
        ('MEDICO', 'Médico'),
    ]
    
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True)
    email = models.EmailField('Correo electrónico', unique=True)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def clean(self):
        super().clean()
        
        # Si es superusuario, no validar correo
        if self.is_superuser:
            return
        
        # Si no es superusuario, validar el correo
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
            
            # Asignar rol automáticamente según el dominio
            if dominio == 'nexalud.admin.com':
                self.rol = 'ADMINISTRADOR'
            elif dominio == 'nexalud.secretario.com':
                self.rol = 'SECRETARIA'
            elif dominio == 'nexalud.medico.com':
                self.rol = 'MEDICO'
    
    def save(self, *args, **kwargs):
        # Si es superusuario, asignar rol ADMINISTRADOR automáticamente
        if self.is_superuser:
            self.rol = 'ADMINISTRADOR'
        else:
            # Ejecutar validaciones solo si no es superusuario
            self.full_clean()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.username} - {self.get_rol_display() if self.rol else 'Sin rol'}"