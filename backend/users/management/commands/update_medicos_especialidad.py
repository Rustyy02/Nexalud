# backend/users/management/commands/update_medicos_especialidad.py
from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Actualiza los médicos existentes para asignarles una especialidad por defecto'

    def handle(self, *args, **kwargs):
        # Buscar médicos sin especialidad
        medicos_sin_especialidad = User.objects.filter(
            rol='MEDICO',
            especialidad__isnull=True
        )
        
        count = medicos_sin_especialidad.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay médicos sin especialidad.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Se encontraron {count} médicos sin especialidad.')
        )
        
        # Asignar Medicina General por defecto
        for medico in medicos_sin_especialidad:
            medico.especialidad = 'MEDICINA_GENERAL'
            medico.save(update_fields=['especialidad'])
            self.stdout.write(
                f'Actualizado: {medico.username} - Asignada especialidad: Medicina General'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Se actualizaron {count} médicos exitosamente.')
        )