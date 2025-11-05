# backend/atenciones/management/commands/crear_atenciones_prueba.py
"""
Comando para crear atenciones de prueba
Ejecutar con: python manage.py crear_atenciones_prueba
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from atenciones.models import Atencion
from pacientes.models import Paciente
from boxes.models import Box
from users.models import User
import random

class Command(BaseCommand):
    help = 'Crea atenciones de prueba para médicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=5,
            help='Cantidad de atenciones a crear (default: 5)'
        )
        parser.add_argument(
            '--medico',
            type=str,
            help='Username del médico específico'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        medico_username = options.get('medico')
        
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('CREANDO ATENCIONES DE PRUEBA'))
        self.stdout.write('='*60)
        
        # Verificar médicos
        if medico_username:
            medicos = User.objects.filter(username=medico_username, rol='MEDICO')
            if not medicos.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ No se encontró el médico: {medico_username}')
                )
                return
        else:
            medicos = User.objects.filter(rol='MEDICO')
        
        if not medicos.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay médicos en el sistema.')
            )
            self.stdout.write('Ejecuta: python manage.py crear_medicos')
            return
        
        # Verificar pacientes
        pacientes = Paciente.objects.all()
        if not pacientes.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay pacientes en el sistema.')
            )
            return
        
        # Verificar boxes
        boxes = Box.objects.filter(activo=True)
        if not boxes.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay boxes disponibles.')
            )
            return
        
        self.stdout.write(f'\n✅ Médicos disponibles: {medicos.count()}')
        self.stdout.write(f'✅ Pacientes disponibles: {pacientes.count()}')
        self.stdout.write(f'✅ Boxes disponibles: {boxes.count()}\n')
        
        tipos_atencion = ['CONSULTA_GENERAL', 'CONSULTA_ESPECIALIDAD', 'CONTROL', 'PROCEDIMIENTO']
        duraciones = [15, 20, 30, 45, 60]
        
        created_count = 0
        ahora = timezone.now()
        
        with transaction.atomic():
            for i in range(cantidad):
                try:
                    # Seleccionar médico, paciente y box aleatorios
                    medico = random.choice(medicos)
                    paciente = random.choice(pacientes)
                    box = random.choice(boxes)
                    
                    # Calcular hora (distribuir en las próximas 8 horas)
                    minutos_adelante = random.randint(0, 480)  # 0 a 8 horas
                    fecha_hora_inicio = ahora + timedelta(minutes=minutos_adelante)
                    
                    # Seleccionar tipo y duración
                    tipo_atencion = random.choice(tipos_atencion)
                    duracion = random.choice(duraciones)
                    
                    # Crear la atención
                    atencion = Atencion.objects.create(
                        paciente=paciente,
                        medico=medico,
                        box=box,
                        fecha_hora_inicio=fecha_hora_inicio,
                        duracion_planificada=duracion,
                        tipo_atencion=tipo_atencion,
                        estado='PROGRAMADA',
                    )
                    
                    created_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ [{i+1}/{cantidad}] Atención creada:\n'
                            f'   📅 {fecha_hora_inicio.strftime("%H:%M")}\n'
                            f'   👨‍⚕️ Dr. {medico.get_full_name()}\n'
                            f'   👤 Paciente: {paciente.identificador_hash[:12]}\n'
                            f'   🏥 Box: {box.numero}\n'
                            f'   ⏱️  Duración: {duracion} min\n'
                        )
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error al crear atención {i+1}: {str(e)}')
                    )
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 RESUMEN:\n'
                f'   • Atenciones creadas: {created_count}\n'
                f'   • Médicos involucrados: {medicos.count()}\n'
            )
        )
        
        # Listar atenciones por médico
        self.stdout.write('\n👨‍⚕️ ATENCIONES POR MÉDICO:\n')
        for medico in medicos:
            count = Atencion.objects.filter(medico=medico).count()
            self.stdout.write(f'   • Dr. {medico.get_full_name()}: {count} atenciones')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                '\n✨ Las atenciones están listas. Ahora puedes:\n'
                '   1. Acceder con un usuario médico\n'
                '   2. Ir a /medico/consultas\n'
                '   3. Ver tus atenciones programadas\n'
            )
        )
