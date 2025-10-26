# backend/tipos_atencion/management/commands/poblar_tipos_atencion.py
"""
Comando para poblar la base de datos con los tipos de atención predefinidos.

Uso:
    python manage.py poblar_tipos_atencion
    python manage.py poblar_tipos_atencion --borrar  # Borra y recrea todo
"""

from django.core.management.base import BaseCommand
from tipos_atencion.models import TipoAtencion, PlantillaFlujo
from decimal import Decimal


class Command(BaseCommand):
    help = 'Puebla la base de datos con los 4 tipos de atención estándar del sistema de salud'

    def add_arguments(self, parser):
        parser.add_argument(
            '--borrar',
            action='store_true',
            help='Borra todos los tipos de atención existentes antes de crear',
        )

    def handle(self, *args, **options):
        if options['borrar']:
            self.stdout.write(self.style.WARNING('⚠️  Borrando tipos de atención existentes...'))
            TipoAtencion.objects.all().delete()
            PlantillaFlujo.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✅ Tipos de atención eliminados\n'))

        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('CREANDO TIPOS DE ATENCIÓN DEL SISTEMA'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

        # ============================================
        # ATENCIÓN PRIMARIA
        # ============================================
        
        self.stdout.write(self.style.SUCCESS('📋 1. ATENCIÓN PRIMARIA'))
        self.stdout.write('-'*80)
        
        atencion_primaria, created = TipoAtencion.objects.get_or_create(
            codigo='PRIM-001',
            defaults={
                'nombre': 'Atención Primaria General',
                'nivel': 'PRIMARIA',
                'descripcion': (
                    'Puerta de entrada al sistema de salud. Enfocada en prevención, '
                    'promoción y tratamiento de problemas comunes de salud. '
                    'Incluye consultas de medicina general, atención materno-infantil, '
                    'vacunación y control de enfermedades crónicas.'
                ),
                'etapas_flujo': [
                    'ADMISION',
                    'REGISTRO',
                    'TRIAJE',
                    'CONSULTA_GENERAL',
                    'EDUCACION_SALUD',
                    'ALTA_MEDICA',
                ],
                'duraciones_estimadas': {
                    'ADMISION': 10,
                    'REGISTRO': 5,
                    'TRIAJE': 10,
                    'CONSULTA_GENERAL': 20,
                    'EDUCACION_SALUD': 15,
                    'ALTA_MEDICA': 5,
                },
                'requiere_especialista': False,
                'requiere_hospitalizacion': False,
                'nivel_complejidad': 1,
                'costo_estimado_base': Decimal('15000.00'),
                'prioridad_default': 'BAJA',
                'activo': True,
                'metadatos': {
                    'ejemplos': [
                        'Consulta medicina general',
                        'Control preventivo',
                        'Vacunación',
                        'Control de enfermedades crónicas',
                        'Atención materno-infantil'
                    ],
                    'recursos_necesarios': [
                        'Médico general',
                        'Enfermera',
                        'Box de atención'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Creado: {atencion_primaria.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Ya existe: {atencion_primaria.nombre}'))
        
        self.stdout.write(f'   Código: {atencion_primaria.codigo}')
        self.stdout.write(f'   Etapas: {len(atencion_primaria.etapas_flujo)}')
        self.stdout.write(f'   Duración Estimada: {atencion_primaria.calcular_duracion_total_estimada()["formateado"]}')
        self.stdout.write('')

        # ============================================
        # ATENCIÓN SECUNDARIA
        # ============================================
        
        self.stdout.write(self.style.SUCCESS('📋 2. ATENCIÓN SECUNDARIA'))
        self.stdout.write('-'*80)
        
        atencion_secundaria, created = TipoAtencion.objects.get_or_create(
            codigo='SEC-001',
            defaults={
                'nombre': 'Atención Secundaria Especializada',
                'nivel': 'SECUNDARIA',
                'descripcion': (
                    'Atención hospitalaria y especializada. Incluye servicios más '
                    'especializados que la atención primaria, como cirugías menores, '
                    'hospitalizaciones básicas y tratamientos para enfermedades no complejas. '
                    'Requiere infraestructura hospitalaria y personal especializado.'
                ),
                'etapas_flujo': [
                    'ADMISION',
                    'REGISTRO',
                    'TRIAJE',
                    'CONSULTA_ESPECIALISTA',
                    'EXAMENES_DIAGNOSTICOS',
                    'PROCEDIMIENTOS_MENORES',
                    'RECUPERACION_CORTA',
                    'SEGUIMIENTO',
                    'ALTA_MEDICA',
                ],
                'duraciones_estimadas': {
                    'ADMISION': 15,
                    'REGISTRO': 10,
                    'TRIAJE': 15,
                    'CONSULTA_ESPECIALISTA': 30,
                    'EXAMENES_DIAGNOSTICOS': 60,
                    'PROCEDIMIENTOS_MENORES': 90,
                    'RECUPERACION_CORTA': 120,
                    'SEGUIMIENTO': 20,
                    'ALTA_MEDICA': 15,
                },
                'requiere_especialista': True,
                'requiere_hospitalizacion': True,
                'nivel_complejidad': 2,
                'costo_estimado_base': Decimal('150000.00'),
                'prioridad_default': 'MEDIA',
                'activo': True,
                'metadatos': {
                    'ejemplos': [
                        'Consulta con especialista',
                        'Cirugía menor',
                        'Hospitalización básica',
                        'Exámenes diagnósticos especializados'
                    ],
                    'recursos_necesarios': [
                        'Médico especialista',
                        'Pabellón quirúrgico',
                        'Sala de hospitalización',
                        'Equipamiento diagnóstico'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Creado: {atencion_secundaria.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Ya existe: {atencion_secundaria.nombre}'))
        
        self.stdout.write(f'   Código: {atencion_secundaria.codigo}')
        self.stdout.write(f'   Etapas: {len(atencion_secundaria.etapas_flujo)}')
        self.stdout.write(f'   Duración Estimada: {atencion_secundaria.calcular_duracion_total_estimada()["formateado"]}')
        self.stdout.write('')

        # ============================================
        # ATENCIÓN TERCIARIA
        # ============================================
        
        self.stdout.write(self.style.SUCCESS('📋 3. ATENCIÓN TERCIARIA'))
        self.stdout.write('-'*80)
        
        atencion_terciaria, created = TipoAtencion.objects.get_or_create(
            codigo='TER-001',
            defaults={
                'nombre': 'Atención Terciaria Alta Complejidad',
                'nivel': 'TERCIARIA',
                'descripcion': (
                    'Atención especializada de alta complejidad. Requiere infraestructura '
                    'avanzada y personal altamente calificado. Incluye cirugías mayores, '
                    'tratamiento de patologías complejas, UCI y procedimientos especializados. '
                    'Disponible solo en hospitales de alta especialidad.'
                ),
                'etapas_flujo': [
                    'ADMISION',
                    'REGISTRO',
                    'TRIAJE',
                    'EVALUACION_ESPECIALIZADA',
                    'ESTUDIOS_AVANZADOS',
                    'JUNTA_MEDICA',
                    'HOSPITALIZACION_COMPLEJA',
                    'CIRUGIA_MAYOR',
                    'UCI',
                    'RECUPERACION_PROLONGADA',
                    'REHABILITACION',
                    'SEGUIMIENTO',
                    'ALTA_MEDICA',
                ],
                'duraciones_estimadas': {
                    'ADMISION': 20,
                    'REGISTRO': 15,
                    'TRIAJE': 20,
                    'EVALUACION_ESPECIALIZADA': 45,
                    'ESTUDIOS_AVANZADOS': 120,
                    'JUNTA_MEDICA': 60,
                    'HOSPITALIZACION_COMPLEJA': 2880,  # 2 días
                    'CIRUGIA_MAYOR': 240,
                    'UCI': 4320,  # 3 días
                    'RECUPERACION_PROLONGADA': 2880,  # 2 días
                    'REHABILITACION': 180,
                    'SEGUIMIENTO': 30,
                    'ALTA_MEDICA': 20,
                },
                'requiere_especialista': True,
                'requiere_hospitalizacion': True,
                'nivel_complejidad': 4,
                'costo_estimado_base': Decimal('2500000.00'),
                'prioridad_default': 'ALTA',
                'activo': True,
                'metadatos': {
                    'ejemplos': [
                        'Cirugías mayores',
                        'Patologías complejas',
                        'Cuidados intensivos',
                        'Procedimientos especializados'
                    ],
                    'recursos_necesarios': [
                        'Equipo multidisciplinario de especialistas',
                        'Pabellón de cirugía mayor',
                        'UCI equipada',
                        'Equipamiento de alta tecnología',
                        'Laboratorio avanzado'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Creado: {atencion_terciaria.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Ya existe: {atencion_terciaria.nombre}'))
        
        self.stdout.write(f'   Código: {atencion_terciaria.codigo}')
        self.stdout.write(f'   Etapas: {len(atencion_terciaria.etapas_flujo)}')
        self.stdout.write(f'   Duración Estimada: {atencion_terciaria.calcular_duracion_total_estimada()["formateado"]}')
        self.stdout.write('')

        # ============================================
        # ATENCIÓN CUATERNARIA
        # ============================================
        
        self.stdout.write(self.style.SUCCESS('📋 4. ATENCIÓN CUATERNARIA'))
        self.stdout.write('-'*80)
        
        atencion_cuaternaria, created = TipoAtencion.objects.get_or_create(
            codigo='CUAT-001',
            defaults={
                'nombre': 'Atención Cuaternaria Máxima Complejidad',
                'nivel': 'CUATERNARIA',
                'descripcion': (
                    'Atención médica de máxima complejidad. Incluye procedimientos '
                    'muy especializados que se realizan en centros muy específicos. '
                    'Ejemplos: trasplantes de órganos, terapias de vanguardia, '
                    'procedimientos experimentales. Requiere infraestructura única '
                    'y personal ultra-especializado.'
                ),
                'etapas_flujo': [
                    'ADMISION',
                    'REGISTRO',
                    'EVALUACION_MULTIDISCIPLINARIA',
                    'PROTOCOLO_INVESTIGACION',
                    'ESTUDIOS_AVANZADOS',
                    'JUNTA_MEDICA',
                    'PREPARACION_ESPECIALIZADA',
                    'PROCEDIMIENTO_ALTA_COMPLEJIDAD',
                    'TRASPLANTE',
                    'UCI_ESPECIALIZADA',
                    'TERAPIA_AVANZADA',
                    'RECUPERACION_PROLONGADA',
                    'REHABILITACION',
                    'SEGUIMIENTO_LARGO_PLAZO',
                    'ALTA_MEDICA',
                ],
                'duraciones_estimadas': {
                    'ADMISION': 30,
                    'REGISTRO': 20,
                    'EVALUACION_MULTIDISCIPLINARIA': 120,
                    'PROTOCOLO_INVESTIGACION': 180,
                    'ESTUDIOS_AVANZADOS': 240,
                    'JUNTA_MEDICA': 90,
                    'PREPARACION_ESPECIALIZADA': 1440,  # 1 día
                    'PROCEDIMIENTO_ALTA_COMPLEJIDAD': 480,
                    'TRASPLANTE': 720,
                    'UCI_ESPECIALIZADA': 7200,  # 5 días
                    'TERAPIA_AVANZADA': 2880,  # 2 días
                    'RECUPERACION_PROLONGADA': 5760,  # 4 días
                    'REHABILITACION': 360,
                    'SEGUIMIENTO_LARGO_PLAZO': 60,
                    'ALTA_MEDICA': 30,
                },
                'requiere_especialista': True,
                'requiere_hospitalizacion': True,
                'nivel_complejidad': 5,
                'costo_estimado_base': Decimal('15000000.00'),
                'prioridad_default': 'CRITICA',
                'activo': True,
                'metadatos': {
                    'ejemplos': [
                        'Trasplantes de órganos',
                        'Terapias de vanguardia',
                        'Procedimientos experimentales',
                        'Cirugías de máxima complejidad'
                    ],
                    'recursos_necesarios': [
                        'Equipo multidisciplinario ultra-especializado',
                        'Centro de trasplantes',
                        'UCI especializada',
                        'Equipamiento de última generación',
                        'Laboratorio de investigación',
                        'Infraestructura única'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Creado: {atencion_cuaternaria.nombre}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  Ya existe: {atencion_cuaternaria.nombre}'))
        
        self.stdout.write(f'   Código: {atencion_cuaternaria.codigo}')
        self.stdout.write(f'   Etapas: {len(atencion_cuaternaria.etapas_flujo)}')
        self.stdout.write(f'   Duración Estimada: {atencion_cuaternaria.calcular_duracion_total_estimada()["formateado"]}')
        self.stdout.write('')

        # ============================================
        # RESUMEN FINAL
        # ============================================
        
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('RESUMEN FINAL'))
        self.stdout.write(self.style.SUCCESS('='*80))
        
        total_tipos = TipoAtencion.objects.filter(activo=True).count()
        self.stdout.write(f'\n✅ Total de tipos de atención activos: {total_tipos}')
        
        self.stdout.write('\n📊 Distribución por nivel de complejidad:')
        for tipo in TipoAtencion.objects.filter(activo=True).order_by('nivel_complejidad'):
            duracion = tipo.calcular_duracion_total_estimada()
            self.stdout.write(
                f"   {'⭐' * tipo.nivel_complejidad} {tipo.nombre} - "
                f"{len(tipo.etapas_flujo)} etapas - "
                f"{duracion['formateado']}"
            )
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('🎉 TIPOS DE ATENCIÓN CREADOS EXITOSAMENTE'))
        self.stdout.write('='*80 + '\n')
        
        self.stdout.write(self.style.SUCCESS('💡 Próximos pasos:'))
        self.stdout.write('   1. Los pacientes nuevos se asignarán automáticamente a un tipo de atención')
        self.stdout.write('   2. Las rutas clínicas usarán las etapas específicas de cada tipo')
        self.stdout.write('   3. Puedes personalizar los tipos de atención desde el admin de Django\n')
