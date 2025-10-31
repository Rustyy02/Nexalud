#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE POBLACIÓN DEFINITIVO - NEXALUD
=========================================

Ajustado a la estructura real de modelos de Nexalud

Uso: Get-Content populate_nexalud_final.py | python manage.py shell
"""

from django.utils import timezone
from datetime import timedelta, date
from random import choice, randint, sample
from decimal import Decimal
import json

print("\n" + "="*70)
print("🏥 POBLACIÓN DE BASE DE DATOS - NEXALUD")
print("="*70)

# =============================================================================
# IMPORTAR MODELOS
# =============================================================================
print("\n📦 Importando modelos...")

from pacientes.models import Paciente
from boxes.models import Box, OcupacionManual
from atenciones.models import Atencion, Medico

print("  ✅ Todos los modelos importados correctamente")

# =============================================================================
# DATOS DE PRUEBA
# =============================================================================

NOMBRES = [
    'Juan', 'María', 'Pedro', 'Ana', 'Luis', 'Carmen', 'José', 'Isabel',
    'Carlos', 'Rosa', 'Miguel', 'Patricia', 'Antonio', 'Laura', 'Francisco',
    'Elena', 'Manuel', 'Beatriz', 'Javier', 'Lucía', 'David', 'Cristina',
    'Andrés', 'Sofía', 'Diego', 'Valentina', 'Matías', 'Camila', 'Sebastián', 'Fernanda'
]

APELLIDOS = [
    'García', 'Rodríguez', 'Martínez', 'López', 'González', 'Hernández',
    'Pérez', 'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez',
    'Díaz', 'Cruz', 'Morales', 'Reyes', 'Gutiérrez', 'Ortiz', 'Jiménez'
]

COMUNAS_CHILE = [
    'Santiago', 'Providencia', 'Las Condes', 'Ñuñoa', 'La Florida',
    'Maipú', 'Puente Alto', 'San Bernardo', 'Quilicura', 'Peñalolén',
    'La Reina', 'Vitacura', 'Lo Barnechea', 'Huechuraba', 'Recoleta'
]

CIUDADES_CHILE = [
    'Santiago', 'Valparaíso', 'Viña del Mar', 'Concepción', 'Temuco',
    'Antofagasta', 'Iquique', 'La Serena', 'Rancagua', 'Talca'
]

REGIONES_CHILE = [
    'Metropolitana', 'Valparaíso', 'Biobío', 'Araucanía', 'Los Lagos',
    'Maule', 'Antofagasta', 'Coquimbo', 'O\'Higgins', 'Tarapacá'
]

TIPOS_SANGRE = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

SEGUROS_MEDICOS = ['FONASA', 'ISAPRE', 'PARTICULAR', 'OTRO']

ALERGIAS_COMUNES = [
    'Ninguna',
    'Penicilina',
    'Polen',
    'Ácaros',
    'Mariscos',
    'Látex',
    'Aspirina',
    'Ibuprofeno'
]

CONDICIONES_COMUNES = [
    'Ninguna',
    'Hipertensión arterial',
    'Diabetes mellitus tipo 2',
    'Asma',
    'Hipotiroidismo',
    'Colesterol alto',
    'Arritmia cardíaca'
]

MEDICAMENTOS_COMUNES = [
    'Ninguno',
    'Enalapril 10mg',
    'Metformina 850mg',
    'Losartán 50mg',
    'Atorvastatina 20mg',
    'Omeprazol 20mg',
    'Levotiroxina 100mcg'
]

def generar_rut():
    """Genera un RUT chileno válido"""
    numero = randint(10000000, 25000000)
    suma = 0
    multiplo = 2
    for d in str(numero)[::-1]:
        suma += int(d) * multiplo
        multiplo = multiplo + 1 if multiplo < 7 else 2
    dv = 11 - (suma % 11)
    dv = '0' if dv == 11 else ('K' if dv == 10 else str(dv))
    return f"{numero}-{dv}"

def calcular_edad(fecha_nacimiento):
    """Calcula la edad a partir de la fecha de nacimiento"""
    hoy = date.today()
    edad = hoy.year - fecha_nacimiento.year
    if hoy.month < fecha_nacimiento.month or (hoy.month == fecha_nacimiento.month and hoy.day < fecha_nacimiento.day):
        edad -= 1
    return edad

# =============================================================================
# 1. CREAR BOXES
# =============================================================================
print("\n🏥 Creando Boxes...")

boxes_data = [
    {
        'numero': 'BOX-001',
        'nombre': 'Box Medicina General 1',
        'especialidad': 'GENERAL',
        'equipamiento': ['Camilla', 'Tensiómetro', 'Termómetro', 'Oxímetro']
    },
    {
        'numero': 'BOX-002',
        'nombre': 'Box Cardiología',
        'especialidad': 'CARDIOLOGIA',
        'equipamiento': ['Camilla', 'Electrocardiógrafo', 'Tensiómetro']
    },
    {
        'numero': 'BOX-003',
        'nombre': 'Box Pediatría',
        'especialidad': 'PEDIATRIA',
        'equipamiento': ['Camilla pediátrica', 'Balanza', 'Tallímetro']
    },
    {
        'numero': 'BOX-004',
        'nombre': 'Box Procedimientos',
        'especialidad': 'PROCEDIMIENTOS',
        'equipamiento': ['Camilla', 'Mesa de instrumentos', 'Lámpara']
    },
    {
        'numero': 'BOX-005',
        'nombre': 'Box Multiuso',
        'especialidad': 'MULTIUSO',
        'capacidad_maxima': 2,
        'equipamiento': ['Camilla', 'Silla', 'Mesa']
    },
    {
        'numero': 'BOX-006',
        'nombre': 'Box Traumatología',
        'especialidad': 'TRAUMATOLOGIA',
        'equipamiento': ['Camilla', 'Negatoscopio', 'Férulas']
    }
]

boxes = []
for data in boxes_data:
    box, created = Box.objects.get_or_create(
        numero=data['numero'],
        defaults=data
    )
    boxes.append(box)
    status = "✅" if created else "ℹ️"
    print(f"{status} {box.numero} - {box.nombre}")

print(f"✅ Total boxes: {len(boxes)}")

# =============================================================================
# 2. CREAR MÉDICOS
# =============================================================================
print("\n👨‍⚕️ Creando Médicos...")

medicos_data = [
    {
        'codigo_medico': 'MED-001',
        'nombre': 'Roberto',
        'apellido': 'González',
        'especialidad_principal': 'MEDICINA_GENERAL'
    },
    {
        'codigo_medico': 'MED-002',
        'nombre': 'María',
        'apellido': 'Fernández',
        'especialidad_principal': 'CARDIOLOGIA'
    },
    {
        'codigo_medico': 'MED-003',
        'nombre': 'Patricia',
        'apellido': 'Ramírez',
        'especialidad_principal': 'PEDIATRIA'
    },
    {
        'codigo_medico': 'MED-004',
        'nombre': 'Carlos',
        'apellido': 'Muñoz',
        'especialidad_principal': 'TRAUMATOLOGIA'
    },
    {
        'codigo_medico': 'MED-005',
        'nombre': 'Andrea',
        'apellido': 'Torres',
        'especialidad_principal': 'MEDICINA_INTERNA'
    }
]

medicos = []
for data in medicos_data:
    medico, created = Medico.objects.get_or_create(
        codigo_medico=data['codigo_medico'],
        defaults=data
    )
    medicos.append(medico)
    status = "✅" if created else "ℹ️"
    print(f"{status} Dr. {medico.nombre} {medico.apellido}")

print(f"✅ Total médicos: {len(medicos)}")

# =============================================================================
# 3. CREAR PACIENTES
# =============================================================================
print("\n👥 Creando 30 Pacientes...")

pacientes = []
errores = 0

for i in range(30):
    try:
        # Generar edad y fecha de nacimiento
        edad_anos = randint(1, 90)
        fecha_nacimiento = date.today() - timedelta(days=edad_anos * 365 + randint(0, 364))
        edad_calculada = calcular_edad(fecha_nacimiento)
        
        # Datos personales
        nombre = choice(NOMBRES)
        apellido_p = choice(APELLIDOS)
        apellido_m = choice(APELLIDOS)
        genero = choice(['M', 'F', 'O'])
        
        # Dirección
        calle = choice(['Los Álamos', 'Las Rosas', 'El Bosque', 'San Martín', 'Av. Providencia'])
        numero_calle = randint(100, 9999)
        comuna = choice(COMUNAS_CHILE)
        ciudad = choice(CIUDADES_CHILE)
        region = choice(REGIONES_CHILE)
        codigo_postal = randint(1000000, 9999999)
        
        # Datos médicos
        peso = Decimal(str(randint(30, 120) + randint(0, 9) / 10))
        altura = randint(50, 200)  # en cm
        tipo_sangre = choice(TIPOS_SANGRE)
        
        # Alergias y condiciones
        alergias = choice(ALERGIAS_COMUNES)
        condiciones = choice(CONDICIONES_COMUNES)
        medicamentos = choice(MEDICAMENTOS_COMUNES)
        
        # Seguro médico
        seguro = choice(SEGUROS_MEDICOS)
        numero_beneficiario = f"{randint(100000, 999999)}-{randint(1, 9)}"
        
        # Estado
        estado_actual = choice(['INGRESO', 'ESPERA', 'EN_ATENCION', 'EN_EXAMENES'])
        etapa_actual = choice(['REGISTRO', 'TRIAJE', 'ATENCION', 'EXAMENES'])
        nivel_urgencia = choice(['BAJA', 'MEDIA', 'ALTA', 'CRITICA'])
        
        # Crear paciente con TODOS los campos
        paciente = Paciente.objects.create(
            rut=generar_rut(),
            nombre=nombre,
            apellido_paterno=apellido_p,
            apellido_materno=apellido_m,
            fecha_nacimiento=fecha_nacimiento,
            edad=edad_calculada,
            genero=genero,
            correo=f"{nombre.lower()}.{apellido_p.lower()}{randint(1,999)}@email.com",
            telefono=f"+56 9 {randint(5000,9999)} {randint(1000,9999)}",
            telefono_emergencia=f"+56 9 {randint(5000,9999)} {randint(1000,9999)}",
            nombre_contacto_emergencia=f"{choice(NOMBRES)} {choice(APELLIDOS)}",
            direccion_calle=f"{calle} {numero_calle}",
            direccion_comuna=comuna,
            direccion_ciudad=ciudad,
            direccion_region=region,
            direccion_codigo_postal=str(codigo_postal),
            seguro_medico=seguro,
            numero_beneficiario=numero_beneficiario,
            tipo_sangre=tipo_sangre,
            peso=peso,
            altura=altura,
            alergias=alergias,
            condiciones_preexistentes=condiciones,
            medicamentos_actuales=medicamentos,
            estado_actual=estado_actual,
            etapa_actual=etapa_actual,
            nivel_urgencia=nivel_urgencia,
            activo=True,
            metadatos_adicionales={'origen': 'script_poblacion', 'version': '1.0'}
        )
        
        pacientes.append(paciente)
        
        if (i + 1) % 10 == 0:
            print(f"✅ {i+1}/30 pacientes creados")
            
    except Exception as e:
        errores += 1
        print(f"❌ Error en paciente {i+1}: {str(e)}")
        continue

print(f"✅ Total pacientes creados: {len(pacientes)}")
if errores > 0:
    print(f"⚠️  Errores: {errores}")

# =============================================================================
# 4. CREAR ATENCIONES
# =============================================================================
if len(pacientes) > 0 and len(medicos) > 0 and len(boxes) > 0:
    print("\n📋 Creando Atenciones...")
    
    # Seleccionar 10 pacientes aleatorios
    num_pacientes_atencion = min(10, len(pacientes))
    pacientes_sel = sample(pacientes, num_pacientes_atencion)
    atenciones = []
    
    for paciente in pacientes_sel:
        # Crear 1-3 atenciones por paciente
        num_atenciones = randint(1, 3)
        
        for j in range(num_atenciones):
            try:
                medico = choice(medicos)
                box = choice(boxes)
                
                # Fecha aleatoria
                dias_offset = randint(-30, 7)
                hora = randint(8, 17)
                minuto = choice([0, 15, 30, 45])
                
                fecha_hora = timezone.now() + timedelta(
                    days=dias_offset,
                    hours=hora - timezone.now().hour,
                    minutes=minuto - timezone.now().minute,
                    seconds=-timezone.now().second,
                    microseconds=-timezone.now().microsecond
                )
                
                # Duración
                duracion = choice([15, 20, 30, 45, 60])
                
                # Estado según fecha
                if dias_offset < -7:
                    estado = 'COMPLETADA'
                elif dias_offset < 0:
                    estado = choice(['COMPLETADA', 'COMPLETADA', 'CANCELADA'])
                elif dias_offset == 0:
                    estado = choice(['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO'])
                else:
                    estado = 'PROGRAMADA'
                
                # Crear atención
                atencion = Atencion.objects.create(
                    paciente=paciente,
                    medico=medico,
                    box=box,
                    fecha_hora_inicio=fecha_hora,
                    fecha_hora_fin=fecha_hora + timedelta(minutes=duracion),
                    duracion_planificada=duracion,
                    estado=estado,
                    tipo_atencion=choice([
                        'CONSULTA_GENERAL',
                        'CONSULTA_ESPECIALIDAD',
                        'CONTROL',
                        'PROCEDIMIENTO',
                        'EXAMEN',
                        'URGENCIA'
                    ])
                )
                
                # Si está completada, agregar tiempos reales
                if estado == 'COMPLETADA':
                    retraso = randint(0, 15)
                    atencion.inicio_cronometro = fecha_hora + timedelta(minutes=retraso)
                    duracion_real = duracion + randint(-10, 20)
                    atencion.duracion_real = max(5, duracion_real)
                    atencion.fin_cronometro = atencion.inicio_cronometro + timedelta(minutes=atencion.duracion_real)
                    atencion.save()
                elif estado == 'EN_CURSO':
                    atencion.inicio_cronometro = fecha_hora + timedelta(minutes=randint(0, 10))
                    atencion.save()
                
                atenciones.append(atencion)
                
            except Exception as e:
                if len(atenciones) < 3:
                    print(f"⚠️  Error: {str(e)}")
                continue
    
    print(f"✅ Total atenciones creadas: {len(atenciones)}")
else:
    print("\n⚠️  No se pueden crear atenciones")
    atenciones = []

# =============================================================================
# 5. CREAR OCUPACIONES MANUALES
# =============================================================================
if len(boxes) > 0:
    print("\n🔒 Creando Ocupaciones Manuales...")
    
    motivos = [
        'Limpieza profunda',
        'Mantenimiento de equipos',
        'Instalación de equipamiento',
        'Fumigación',
        'Reparaciones'
    ]
    
    for i in range(3):
        try:
            box = choice(boxes)
            dias = randint(0, 3)
            fecha_inicio = timezone.now() + timedelta(days=dias, hours=randint(12, 16))
            duracion = choice([30, 60, 90, 120])
            
            OcupacionManual.objects.create(
                box=box,
                duracion_minutos=duracion,
                fecha_inicio=fecha_inicio,
                fecha_fin_programada=fecha_inicio + timedelta(minutes=duracion),
                motivo=choice(motivos),
                activa=dias <= 1
            )
        except Exception as e:
            print(f"⚠️  Error: {str(e)[:50]}")
    
    print(f"✅ Ocupaciones manuales creadas: 3")

# =============================================================================
# 6. GENERAR RUTAS CLÍNICAS (JSON)
# =============================================================================
print("\n🔄 Generando datos de rutas clínicas...")

ETAPAS = [
    'INGRESO', 'TRIAJE', 'ESPERA_ATENCION', 'EN_ATENCION', 
    'EXAMENES', 'ESPERA_RESULTADOS', 'DIAGNOSTICO', 'TRATAMIENTO', 
    'ALTA', 'SEGUIMIENTO'
]

rutas = []
for paciente in pacientes[:20]:
    try:
        etapa = choice(ETAPAS)
        estado = choice(['EN_PROCESO', 'COMPLETADA', 'PAUSADA'])
        
        ruta = {
            'paciente_id': str(paciente.id),
            'paciente_rut': paciente.rut,
            'paciente_nombre': f"{paciente.nombre} {paciente.apellido_paterno}",
            'etapa_actual': etapa,
            'estado': estado,
            'prioridad': paciente.nivel_urgencia,
            'fecha_inicio': (timezone.now() - timedelta(days=randint(0, 30))).isoformat(),
            'edad': paciente.edad,
            'seguro': paciente.seguro_medico
        }
        rutas.append(ruta)
    except Exception as e:
        continue

# Guardar JSON
try:
    with open('rutas_clinicas_generadas.json', 'w', encoding='utf-8') as f:
        json.dump(rutas, f, indent=2, ensure_ascii=False)
    print(f"✅ {len(rutas)} rutas generadas → rutas_clinicas_generadas.json")
except:
    print(f"✅ {len(rutas)} rutas generadas (JSON no guardado)")

# =============================================================================
# RESUMEN FINAL
# =============================================================================
print("\n" + "="*70)
print("📊 RESUMEN FINAL")
print("="*70)
print(f"👥 Pacientes: {Paciente.objects.count()}")
print(f"🏥 Boxes: {Box.objects.count()}")
print(f"👨‍⚕️ Médicos: {Medico.objects.count()}")
print(f"📋 Atenciones: {Atencion.objects.count()}")
print(f"🔒 Ocupaciones: {OcupacionManual.objects.count()}")
print(f"🔄 Rutas (JSON): {len(rutas)}")
print("="*70)

# Estadísticas
if Atencion.objects.exists():
    print("\n📊 Atenciones por estado:")
    from django.db.models import Count
    for e in Atencion.objects.values('estado').annotate(c=Count('id')):
        print(f"  - {e['estado']}: {e['c']}")

if Paciente.objects.exists():
    print("\n👥 Pacientes por nivel de urgencia:")
    for e in Paciente.objects.values('nivel_urgencia').annotate(c=Count('id')):
        print(f"  - {e['nivel_urgencia']}: {e['c']}")

print("\n✅ ¡PROCESO COMPLETADO EXITOSAMENTE!")
print("="*70)