# backend/users/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'rol',  # ✅ IMPORTANTE: El campo rol debe estar aquí
            'rol_display', 
            'is_staff', 
            'is_superuser'
        ]
        read_only_fields = ['rol_display']
    
    def to_representation(self, instance):
        """Asegurar que el rol siempre se incluya en la respuesta"""
        data = super().to_representation(instance)
        
        # Si el usuario es superusuario y no tiene rol, asignar ADMINISTRADOR
        if instance.is_superuser and not data.get('rol'):
            data['rol'] = 'ADMINISTRADOR'
            data['rol_display'] = 'Administrador'
        
        # Debug: Imprimir los datos serializados
        print(f"Datos serializados para {instance.username}: {data}")
        
        return data