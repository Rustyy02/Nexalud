# backend/fix_admin_roles.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

def corregir_roles():
    # Actualizar todos los usuarios con dominio @nexalud.admin.com
    usuarios_admin = User.objects.filter(email__endswith='@nexalud.admin.com')
    
    for user in usuarios_admin:
        user.rol = 'ADMINISTRADOR'
        user.save()
        print(f"✓ Usuario {user.username} actualizado a ADMINISTRADOR")
    
    # Actualizar todos los superusuarios
    superusuarios = User.objects.filter(is_superuser=True)
    
    for user in superusuarios:
        user.rol = 'ADMINISTRADOR'
        user.save()
        print(f"✓ Superusuario {user.username} actualizado a ADMINISTRADOR")
    
    # Verificar los cambios
    print("\n--- Estado actual de usuarios ---")
    for user in User.objects.all():
        print(f"{user.username}: {user.rol} (Email: {user.email})")

if __name__ == '__main__':
    corregir_roles()