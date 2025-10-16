# backend/generate_patients_improved.py
# Script mejorado para generar pacientes con datos médicos completos
# Ejecutar con: python manage.py shell < generate_patients_improved.py

from pacientes.models import Paciente
from rutas_clinicas.models import RutaClinica
from django.utils import timezone
from datetime import timedelta
import hashlib

print("\n" + "="*60)
print("GENERANDO PACIENTES CON DATOS MÉDICOS COMPLETOS")
print("="*60 + "\n")

# Datos de 5 pacientes mejorados
pacientes_data = [
    {
        'rut': '12.345.678-9',
        'nombre': 'Ana María Torres',
        'edad': 42,
        'genero': 'F',
        'tipo_sangre': 'O+',
        'peso': 68.5,
        'altura': 165,
        'alergias': 'Penicilina, Polen',
        'condiciones_preexistentes': 'Hipertensión arterial controlada',
        'medicamentos_actuales': 'Losartán 50mg (1 vez al día)',
        'urgencia': 'MEDIA',
        'estado': 'EN_CONSULTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'REVISION_EXAMEN'],
        'etapa_actual_index': 1,
        'correo': 'ana.torres@email.com',
        'contacto': '+56 9 7846 1789',
        'direccion': 'Avenida Libertad 123, Viña del Mar',
        'seguro': 'Fonasa',
        'notas': 'Paciente con dolor lumbar persistente, derivada para exámenes'
    },
    {
        'rut': '18.765.432-1',
        'nombre': 'Carlos Andrés Muñoz',
        'edad': 35,
        'genero': 'M',
        'tipo_sangre': 'A+',
        'peso': 82.0,
        'altura': 178,
        'alergias': 'Sin alergias conocidas',
        'condiciones_preexistentes': 'Sin condiciones preexistentes',
        'medicamentos_actuales': 'Sin medicamentos',
        'urgencia': 'BAJA',
        'estado': 'EN_ESPERA',
        'etapas': ['CONSULTA_MEDICA', 'ALTA'],
        'etapa_actual_index': 0,
        'correo': 'carlos.munoz@email.com',
        'contacto': '+56 9 8123 4567',
        'direccion': 'Calle Principal 456, Quilpué',
        'seguro': 'Isapre Banmédica',
        'notas': 'Control preventivo anual, sin síntomas'
    },
    {
        'rut': '15.234.567-8',
        'nombre': 'Patricia Elena Rojas',
        'edad': 28,
        'genero': 'F',
        'tipo_sangre': 'B+',
        'peso': 58.0,
        'altura': 160,
        'alergias': 'Ibuprofeno, Mariscos',
        'condiciones_preexistentes': 'Asma leve',
        'medicamentos_actuales': 'Salbutamol (inhalador de rescate)',
        'urgencia': 'ALTA',
        'estado': 'EN_CONSULTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'HOSPITALIZACION', 'OPERACION'],
        'etapa_actual_index': 2,
        'correo': 'patricia.rojas@email.com',
        'contacto': '+56 9 6789 0123',
        'direccion': 'Pasaje Los Olivos 789, Villa Alemana',
        'seguro': 'Isapre Consalud',
        'notas': 'Requiere cirugía programada, en evaluación pre-operatoria'
    },
    {
        'rut': '20.111.222-3',
        'nombre': 'Roberto Luis Silva',
        'edad': 55,
        'genero': 'M',
        'tipo_sangre': 'AB+',
        'peso': 95.5,
        'altura': 175,
        'alergias': 'Sin alergias conocidas',
        'condiciones_preexistentes': 'Diabetes tipo 2, Hipercolesterolemia',
        'medicamentos_actuales': 'Metformina 850mg (2 veces/día), Atorvastatina 20mg (noche)',
        'urgencia': 'MEDIA',
        'estado': 'EN_CONSULTA',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN'],
        'etapa_actual_index': 0,
        'correo': 'roberto.silva@email.com',
        'contacto': '+56 9 4567 8901',
        'direccion': 'Avenida España 321, Valparaíso',
        'seguro': 'Fonasa',
        'notas': 'Primera consulta por hipertensión, necesita exámenes'
    },
    {
        'rut': '16.987.654-3',
        'nombre': 'Valentina Paz González',
        'edad': 22,
        'genero': 'F',
        'tipo_sangre': 'O-',
        'peso': 52.0,
        'altura': 158,
        'alergias': 'Látex',
        'condiciones_preexistentes': 'Sin condiciones preexistentes',
        'medicamentos_actuales': 'Anticonceptivos orales',
        'urgencia': 'BAJA',
        'estado': 'PROCESO_PAUSADO',
        'etapas': ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'REVISION_EXAMEN', 'ALTA'],
        'etapa_actual_index': 1,
        'correo': 'valentina.gonzalez@email.com',
        'contacto': '+56 9 2345 6789',
        'direccion': 'Calle Álvarez 654, Viña del Mar',
        'seguro': 'Isapre Cruz Blanca',
        'notas': 'Esperando resultados de exámenes externos'
    },
]

