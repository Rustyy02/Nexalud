# backend/create_test_users.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

def crear_usuarios_prueba():
    # Crear superusuario
    if not User.objects.filter(username='admin').exists():
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@nexalud.com',
            password='admin123',
            first_name='Super',
            last_name='Admin'
        )
        # El rol se asigna automáticamente en el save()
        print('✓ Superusuario creado con rol ADMINISTRADOR')
    
    # Crear Administrador
    if not User.objects.filter(email='carlos.admin@nexalud.admin.com').exists():
        User.objects.create_user(
            username='carlos_admin',
            email='carlos.admin@nexalud.admin.com',
            password='admin123',
            first_name='Carlos',
            last_name='Administrador'
        )
        print('✓ Administrador creado')
    
    # Crear Secretaria
    if not User.objects.filter(email='maria.secretaria@nexalud.secretario.com').exists():
        User.objects.create_user(
            username='maria_secretaria',
            email='maria.secretaria@nexalud.secretario.com',
            password='secretaria123',
            first_name='María',
            last_name='Secretaria'
        )
        print('✓ Secretaria creada')
    
    # Crear Médico
    if not User.objects.filter(email='juan.medico@nexalud.medico.com').exists():
        User.objects.create_user(
            username='juan_medico',
            email='juan.medico@nexalud.medico.com',
            password='medico123',
            first_name='Juan',
            last_name='Médico'
        )
        print('✓ Médico creado')
    
    print('\n--- Usuarios de prueba creados ---')
    print('Superusuario: admin / admin123 (acceso a TODO)')
    print('Administrador: carlos.admin@nexalud.admin.com / admin123')
    print('Secretaria: maria.secretaria@nexalud.secretario.com / secretaria123')
    print('Médico: juan.medico@nexalud.medico.com / medico123')

if __name__ == '__main__':
    crear_usuarios_prueba()