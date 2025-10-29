# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import User

class CustomUserCreationForm(UserCreationForm):
    """Formulario personalizado para crear usuarios"""
    email = forms.EmailField(
        required=True,
        help_text='Requerido. Use un dominio válido: @nexalud.admin.com, @nexalud.secretario.com, @nexalud.medico.com'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Permitir cualquier correo para superusuarios
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Este correo ya está registrado.')
        return email

class CustomUserChangeForm(UserChangeForm):
    """Formulario personalizado para editar usuarios"""
    class Meta:
        model = User
        fields = '__all__'

class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # Campos a mostrar en la lista
    list_display = ('username', 'email', 'rol', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')
    
    # Campos de búsqueda
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Ordenamiento
    ordering = ('username',)
    
    # Configuración de los fieldsets (vista de edición)
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'rut')
        }),
        ('Rol y Permisos', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'El rol se asigna automáticamente según el dominio del correo.'
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Configuración para agregar usuario (vista de creación)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'rut'),
        }),
        ('Permisos', {
            'fields': ('is_staff', 'is_superuser'),
            'description': 'El rol se asignará automáticamente según el dominio del correo.'
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'rol')
    
    def get_readonly_fields(self, request, obj=None):
        """Hacer el rol de solo lectura ya que se asigna automáticamente"""
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Si estamos editando
            readonly.append('rol')
        return readonly

# Registrar el modelo con la configuración personalizada
admin.site.unregister(User) if admin.site.is_registered(User) else None
admin.site.register(User, CustomUserAdmin)