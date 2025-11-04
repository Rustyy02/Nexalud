# backend/users/admin.py - VERSIÓN SIMPLIFICADA
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django import forms
from .models import User

class CustomUserCreationForm(forms.ModelForm):
    """Formulario personalizado para crear usuarios"""
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese una contraseña segura'
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput,
        help_text='Ingrese la misma contraseña para verificación'
    )
    
    email = forms.EmailField(
        required=True,
        help_text='Requerido. Use un dominio válido: @nexalud.admin.com, @nexalud.secretario.com, @nexalud.medico.com'
    )
    
    especialidad = forms.ChoiceField(
        choices=[('', '---------')] + User.ESPECIALIDAD_CHOICES,
        required=False,
        help_text='Solo requerido para médicos'
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'rut', 'especialidad')
    
    def _get_rol_from_email(self, email):
        """Determinar el rol basado en el dominio del email"""
        if not email:
            return None
        
        if '@nexalud.admin.com' in email:
            return 'ADMINISTRADOR'
        elif '@nexalud.secretario.com' in email:
            return 'SECRETARIA'
        elif '@nexalud.medico.com' in email:
            return 'MEDICO'
        return None
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        
        return password2
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError('Este correo ya está registrado.')
            
            dominios_validos = ['@nexalud.admin.com', '@nexalud.secretario.com', '@nexalud.medico.com']
            if not any(dominio in email for dominio in dominios_validos):
                raise forms.ValidationError('Debe usar un dominio válido.')
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        especialidad = cleaned_data.get('especialidad')
        
        rol = self._get_rol_from_email(email)
        
        if email and rol:
            if rol == 'MEDICO':
                if not especialidad:
                    self.add_error('especialidad', 'La especialidad es obligatoria para médicos.')
            else:
                if especialidad:
                    self.add_error('especialidad', 'Solo los médicos pueden tener especialidad.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        
        email = self.cleaned_data.get('email')
        rol = self._get_rol_from_email(email)
        
        if rol:
            user.rol = rol
            if rol != 'MEDICO':
                user.especialidad = None
        
        if commit:
            user.save()
        
        return user

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'rol', 'get_especialidad_medico', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('rol', 'especialidad', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'rut')
    ordering = ('username',)
    
    def get_especialidad_medico(self, obj):
        if obj.rol == 'MEDICO' and obj.especialidad:
            return obj.get_especialidad_display()
        return '-'
    get_especialidad_medico.short_description = 'Especialidad'
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Información Personal', {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'rut'),
        }),
        ('Especialidad Médica', {
            'classes': ('wide',),
            'fields': ('especialidad',),
            'description': 'El rol se asigna automáticamente. Si usa @nexalud.medico.com, debe seleccionar especialidad.',
        }),
        ('Permisos', {
            'classes': ('wide',),
            'fields': ('is_active', 'is_staff', 'is_superuser'),
        }),
    )
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'rut')}),
        ('Rol y Especialidad', {'fields': ('rol', 'especialidad')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ('last_login', 'date_joined')

admin.site.unregister(User) if admin.site.is_registered(User) else None
admin.site.register(User, CustomUserAdmin)