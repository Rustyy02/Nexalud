# backend/pacientes/management/commands/insertar_pacientes_prueba.py
"""
Comando de Django para insertar pacientes de prueba
Uso: python manage.py insertar_pacientes_prueba
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from decimal import Decimal
from pacientes.models import Paciente


class Command(BaseCommand):
    help = 'Inserta 10 pacientes de prueba en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrar',
            action='store_true',
            help='Borra todos los pacientes antes de insertar',
        )

    def handle(self, *args, **options):
        if options['borrar']:
            self.stdout.write(self.style.WARNING('⚠️  Borrando todos los pacientes existentes...'))
            count = Paciente.objects.all().delete()[0]
            self.stdout.write(self.style.SUCCESS(f'✅ {count} pacientes eliminados'))
            self.stdout.write('')

        # Datos de prueba
        pacientes_data = [
            {
                'rut': '21.376.955-3',
                'nombre': 'María José',
                'apellido_paterno': 'González',
                'apellido_materno': 'Silva',
                'fecha_nacimiento': date(1995, 3, 15),
                'genero': 'F',
                'correo': 'maria.gonzalez@email.cl',
                'telefono': '+56912345678',
                'telefono_emergencia': '+56987654321',
                'nombre_contacto_emergencia': 'Pedro González (padre)',
                'direccion_calle': 'Av. Libertad 1234',
                'direccion_comuna': 'Quilpué',
                'direccion_ciudad': 'Quilpué',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2430000',
                'seguro_medico': 'FONASA_B',
                'numero_beneficiario': 'F-2137695531',
                'tipo_sangre': 'O+',
                'peso': Decimal('65.5'),
                'altura': 165,
                'alergias': 'Penicilina, Polen',
                'condiciones_preexistentes': 'Asma leve',
                'medicamentos_actuales': 'Salbutamol (inhalador de rescate)',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'MEDIA',
            },
            {
                'rut': '18.234.567-8',
                'nombre': 'Carlos Alberto',
                'apellido_paterno': 'Muñoz',
                'apellido_materno': 'Pérez',
                'fecha_nacimiento': date(1988, 7, 22),
                'genero': 'M',
                'correo': 'carlos.munoz@gmail.com',
                'telefono': '+56923456789',
                'telefono_emergencia': '+56998765432',
                'nombre_contacto_emergencia': 'Ana Pérez (esposa)',
                'direccion_calle': 'Calle Los Aromos 567',
                'direccion_comuna': 'Viña del Mar',
                'direccion_ciudad': 'Viña del Mar',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2520000',
                'seguro_medico': 'ISAPRE_CONSALUD',
                'numero_beneficiario': 'CS-18234567',
                'tipo_sangre': 'A+',
                'peso': Decimal('78.0'),
                'altura': 175,
                'alergias': 'Sin alergias conocidas',
                'condiciones_preexistentes': 'Hipertensión arterial',
                'medicamentos_actuales': 'Enalapril 10mg (1 vez al día)',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'BAJA',
            },
            {
                'rut': '15.987.654-3',
                'nombre': 'Javiera',
                'apellido_paterno': 'Rojas',
                'apellido_materno': 'Cortés',
                'fecha_nacimiento': date(1992, 11, 8),
                'genero': 'F',
                'correo': 'javiera.rojas@hotmail.com',
                'telefono': '+56934567890',
                'telefono_emergencia': '+56976543210',
                'nombre_contacto_emergencia': 'Luis Rojas (hermano)',
                'direccion_calle': 'Pasaje Las Rosas 890',
                'direccion_comuna': 'Valparaíso',
                'direccion_ciudad': 'Valparaíso',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2340000',
                'seguro_medico': 'FONASA_C',
                'numero_beneficiario': 'F-1598765432',
                'tipo_sangre': 'B+',
                'peso': Decimal('58.3'),
                'altura': 160,
                'alergias': 'Mariscos, Ibuprofeno',
                'condiciones_preexistentes': 'Sin condiciones previas',
                'medicamentos_actuales': 'Sin medicamentos actuales',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'ALTA',
            },
            {
                'rut': '12.345.678-5',
                'nombre': 'Roberto',
                'apellido_paterno': 'Fernández',
                'apellido_materno': 'Martínez',
                'fecha_nacimiento': date(1978, 5, 30),
                'genero': 'M',
                'correo': 'r.fernandez@outlook.com',
                'telefono': '+56945678901',
                'telefono_emergencia': '+56965432109',
                'nombre_contacto_emergencia': 'Carmen Martínez (madre)',
                'direccion_calle': 'Av. Argentina 2345',
                'direccion_comuna': 'Santiago',
                'direccion_ciudad': 'Santiago',
                'direccion_region': 'RM',
                'direccion_codigo_postal': '8320000',
                'seguro_medico': 'FONASA_D',
                'numero_beneficiario': 'F-1234567851',
                'tipo_sangre': 'AB+',
                'peso': Decimal('85.2'),
                'altura': 180,
                'alergias': 'Sin alergias conocidas',
                'condiciones_preexistentes': 'Diabetes tipo 2, Colesterol alto',
                'medicamentos_actuales': 'Metformina 850mg (2 veces al día), Atorvastatina 20mg',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'MEDIA',
            },
            {
                'rut': '19.876.543-2',
                'nombre': 'Valentina',
                'apellido_paterno': 'Soto',
                'apellido_materno': 'Vargas',
                'fecha_nacimiento': date(2000, 1, 12),
                'genero': 'F',
                'correo': 'vale.soto@yahoo.com',
                'telefono': '+56956789012',
                'telefono_emergencia': '+56954321098',
                'nombre_contacto_emergencia': 'Ricardo Soto (padre)',
                'direccion_calle': 'Calle Primavera 456',
                'direccion_comuna': 'Concón',
                'direccion_ciudad': 'Concón',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2510000',
                'seguro_medico': 'ISAPRE_BANMEDICA',
                'numero_beneficiario': 'BM-19876543',
                'tipo_sangre': 'O-',
                'peso': Decimal('52.0'),
                'altura': 158,
                'alergias': 'Látex, Frutos secos',
                'condiciones_preexistentes': 'Anemia leve',
                'medicamentos_actuales': 'Sulfato ferroso 300mg',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'BAJA',
            },
            {
                'rut': '16.543.210-9',
                'nombre': 'Diego',
                'apellido_paterno': 'Castillo',
                'apellido_materno': 'Ramírez',
                'fecha_nacimiento': date(1985, 9, 18),
                'genero': 'M',
                'correo': 'diego.castillo@empresa.cl',
                'telefono': '+56967890123',
                'telefono_emergencia': '+56943210987',
                'nombre_contacto_emergencia': 'Patricia Ramírez (esposa)',
                'direccion_calle': 'Los Castaños 789',
                'direccion_comuna': 'Villa Alemana',
                'direccion_ciudad': 'Villa Alemana',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2800000',
                'seguro_medico': 'PARTICULAR',
                'numero_beneficiario': 'Sin proporcionar',
                'tipo_sangre': 'A-',
                'peso': Decimal('72.5'),
                'altura': 170,
                'alergias': 'Sin alergias conocidas',
                'condiciones_preexistentes': 'Sin condiciones previas',
                'medicamentos_actuales': 'Sin medicamentos actuales',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'CRITICA',
            },
            {
                'rut': '20.123.456-7',
                'nombre': 'Camila',
                'apellido_paterno': 'Torres',
                'apellido_materno': 'Lagos',
                'fecha_nacimiento': date(1998, 4, 25),
                'genero': 'F',
                'correo': 'camila.torres@estudiante.cl',
                'telefono': '+56978901234',
                'telefono_emergencia': '+56932109876',
                'nombre_contacto_emergencia': 'Sofía Lagos (madre)',
                'direccion_calle': 'Paseo Independencia 123',
                'direccion_comuna': 'Limache',
                'direccion_ciudad': 'Limache',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2240000',
                'seguro_medico': 'FONASA_A',
                'numero_beneficiario': 'F-2012345671',
                'tipo_sangre': 'B-',
                'peso': Decimal('60.0'),
                'altura': 163,
                'alergias': 'Sin alergias conocidas',
                'condiciones_preexistentes': 'Migraña crónica',
                'medicamentos_actuales': 'Paracetamol según necesidad',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'MEDIA',
            },
            {
                'rut': '17.654.321-K',
                'nombre': 'Andrés',
                'apellido_paterno': 'Morales',
                'apellido_materno': 'Fuentes',
                'fecha_nacimiento': date(1990, 12, 3),
                'genero': 'M',
                'correo': 'andres.morales@trabajo.cl',
                'telefono': '+56989012345',
                'telefono_emergencia': '+56921098765',
                'nombre_contacto_emergencia': 'María Fuentes (madre)',
                'direccion_calle': 'Av. España 3456',
                'direccion_comuna': 'Valparaíso',
                'direccion_ciudad': 'Valparaíso',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2340000',
                'seguro_medico': 'ISAPRE_CRUZBANCA',
                'numero_beneficiario': 'CB-17654321',
                'tipo_sangre': 'O+',
                'peso': Decimal('90.0'),
                'altura': 182,
                'alergias': 'Aspirina',
                'condiciones_preexistentes': 'Obesidad grado 1',
                'medicamentos_actuales': 'Sin medicamentos actuales',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'BAJA',
            },
            {
                'rut': '14.789.012-3',
                'nombre': 'Francisca',
                'apellido_paterno': 'Pino',
                'apellido_materno': 'Bravo',
                'fecha_nacimiento': date(1983, 6, 14),
                'genero': 'F',
                'correo': 'francisca.pino@correo.cl',
                'telefono': '+56990123456',
                'telefono_emergencia': '+56910987654',
                'nombre_contacto_emergencia': 'Jorge Pino (esposo)',
                'direccion_calle': 'Los Olivos 234',
                'direccion_comuna': 'Quilpué',
                'direccion_ciudad': 'Quilpué',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2430000',
                'seguro_medico': 'ISAPRE_COLMENA',
                'numero_beneficiario': 'CO-14789012',
                'tipo_sangre': 'AB-',
                'peso': Decimal('68.7'),
                'altura': 168,
                'alergias': 'Sin alergias conocidas',
                'condiciones_preexistentes': 'Hipotiroidismo',
                'medicamentos_actuales': 'Levotiroxina 100mcg (en ayunas)',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'ALTA',
            },
            {
                'rut': '13.456.789-0',
                'nombre': 'Sebastián',
                'apellido_paterno': 'Reyes',
                'apellido_materno': 'Campos',
                'fecha_nacimiento': date(1975, 10, 28),
                'genero': 'M',
                'correo': 'sebastian.reyes@mail.com',
                'telefono': '+56901234567',
                'telefono_emergencia': '+56909876543',
                'nombre_contacto_emergencia': 'Elena Campos (madre)',
                'direccion_calle': 'Calle Central 567',
                'direccion_comuna': 'Viña del Mar',
                'direccion_ciudad': 'Viña del Mar',
                'direccion_region': 'V',
                'direccion_codigo_postal': '2520000',
                'seguro_medico': 'FONASA_C',
                'numero_beneficiario': 'F-1345678901',
                'tipo_sangre': 'A+',
                'peso': Decimal('75.8'),
                'altura': 173,
                'alergias': 'Contraste yodado',
                'condiciones_preexistentes': 'Gastritis crónica',
                'medicamentos_actuales': 'Omeprazol 20mg (antes del desayuno)',
                'estado_actual': 'EN_ESPERA',
                'nivel_urgencia': 'MEDIA',
            },
        ]

        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('INSERTANDO 10 PACIENTES DE PRUEBA'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')

        creados = 0
        existentes = 0
        errores = 0

        for i, datos in enumerate(pacientes_data, 1):
            try:
                # Verificar si existe
                if Paciente.objects.filter(rut=datos['rut']).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"[{i}/10] ⚠️  {datos['nombre']} {datos['apellido_paterno']} "
                            f"(RUT: {datos['rut']}) ya existe. Saltando..."
                        )
                    )
                    existentes += 1
                    continue

                # Crear paciente
                paciente = Paciente.objects.create(**datos)

                self.stdout.write(
                    self.style.SUCCESS(f"[{i}/10] ✅ {paciente.nombre_completo} creado exitosamente")
                )
                self.stdout.write(f"       RUT: {paciente.rut}")
                self.stdout.write(f"       Edad: {paciente.edad} años")
                self.stdout.write(f"       Urgencia: {paciente.get_nivel_urgencia_display()}")
                self.stdout.write('')

                creados += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"[{i}/10] ❌ Error al crear {datos['nombre']} {datos['apellido_paterno']}: {str(e)}"
                    )
                )
                errores += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(f"✅ Creados: {creados}")
        self.stdout.write(f"⚠️  Ya existían: {existentes}")
        self.stdout.write(f"❌ Errores: {errores}")
        self.stdout.write(f"📊 Total procesados: {len(pacientes_data)}")
        self.stdout.write('')
        self.stdout.write(f"📋 Total en base de datos: {Paciente.objects.count()}")
        self.stdout.write(self.style.SUCCESS('=' * 70))
