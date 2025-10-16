# Script para generar 5 pacientes en Django
# Ejecutar con: python manage.py shell < generate_5_patients.py

from pacientes.models import Paciente
from rutas_clinicas.models import RutaClinica
from boxes.models import Box
from atenciones.models import Medico
from django.utils import timezone
from datetime import timedelta
import hashlib

print("\n" + "="*60)
print("GENERANDO 5 PACIENTES DE PRUEBA")
print("="*60 + "\n")

# Primero verificar/crear boxes si no existen
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

# Verificar/crear médicos si no existen
medicos_data = [
    {'codigo': 'MED001', 'nombre': 'Juan', 'apellido': 'Pérez', 'especialidad': 'MEDICINA_GENERAL'},
    {'codigo': 'MED002', 'nombre': 'María', 'apellido': 'González', 'especialidad': 'TRAUMATOLOGIA'},
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

print("✓ Boxes y médicos verificados\n")

# Datos de los 5 pacientes
pacientes_data = [
    {
        'rut': '12.345.678-9',
        'nombre': 'Ana María Torres',
        'edad': 42,
        'genero': 'F',
        'urgencia': 'MEDIA',
        'estado': 'EN_CONSULTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'REVISION_EXAMEN'],
        'etapa_actual_index': 1,
        'correo': 'ana.torres@email.com',
        'contacto': '+56 9 7846 1789',
        'direccion': 'Avenida Libertad 123, Viña del Mar',
        'tipo_sangre': 'O+',
        'seguro': 'Fonasa',
        'notas': 'Paciente con dolor lumbar persistente, derivada para exámenes'
    },
    {
        'rut': '18.765.432-1',
        'nombre': 'Carlos Andrés Muñoz',
        'edad': 35,
        'genero': 'M',
        'urgencia': 'BAJA',
        'estado': 'EN_ESPERA',
        'etapas': ['CONSULTA_MEDICA', 'ALTA'],
        'etapa_actual_index': 0,
        'correo': 'carlos.munoz@email.com',
        'contacto': '+56 9 8123 4567',
        'direccion': 'Calle Principal 456, Quilpué',
        'tipo_sangre': 'A+',
        'seguro': 'Isapre Banmédica',
        'notas': 'Control preventivo anual, sin síntomas'
    },
    {
        'rut': '15.234.567-8',
        'nombre': 'Patricia Elena Rojas',
        'edad': 28,
        'genero': 'F',
        'urgencia': 'ALTA',
        'estado': 'EN_CONSULTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'HOSPITALIZACION', 'OPERACION'],
        'etapa_actual_index': 2,
        'correo': 'patricia.rojas@email.com',
        'contacto': '+56 9 6789 0123',
        'direccion': 'Pasaje Los Olivos 789, Villa Alemana',
        'tipo_sangre': 'B+',
        'seguro': 'Isapre Consalud',
        'notas': 'Paciente requiere cirugía programada, actualmente en evaluación pre-operatoria'
    },
    {
        'rut': '20.111.222-3',
        'nombre': 'Roberto Luis Silva',
        'edad': 55,
        'genero': 'M',
        'urgencia': 'MEDIA',
        'estado': 'EN_CONSULTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN'],
        'etapa_actual_index': 0,
        'correo': 'roberto.silva@email.com',
        'contacto': '+56 9 4567 8901',
        'direccion': 'Avenida España 321, Valparaíso',
        'tipo_sangre': 'AB+',
        'seguro': 'Fonasa',
        'notas': 'Primera consulta por hipertensión, necesita exámenes de laboratorio'
    },
    {
        'rut': '16.987.654-3',
        'nombre': 'Valentina Paz González',
        'edad': 22,
        'genero': 'F',
        'urgencia': 'BAJA',
        'estado': 'PROCESO_PAUSADO',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'REVISION_EXAMEN', 'ALTA'],
        'etapa_actual_index': 1,
        'correo': 'valentina.gonzalez@email.com',
        'contacto': '+56 9 2345 6789',
        'direccion': 'Calle Álvarez 654, Viña del Mar',
        'tipo_sangre': 'O-',
        'seguro': 'Isapre Cruz Blanca',
        'notas': 'Esperando resultados de exámenes de laboratorio externos'
    },
]

print("Creando pacientes...\n")

for i, pac_data in enumerate(pacientes_data, 1):
    # Crear hash del RUT
    identificador_hash = hashlib.sha256(pac_data['rut'].encode()).hexdigest()
    
    # Eliminar paciente existente si hay uno con el mismo hash
    Paciente.objects.filter(identificador_hash=identificador_hash).delete()
    
    # Crear paciente
    paciente = Paciente.objects.create(
        identificador_hash=identificador_hash,
        edad=pac_data['edad'],
        genero=pac_data['genero'],
        nivel_urgencia=pac_data['urgencia'],
        estado_actual=pac_data['estado'],
        activo=True,
        metadatos_adicionales={
            'nombre': pac_data['nombre'],
            'rut_original': pac_data['rut'],
            'correo': pac_data['correo'],
            'contacto': pac_data['contacto'],
            'direccion': pac_data['direccion'],
            'tipo_sangre': pac_data['tipo_sangre'],
            'seguro': pac_data['seguro'],
            'notas': pac_data['notas'],
        }
    )
    
    print(f"✓ Paciente {i}: {pac_data['nombre']}")
    print(f"  RUT: {pac_data['rut']}")
    print(f"  Edad: {pac_data['edad']} años")
    print(f"  Urgencia: {pac_data['urgencia']}")
    print(f"  Estado: {pac_data['estado']}")
    
    # Crear ruta clínica
    horas_atras = [2, 3, 1, 4, 2][i-1]  # Diferentes tiempos para cada paciente
    
    ruta = RutaClinica.objects.create(
        paciente=paciente,
        etapas_seleccionadas=pac_data['etapas'],
        estado='EN_PROGRESO',
        fecha_inicio=timezone.now() - timedelta(hours=horas_atras),
        fecha_estimada_fin=timezone.now() + timedelta(hours=4),
    )
    
    # Iniciar la ruta
    ruta.iniciar_ruta()
    
    # Avanzar hasta la etapa actual
    for _ in range(pac_data['etapa_actual_index']):
        ruta.avanzar_etapa()
    
    # Si el paciente está pausado, pausar la ruta
    if pac_data['estado'] == 'PROCESO_PAUSADO':
        ruta.pausar_ruta("Esperando resultados de exámenes externos")
    
    print(f"  Ruta clínica: {len(pac_data['etapas'])} etapas")
    print(f"  Etapa actual: {pac_data['etapas'][pac_data['etapa_actual_index']] if pac_data['etapa_actual_index'] < len(pac_data['etapas']) else 'Completada'}")
    print(f"  Progreso: {ruta.porcentaje_completado:.1f}%")
    print()

print("="*60)
print("✅ GENERACIÓN COMPLETADA EXITOSAMENTE")
print("="*60)
print(f"\nSe han creado {len(pacientes_data)} pacientes con sus rutas clínicas")
print("\nPuedes verlos en:")
print("  - Frontend: http://localhost:3000")
print("  - Admin: http://127.0.0.1:8000/admin/pacientes/paciente/")
print("\nCredenciales de admin:")
print("  Usuario: admin")
print("  Contraseña: admin123")
print("\n" + "="*60 + "\n")