print("Creando pacientes con información médica completa...\n")

for i, pac_data in enumerate(pacientes_data, 1):
    # Crear hash del RUT
    identificador_hash = hashlib.sha256(pac_data['rut'].encode()).hexdigest()
    
    # Eliminar paciente existente si hay uno
    Paciente.objects.filter(identificador_hash=identificador_hash).delete()
    
    # Crear paciente con TODOS los campos
    paciente = Paciente.objects.create(
        identificador_hash=identificador_hash,
        edad=pac_data['edad'],
        genero=pac_data['genero'],
        tipo_sangre=pac_data['tipo_sangre'],
        peso=pac_data['peso'],
        altura=pac_data['altura'],
        alergias=pac_data['alergias'],
        condiciones_preexistentes=pac_data['condiciones_preexistentes'],
        medicamentos_actuales=pac_data['medicamentos_actuales'],
        nivel_urgencia=pac_data['urgencia'],
        estado_actual=pac_data['estado'],
        activo=True,
        metadatos_adicionales={  # DICT, no lista
            'nombre': pac_data['nombre'],
            'rut_original': pac_data['rut'],
            'correo': pac_data['correo'],
            'contacto': pac_data['contacto'],
            'direccion': pac_data['direccion'],
            'seguro': pac_data['seguro'],
            'notas': pac_data['notas'],
        }
    )
    
    # Calcular IMC
    imc = paciente.calcular_imc()
    categoria_imc = paciente.obtener_categoria_imc()
    
    print(f"✓ Paciente {i}: {pac_data['nombre']}")
    print(f"  RUT: {pac_data['rut']}")
    print(f"  Edad: {pac_data['edad']} años | Género: {pac_data['genero']}")
    print(f"  Tipo Sangre: {pac_data['tipo_sangre']}")
    print(f"  Peso: {pac_data['peso']} kg | Altura: {pac_data['altura']} cm")
    print(f"  IMC: {imc} ({categoria_imc})")
    print(f"  Alergias: {pac_data['alergias']}")
    print(f"  Condiciones: {pac_data['condiciones_preexistentes']}")
    print(f"  Medicamentos: {pac_data['medicamentos_actuales']}")
    print(f"  Urgencia: {pac_data['urgencia']}")
    print(f"  Estado: {pac_data['estado']}")
    
    # Crear ruta clínica
    horas_atras = [2, 3, 1, 4, 2][i-1]
    
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
    
    # Si está pausado, pausar la ruta
    if pac_data['estado'] == 'PROCESO_PAUSADO':
        ruta.pausar_ruta("Esperando resultados de exámenes externos")
    
    print(f"  Ruta clínica: {len(pac_data['etapas'])} etapas")
    print(f"  Etapa actual: {pac_data['etapas'][pac_data['etapa_actual_index']] if pac_data['etapa_actual_index'] < len(pac_data['etapas']) else 'Completada'}")
    print(f"  Progreso: {ruta.porcentaje_completado:.1f}%")
    print()

print("="*60)
print("✅ GENERACIÓN COMPLETADA")
print("="*60)
print(f"\n{len(pacientes_data)} pacientes creados con datos médicos completos")
print("\nPuedes verlos en:")
print("  - Frontend: http://localhost:3000")
print("  - Admin: http://127.0.0.1:8000/admin/pacientes/paciente/")
print("\nCredenciales:")
print("  Usuario: admin")
print("  Contraseña: admin123")
print("\n" + "="*60 + "\n")
