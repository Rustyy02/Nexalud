import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User

def crear_usuarios_prueba():
    print('\n creación de usuarios de prueba...\n')
    
    # Crear superusuario
    if not User.objects.filter(username='admin').exists():
        superuser = User.objects.create_superuser(
            username='nexalud_admin',
            email='admin@nexalud.com',
            password='nexaludgatowatong2025',
            first_name='Super',
            last_name='Admin'
        )
        # El rol se asigna automáticamente en el save()
        print(' Superusuario creado con rol ADMINISTRADOR')
    else:
        print(' Superusuario ya existe')
    
    # Crear Administrador
    if not User.objects.filter(email='carlos.admin@nexalud.admin.com').exists():
        User.objects.create_user(
            username='carlos_admin',
            email='carlos.admin@nexalud.admin.com',
            password='admin123',
            first_name='Carlos',
            last_name='González'
        )
        print(' Administrador creado: Carlos González')
    else:
        print(' Administrador Carlos ya existe')
    
    # Crear Secretarias
    secretarias = [
        {
            'username': 'maria_secretaria',
            'email': 'maria.secretaria@nexalud.secretario.com',
            'password': 'secretaria123',
            'first_name': 'María',
            'last_name': 'Rodríguez'
        },
        {
            'username': 'ana_secretaria',
            'email': 'ana.secretaria@nexalud.secretario.com',
            'password': 'secretaria123',
            'first_name': 'Ana',
            'last_name': 'Martínez'
        }
    ]
    
    for secretaria in secretarias:
        if not User.objects.filter(email=secretaria['email']).exists():
            User.objects.create_user(**secretaria)
            print(f" Secretaria creada: {secretaria['first_name']} {secretaria['last_name']}")
        else:
            print(f" Secretaria {secretaria['first_name']} ya existe")
    
    # Crear Médicos con diferentes especialidades
    medicos = [
        {
            'username': 'juan_medico',
            'email': 'juan.medico@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'especialidad': 'MEDICINA_GENERAL'
        },
        {
            'username': 'laura_pediatra',
            'email': 'laura.pediatra@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Laura',
            'last_name': 'Silva',
            'especialidad': 'PEDIATRIA'
        },
        {
            'username': 'pedro_cardiologo',
            'email': 'pedro.cardiologo@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Pedro',
            'last_name': 'Muñoz',
            'especialidad': 'CARDIOLOGIA'
        },
        {
            'username': 'sofia_ginecologa',
            'email': 'sofia.ginecologa@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Sofía',
            'last_name': 'López',
            'especialidad': 'GINECOLOGIA'
        },
        {
            'username': 'carlos_traumatologo',
            'email': 'carlos.traumatologo@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Carlos',
            'last_name': 'Díaz',
            'especialidad': 'TRAUMATOLOGIA'
        },
        {
            'username': 'isabel_neurologa',
            'email': 'isabel.neurologa@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Isabel',
            'last_name': 'Torres',
            'especialidad': 'NEUROLOGIA'
        },
        {
            'username': 'miguel_urgencias',
            'email': 'miguel.urgencias@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Miguel',
            'last_name': 'Vargas',
            'especialidad': 'URGENCIAS'
        },
        {
            'username': 'patricia_dermatologa',
            'email': 'patricia.dermatologa@nexalud.medico.com',
            'password': 'medico123',
            'first_name': 'Patricia',
            'last_name': 'Herrera',
            'especialidad': 'DERMATOLOGIA'
        }
    ]
    
    for medico_data in medicos:
        if not User.objects.filter(email=medico_data['email']).exists():
            medico = User.objects.create_user(
                username=medico_data['username'],
                email=medico_data['email'],
                password=medico_data['password'],
                first_name=medico_data['first_name'],
                last_name=medico_data['last_name']
            )
            # Asignar especialidad después de crear el usuario
            medico.especialidad = medico_data['especialidad']
            medico.rol = 'MEDICO'
            medico.save()
            
            # Obtener el nombre de la especialidad
            especialidad_display = dict(User.ESPECIALIDAD_CHOICES).get(medico_data['especialidad'])
            print(f" Médico creado: Dr. {medico_data['first_name']} {medico_data['last_name']} - {especialidad_display}")
        else:
            print(f" Médico {medico_data['first_name']} ya existe")
    
    print('\n' + '='*60)
    print(' USUARIOS DE PRUEBA CREADOS')
    print('='*60)
    print('\n CREDENCIALES DE ACCESO:\n')
    
    print('SUPERUSUARIO:')
    print('   admin / admin123 (acceso completo al sistema)')
    
    print('\nADMINISTRADORES:')
    print('   carlos.admin@nexalud.admin.com / admin123')
    
    print('\nSECRETARIAS:')
    print('   maria.secretaria@nexalud.secretario.com / secretaria123')
    print('   ana.secretaria@nexalud.secretario.com / secretaria123')
    
    print('\nMÉDICOS:')
    for medico_data in medicos:
        especialidad = dict(User.ESPECIALIDAD_CHOICES).get(medico_data['especialidad'])
        print(f"  {medico_data['email']} / medico123 ({especialidad})")
    
    print('\n' + '='*60)
    
    # resumen
    print('\n RESUMEN:')
    total_usuarios = User.objects.count()
    total_medicos = User.objects.filter(rol='MEDICO').count()
    total_secretarias = User.objects.filter(rol='SECRETARIA').count()
    total_admins = User.objects.filter(rol='ADMINISTRADOR').count()
    
    print(f'  Total usuarios: {total_usuarios}')
    print(f'  ├─ Administradores: {total_admins}')
    print(f'  ├─ Secretarias: {total_secretarias}')
    print(f'  └─ Médicos: {total_medicos}')
    
    # especialidades disponibles
    if total_medicos > 0:
        print('\n ESPECIALIDADES MÉDICAS DISPONIBLES:')
        medicos_con_especialidad = User.objects.filter(rol='MEDICO').exclude(especialidad__isnull=True)
        especialidades = medicos_con_especialidad.values_list('especialidad', flat=True).distinct()
        for esp in especialidades:
            esp_display = dict(User.ESPECIALIDAD_CHOICES).get(esp)
            count = medicos_con_especialidad.filter(especialidad=esp).count()
            print(f'  ├─ {esp_display}: {count} médico(s)')
    
    print('\n Proceso completado exitosamente!\n')

if __name__ == '__main__':
    crear_usuarios_prueba()