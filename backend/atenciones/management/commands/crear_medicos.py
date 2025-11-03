# backend/atenciones/management/commands/crear_medicos.py
"""
Comando de gestión para crear usuarios médicos de ejemplo.

Uso:
    python manage.py crear_medicos
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea usuarios médicos de ejemplo para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=5,
            help='Cantidad de médicos a crear (default: 5)'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        
        medicos_data = [
            {
                'username': 'dr_gonzalez',
                'email': 'gonzalez@nexalud.medico.com',
                'first_name': 'Juan',
                'last_name': 'González',
                'password': 'medico123',
            },
            {
                'username': 'dra_martinez',
                'email': 'martinez@nexalud.medico.com',
                'first_name': 'María',
                'last_name': 'Martínez',
                'password': 'medico123',
            },
            {
                'username': 'dr_rodriguez',
                'email': 'rodriguez@nexalud.medico.com',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'password': 'medico123',
            },
            {
                'username': 'dra_lopez',
                'email': 'lopez@nexalud.medico.com',
                'first_name': 'Ana',
                'last_name': 'López',
                'password': 'medico123',
            },
            {
                'username': 'dr_silva',
                'email': 'silva@nexalud.medico.com',
                'first_name': 'Pedro',
                'last_name': 'Silva',
                'password': 'medico123',
            },
            {
                'username': 'dra_perez',
                'email': 'perez@nexalud.medico.com',
                'first_name': 'Laura',
                'last_name': 'Pérez',
                'password': 'medico123',
            },
            {
                'username': 'dr_morales',
                'email': 'morales@nexalud.medico.com',
                'first_name': 'Diego',
                'last_name': 'Morales',
                'password': 'medico123',
            },
            {
                'username': 'dra_castro',
                'email': 'castro@nexalud.medico.com',
                'first_name': 'Carmen',
                'last_name': 'Castro',
                'password': 'medico123',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for i, medico_info in enumerate(medicos_data[:cantidad]):
                try:
                    # Verificar si el usuario ya existe
                    user, created = User.objects.get_or_create(
                        username=medico_info['username'],
                        defaults={
                            'email': medico_info['email'],
                            'first_name': medico_info['first_name'],
                            'last_name': medico_info['last_name'],
                            'rol': 'MEDICO',
                            'is_active': True,
                            'is_staff': False,
                        }
                    )
                    
                    if created:
                        # Establecer la contraseña
                        user.set_password(medico_info['password'])
                        user.save()
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Creado: Dr. {user.first_name} {user.last_name} '
                                f'({user.username})'
                            )
                        )
                    else:
                        # Actualizar información si ya existe
                        user.first_name = medico_info['first_name']
                        user.last_name = medico_info['last_name']
                        user.email = medico_info['email']
                        user.rol = 'MEDICO'
                        user.is_active = True
                        user.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️  Actualizado: Dr. {user.first_name} {user.last_name} '
                                f'({user.username})'
                            )
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Error al procesar {medico_info["username"]}: {str(e)}'
                        )
                    )
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 RESUMEN:\n'
                f'   • Médicos creados: {created_count}\n'
                f'   • Médicos actualizados: {updated_count}\n'
                f'   • Total procesados: {created_count + updated_count}\n'
            )
        )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🔑 Contraseña por defecto para todos: medico123\n'
                    f'   (Se recomienda cambiarla en el primer acceso)\n'
                )
            )
        
        # Listar todos los médicos activos
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('\n👨‍⚕️ MÉDICOS DISPONIBLES EN EL SISTEMA:\n'))
        
        medicos = User.objects.filter(rol='MEDICO', is_active=True).order_by('last_name')
        for medico in medicos:
            self.stdout.write(
                f'   • Dr. {medico.first_name} {medico.last_name} '
                f'- Usuario: {medico.username} - Email: {medico.email}'
            )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                '\n✨ Los médicos pueden acceder con su usuario o email '
                'en http://localhost:3000/login\n'
            )
        )