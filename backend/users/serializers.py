from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'rol',
            'rol_display',
            'especialidad',
            'especialidad_display',
            'is_staff', 
            'is_superuser'
        ]
        read_only_fields = ['rol_display', 'especialidad_display']
    
    def to_representation(self, instance):
        """Asegurar que el rol siempre se incluya en la respuesta"""
        data = super().to_representation(instance)
        
        # Si el usuario es superusuario y no tiene rol, asignar ADMINISTRADOR
        if instance.is_superuser and not data.get('rol'):
            data['rol'] = 'ADMINISTRADOR'
            data['rol_display'] = 'Administrador'
        
        # Si no es médico, no mostrar especialidad
        if instance.rol != 'MEDICO':
            data['especialidad'] = None
            data['especialidad_display'] = None
        
        #Imprimir los datos serializados
        print(f"Datos serializados para {instance.username}: {data}")
        
        return data
    
    def validate(self, data):
        """Validar que solo médicos tengan especialidad"""
        rol = data.get('rol', self.instance.rol if self.instance else None)
        especialidad = data.get('especialidad')
        
        if rol != 'MEDICO' and especialidad:
            raise serializers.ValidationError({
                'especialidad': 'Solo los usuarios con rol Médico pueden tener especialidad.'
            })
        
        if rol == 'MEDICO' and not especialidad:
            raise serializers.ValidationError({
                'especialidad': 'Los médicos deben tener una especialidad asignada.'
            })
        
        return data