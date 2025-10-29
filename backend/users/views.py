# backend/users/views.py
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from .serializers import UserSerializer

class CustomAuthToken(ObtainAuthToken):
    """
    Vista personalizada para autenticación que acepta tanto username como email
    """
    def post(self, request, *args, **kwargs):
        # Obtener las credenciales del request
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response({
                'error': 'Por favor proporcione usuario/correo y contraseña'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Intentar autenticar con username primero
        user = authenticate(username=username_or_email, password=password)
        
        # Si falla, intentar con email
        if not user:
            from users.models import User
            try:
                # Buscar usuario por email
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user:
            # Generar o recuperar token
            token, created = Token.objects.get_or_create(user=user)
            
            # Serializar información del usuario
            user_data = UserSerializer(user).data
            
            # ✅ IMPORTANTE: Imprimir en consola para debug
            print(f"\n=== LOGIN DEBUG ===")
            print(f"Usuario: {user.username}")
            print(f"Email: {user.email}")
            print(f"Rol: {user.rol}")
            print(f"Rol Display: {user.get_rol_display()}")
            print(f"Is Superuser: {user.is_superuser}")
            print(f"Data enviada: {user_data}")
            print(f"==================\n")
            
            return Response({
                'token': token.key,
                'user': user_data,
                'message': 'Autenticación exitosa'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)