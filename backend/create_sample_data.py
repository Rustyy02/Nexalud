# Script para crear datos de ejemplo en Django shell
# Ejecutar con: python manage.py shell < create_sample_data.py

from django.contrib.auth.models import User
from pacientes.models import Paciente
from boxes.models import Box
from atenciones.models import Medico, Atencion
from rutas_clinicas.models import RutaClinica
from django.utils import timezone
from datetime import timedelta
import hashlib

print("Creando datos de ejemplo para Nexalud...")

# 1. Crear usuario admin si no existe
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@nexalud.cl', 'admin123')
    print("✓ Usuario admin creado (username: admin, password: admin123)")
else:
    print("✓ Usuario admin ya existe")

# 2. Crear Boxes
boxes_data = [
    {'numero': 'Box 01', 'nombre': 'Sala de Consulta 1', 'especialidad': 'GENERAL'},
    {'numero': 'Box 02', 'nombre': 'Sala de Consulta 2', 'especialidad': 'GENERAL'},
    {'numero': 'Box 03', 'nombre': 'Sala de Procedimientos', 'especialidad': 'PROCEDIMIENTOS'},
    {'numero': 'Box 04', 'nombre': 'Sala de Urgencias', 'especialidad': 'GENERAL'},
]

for box_data in boxes_data:
    Box.objects.get_or_create(
        numero=box_data['numero'],
        defaults={
            'nombre': box_data['nombre'],
            'especialidad': box_data['especialidad'],
            'estado': 'DISPONIBLE',
            'activo': True
        }
    )
print(f"✓ {len(boxes_data)} Boxes creados")

# 3. Crear Médicos
medicos_data = [
    {'codigo': 'MED001', 'nombre': 'Juan', 'apellido': 'Pérez', 'especialidad': 'MEDICINA_GENERAL'},
    {'codigo': 'MED002', 'nombre': 'María', 'apellido': 'González', 'especialidad': 'TRAUMATOLOGIA'},
    {'codigo': 'MED003', 'nombre': 'Carlos', 'apellido': 'Rodríguez', 'especialidad': 'RADIOLOGIA'},
]

for med_data in medicos_data:
    Medico.objects.get_or_create(
        codigo_medico=med_data['codigo'],
        defaults={
            'nombre': med_data['nombre'],
            'apellido': med_data['apellido'],
            'especialidad_principal': med_data['especialidad'],
            'activo': True
        }
    )
print(f"✓ {len(medicos_data)} Médicos creados")

# 4. Crear Pacientes con Rutas Clínicas
pacientes_data = [
    {
        'rut': '21.345.754-3',
        'edad': 42,
        'genero': 'F',
        'urgencia': 'MEDIA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'REVISION_EXAMEN'],
        'etapa_actual_index': 1,  # En Proceso Examen
        'notas': 'Paciente que sufrió caída desde 1 metro, niega pérdida del conocimiento. Posterior al evento refiere dolor de hombro, cadera y zona lumbar, con dificultad para caminar.'
    },
    {
        'rut': '6.647.412-K',
        'edad': 35,
        'genero': 'M',
        'urgencia': 'BAJA',
        'etapas': ['CONSULTA_MEDICA', 'ALTA'],
        'etapa_actual_index': 1,  # Alta
        'notas': 'Control de rutina, paciente estable.'
    },
    {
        'rut': '11.111.111-1',
        'edad': 28,
        'genero': 'F',
        'urgencia': 'ALTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'HOSPITALIZACION', 'OPERACION'],
        'etapa_actual_index': 2,  # Hospitalización
        'notas': 'Paciente requiere cirugía programada.'
    },
    {
        'rut': '19.876.543-2',
        'edad': 55,
        'genero': 'M',
        'urgencia': 'MEDIA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN'],
        'etapa_actual_index': 0,  # Consulta Médica
        'notas': 'Primera consulta, exámenes de rutina.'
    },
]

for pac_data in pacientes_data:
    # Crear hash del RUT
    identificador_hash = hashlib.sha256(pac_data['rut'].encode()).hexdigest()
    
    # Crear o actualizar paciente
    paciente, created = Paciente.objects.get_or_create(
        identificador_hash=identificador_hash,
        defaults={
            'edad': pac_data['edad'],
            'genero': pac_data['genero'],
            'nivel_urgencia': pac_data['urgencia'],
            'estado_actual': 'EN_CONSULTA',
            'activo': True,
            'metadatos_adicionales': {
                'notas': pac_data['notas'],
                'rut_original': pac_data['rut']  # Solo para referencia
            }
        }
    )
    
    if created or not paciente.rutas_clinicas.exists():
        # Crear ruta clínica
        ruta = RutaClinica.objects.create(
            paciente=paciente,
            etapas_seleccionadas=pac_data['etapas'],
            estado='EN_PROGRESO',
            fecha_inicio=timezone.now() - timedelta(hours=2),
            fecha_estimada_fin=timezone.now() + timedelta(hours=4),
        )
        
        # Iniciar la ruta
        ruta.iniciar_ruta()
        
        # Avanzar hasta la etapa actual
        for _ in range(pac_data['etapa_actual_index']):
            ruta.avanzar_etapa()
        
        print(f"✓ Paciente {pac_data['rut']} creado con ruta clínica")

print("\n" + "="*50)
print("DATOS DE EJEMPLO CREADOS EXITOSAMENTE")
print("="*50)
print("\nCredenciales de acceso:")
print("  Usuario: admin")
print("  Contraseña: admin123")
print("\nPuedes acceder a:")
print("  - Frontend: http://localhost:3000")
print("  - Backend Admin: http://127.0.0.1:8000/admin")
print("  - API: http://127.0.0.1:8000/api")
print("\n" + "="*50)