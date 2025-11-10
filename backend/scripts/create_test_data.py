# backend/create_data.py
"""
Script independiente para crear datos de prueba.
Ejecutar: python create_data.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importar modelos despues de configurar Django
from django.utils import timezone
from boxes.models import Box
from pacientes.models import Paciente
from atenciones.models import Medico, Atencion
from rutas_clinicas.models import RutaClinica

print("=" * 60)
print("INICIANDO CREACION DE DATOS DE PRUEBA")
print("=" * 60)

# ============================================
# 1. CREAR BOXES
# ============================================
print("\n1. Creando Boxes...")

boxes_data = [
    {
        'numero': 'BOX-001',
        'nombre': 'Box Medicina General 1',
        'especialidad': 'GENERAL',
        'equipamiento': ['Camilla', 'Tensiometro', 'Estetoscopio', 'Termometro'],
    },
    {
        'numero': 'BOX-002',
        'nombre': 'Box Medicina General 2',
        'especialidad': 'GENERAL',
        'equipamiento': ['Camilla', 'Tensiometro', 'Estetoscopio'],
    },
    {
        'numero': 'BOX-003',
        'nombre': 'Box Cardiologia',
        'especialidad': 'CARDIOLOGIA',
        'equipamiento': ['Electrocardiograma', 'Monitor Cardiaco', 'Desfibrilador'],
    },
    {
        'numero': 'BOX-004',
        'nombre': 'Box Pediatria',
        'especialidad': 'PEDIATRIA',
        'equipamiento': ['Camilla Pediatrica', 'Juguetes', 'Tallimetro', 'Balanza'],
    },
    {
        'numero': 'BOX-005',
        'nombre': 'Box Traumatologia',
        'especialidad': 'TRAUMATOLOGIA',
        'equipamiento': ['Camilla Ortopedica', 'Rayos X Portatil', 'Yeso'],
    },
    {
        'numero': 'SALA-RAD',
        'nombre': 'Sala de Radiologia',
        'especialidad': 'RADIOLOGIA',
        'equipamiento': ['Equipo de Rayos X', 'Escaner', 'Proteccion Plomada'],
    },
    {
        'numero': 'LAB-001',
        'nombre': 'Laboratorio Clinico',
        'especialidad': 'LABORATORIO',
        'equipamiento': ['Microscopio', 'Centrifuga', 'Refrigerador'],
    },
    {
        'numero': 'PROC-001',
        'nombre': 'Sala de Procedimientos',
        'especialidad': 'PROCEDIMIENTOS',
        'equipamiento': ['Mesa Quirurgica', 'Lampara Quirurgica', 'Instrumental'],
    },
]

boxes_creados = []
for box_data in boxes_data:
    box, created = Box.objects.get_or_create(
        numero=box_data['numero'],
        defaults={
            'nombre': box_data['nombre'],
            'especialidad': box_data['especialidad'],
            'equipamiento': box_data['equipamiento'],
            'activo': True,
            'estado': 'DISPONIBLE',
        }
    )
    boxes_creados.append(box)
    status = "[OK] Creado" if created else "[--] Ya existe"
    print(f"   {status}: {box.numero} - {box.nombre}")

print(f"\n[OK] Total de boxes: {len(boxes_creados)}")

# ============================================
# 2. CREAR MEDICOS
# ============================================
print("\n2. Creando Medicos...")

medicos_data = [
    {
        'codigo_medico': 'MED-001',
        'nombre': 'Juan Carlos',
        'apellido': 'Gonzalez Perez',
        'especialidad_principal': 'MEDICINA_GENERAL',
    },
    {
        'codigo_medico': 'MED-002',
        'nombre': 'Maria Elena',
        'apellido': 'Rodriguez Silva',
        'especialidad_principal': 'CARDIOLOGIA',
    },
    {
        'codigo_medico': 'MED-003',
        'nombre': 'Pedro Antonio',
        'apellido': 'Martinez Lopez',
        'especialidad_principal': 'PEDIATRIA',
    },
    {
        'codigo_medico': 'MED-004',
        'nombre': 'Ana Maria',
        'apellido': 'Fernandez Castro',
        'especialidad_principal': 'TRAUMATOLOGIA',
    },
    {
        'codigo_medico': 'MED-005',
        'nombre': 'Roberto',
        'apellido': 'Sanchez Morales',
        'especialidad_principal': 'MEDICINA_INTERNA',
    },
]

medicos_creados = []
for medico_data in medicos_data:
    medico, created = Medico.objects.get_or_create(
        codigo_medico=medico_data['codigo_medico'],
        defaults={
            'nombre': medico_data['nombre'],
            'apellido': medico_data['apellido'],
            'especialidad_principal': medico_data['especialidad_principal'],
            'activo': True,
        }
    )
    medicos_creados.append(medico)
    status = "[OK] Creado" if created else "[--] Ya existe"
    print(f"   {status}: {medico.codigo_medico} - Dr. {medico.nombre_completo}")

print(f"\n[OK] Total de medicos: {len(medicos_creados)}")

# ============================================
# 3. CREAR PACIENTES
# ============================================
print("\n3. Creando Pacientes...")

# Nombres SIN TILDES
nombres = ['Juan', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Lucia', 'Diego', 'Valentina', 'Mateo', 'Sofia',
           'Jose', 'Carmen', 'Luis', 'Isabel', 'Francisco']
apellidos_p = ['Gonzalez', 'Rodriguez', 'Perez', 'Sanchez', 'Ramirez', 'Torres', 'Flores', 'Rivera', 'Gomez', 'Diaz',
               'Martinez', 'Hernandez', 'Lopez', 'Garcia', 'Castro']
apellidos_m = ['Silva', 'Munoz', 'Rojas', 'Fernandez', 'Lopez', 'Hernandez', 'Castro', 'Morales', 'Vega', 'Nunez',
               'Ortiz', 'Jimenez', 'Ruiz', 'Alvarez', 'Vargas']

# Comunas de Chile
comunas = ['Valparaiso', 'Vina del Mar', 'Quilpue', 'Villa Alemana', 'Concon', 'Casablanca']

def generar_rut():
    """Genera un RUT chileno valido"""
    numero = random.randint(10000000, 25999999)
    
    suma = 0
    multiplicador = 2
    for digito in str(numero)[::-1]:
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    
    resto = suma % 11
    dv = 11 - resto
    
    if dv == 11:
        dv = '0'
    elif dv == 10:
        dv = 'K'
    else:
        dv = str(dv)
    
    rut_str = str(numero)
    rut_formateado = f"{rut_str[:-6]}.{rut_str[-6:-3]}.{rut_str[-3:]}-{dv}"
    
    return rut_formateado

pacientes_creados = []
for i in range(15):
    rut = generar_rut()
    
    while Paciente.objects.filter(rut=rut).exists():
        rut = generar_rut()
    
    edad = random.randint(18, 85)
    fecha_nac = datetime.now().date() - timedelta(days=edad*365)
    
    try:
        paciente = Paciente.objects.create(
            rut=rut,
            nombre=random.choice(nombres),
            apellido_paterno=random.choice(apellidos_p),
            apellido_materno=random.choice(apellidos_m),
            fecha_nacimiento=fecha_nac,
            genero=random.choice(['M', 'F']),
            correo=f'paciente{i+1}@mail.com',
            telefono=f'+5691234{random.randint(1000, 9999)}',
            direccion_calle=f'Calle {random.randint(1, 50)} #{random.randint(100, 999)}',
            direccion_comuna=random.choice(comunas),
            direccion_ciudad='Valparaiso',
            direccion_region='V',
            seguro_medico=random.choice(['FONASA_A', 'FONASA_B', 'FONASA_C', 'FONASA_D', 'PARTICULAR']),
            tipo_sangre=random.choice(['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']),
            peso=round(random.uniform(50, 95), 1),
            altura=random.randint(150, 190),
            nivel_urgencia=random.choice(['BAJA', 'MEDIA', 'ALTA']),
            estado_actual='EN_ESPERA',
        )
        pacientes_creados.append(paciente)
        print(f"   [OK] Creado: {paciente.nombre_completo} - RUT: {paciente.rut}")
    except Exception as e:
        print(f"   [ERROR] Error: {e}")

print(f"\n[OK] Total de pacientes: {len(pacientes_creados)}")

# ============================================
# 4. CREAR RUTAS CLINICAS
# ============================================
print("\n4. Creando Rutas Clinicas...")

# TODAS LAS RUTAS TIENEN LAS 6 ETAPAS COMPLETAS EN ORDEN
ETAPAS_COMPLETAS = [
    'CONSULTA_MEDICA',
    'PROCESO_EXAMEN',
    'REVISION_EXAMEN',
    'HOSPITALIZACION',
    'OPERACION',
    'ALTA'
]

rutas_creadas = []
for i, paciente in enumerate(pacientes_creados):  # TODOS los pacientes
    try:
        print(f"\n   [+] Creando ruta para: {paciente.nombre_completo}")
        
        # Crear ruta con TODAS las etapas
        ruta = RutaClinica.objects.create(
            paciente=paciente,
            etapas_seleccionadas=ETAPAS_COMPLETAS,
            fecha_inicio=timezone.now() - timedelta(hours=random.randint(1, 48)),
            estado='INICIADA',
        )
        
        print(f"       [OK] Ruta creada con ID: {str(ruta.id)[:8]}...")
        print(f"       [OK] Etapas configuradas: {len(ETAPAS_COMPLETAS)} etapas")
        
        # Decidir en que etapa iniciar (0-3, no mas alla)
        max_etapa_inicio = min(3, len(ETAPAS_COMPLETAS) - 1)
        indice_inicio = random.randint(0, max_etapa_inicio)
        etapa_inicial = ETAPAS_COMPLETAS[indice_inicio]
        
        print(f"       [OK] Iniciando en etapa: {etapa_inicial} (indice {indice_inicio})")
        
        # Iniciar la ruta
        ruta.iniciar_ruta(etapa_inicial=etapa_inicial)
        
        print(f"       [OK] Ruta iniciada correctamente")
        print(f"       [OK] Estado: {ruta.get_estado_display()}")
        print(f"       [OK] Etapa actual: {ruta.get_etapa_actual_display()}")
        print(f"       [OK] Progreso: {ruta.porcentaje_completado:.1f}%")
        
        # Avanzar aleatoriamente 0-2 etapas mas
        pasos_adicionales = random.randint(0, 2)
        
        for paso in range(pasos_adicionales):
            # Verificar que no estemos en la ultima etapa
            if ruta.indice_etapa_actual < len(ETAPAS_COMPLETAS) - 1:
                if random.random() > 0.3:  # 70% de probabilidad
                    print(f"       [>>] Avanzando etapa (paso {paso + 1})...")
                    ruta.avanzar_etapa(observaciones=f"Avance automatico - paso {paso + 1}")
                    print(f"            Nueva etapa: {ruta.get_etapa_actual_display() if ruta.etapa_actual else 'COMPLETADA'}")
                else:
                    break
        
        rutas_creadas.append(ruta)
        
        # Resumen final de la ruta
        estado_final = "COMPLETADA" if ruta.estado == 'COMPLETADA' else ruta.get_etapa_actual_display()
        print(f"       [OK] Estado final: {ruta.get_estado_display()}")
        print(f"       [OK] Ubicacion: {estado_final}")
        print(f"       [OK] Progreso: {ruta.porcentaje_completado:.1f}%")
        print(f"       [OK] Etapas completadas: {len(ruta.etapas_completadas)}/{len(ETAPAS_COMPLETAS)}")
        
    except Exception as e:
        print(f"   [ERROR] Error al crear ruta para {paciente.nombre_completo}:")
        print(f"           Error: {str(e)}")
        import traceback
        traceback.print_exc()

print(f"\n[OK] Total de rutas creadas: {len(rutas_creadas)}")

# ============================================
# 5. CREAR ATENCIONES
# ============================================
print("\n5. Creando Atenciones...")

tipos_atencion = ['CONSULTA_GENERAL', 'CONSULTA_ESPECIALIDAD', 'CONTROL', 'PROCEDIMIENTO', 'EXAMEN']

atenciones_creadas = []

for i, paciente in enumerate(pacientes_creados[:12]):
    num_atenciones = random.randint(1, 3)
    
    for j in range(num_atenciones):
        try:
            medico = random.choice(medicos_creados)
            box = random.choice(boxes_creados)
            
            dias_atras = random.randint(0, 7)
            hora_inicio = timezone.now() - timedelta(days=dias_atras, hours=random.randint(0, 8))
            
            duracion = random.choice([15, 20, 30, 45, 60])
            hora_fin = hora_inicio + timedelta(minutes=duracion)
            
            atencion = Atencion.objects.create(
                paciente=paciente,
                medico=medico,
                box=box,
                fecha_hora_inicio=hora_inicio,
                fecha_hora_fin=hora_fin,
                duracion_planificada=duracion,
                tipo_atencion=random.choice(tipos_atencion),
                estado='PROGRAMADA',
                observaciones=f'Atencion de prueba {j+1}'
            )
            
            estado_aleatorio = random.random()
            
            if estado_aleatorio < 0.3:
                atencion.iniciar_cronometro()
                atencion.duracion_real = random.randint(duracion - 5, duracion + 10)
                atencion.finalizar_cronometro()
            elif estado_aleatorio < 0.5:
                atencion.iniciar_cronometro()
            elif estado_aleatorio < 0.7:
                atencion.estado = 'EN_ESPERA'
                atencion.save()
            
            atenciones_creadas.append(atencion)
            
            print(f"   [OK] {atencion.get_estado_display()}: {paciente.nombre_completo} con {medico.nombre_completo}")
            
        except Exception as e:
            print(f"   [ERROR] Error: {e}")

print(f"\n[OK] Total de atenciones: {len(atenciones_creadas)}")

# ============================================
# RESUMEN FINAL
# ============================================
print("\n" + "=" * 60)
print("RESUMEN DE DATOS CREADOS")
print("=" * 60)

print(f"\n[BOXES] Total: {Box.objects.count()}")
print(f"   - Disponibles: {Box.objects.filter(estado='DISPONIBLE').count()}")
print(f"   - Ocupados: {Box.objects.filter(estado='OCUPADO').count()}")

print(f"\n[MEDICOS] Total: {Medico.objects.count()}")
print(f"   - Activos: {Medico.objects.filter(activo=True).count()}")

print(f"\n[PACIENTES] Total: {Paciente.objects.count()}")
print(f"   - Activos: {Paciente.objects.filter(activo=True).count()}")
print(f"   - En Espera: {Paciente.objects.filter(estado_actual='EN_ESPERA').count()}")
print(f"   - Activos en Proceso: {Paciente.objects.filter(estado_actual='ACTIVO').count()}")

print(f"\n[RUTAS CLINICAS] Total: {RutaClinica.objects.count()}")
print(f"   - Iniciadas: {RutaClinica.objects.filter(estado='INICIADA').count()}")
print(f"   - En Progreso: {RutaClinica.objects.filter(estado='EN_PROGRESO').count()}")
print(f"   - Completadas: {RutaClinica.objects.filter(estado='COMPLETADA').count()}")

# Mostrar detalles de cada ruta
print("\n   [DETALLES] Rutas creadas:")
for ruta in RutaClinica.objects.all()[:15]:
    etapa = ruta.get_etapa_actual_display() if ruta.etapa_actual else "COMPLETADA"
    print(f"      * {ruta.paciente.nombre_completo[:30]:30} | {ruta.get_estado_display():12} | {etapa:20} | {ruta.porcentaje_completado:5.1f}%")

print(f"\n[ATENCIONES] Total: {Atencion.objects.count()}")
print(f"   - Programadas: {Atencion.objects.filter(estado='PROGRAMADA').count()}")
print(f"   - En Espera: {Atencion.objects.filter(estado='EN_ESPERA').count()}")
print(f"   - En Curso: {Atencion.objects.filter(estado='EN_CURSO').count()}")
print(f"   - Completadas: {Atencion.objects.filter(estado='COMPLETADA').count()}")

print("\n" + "=" * 60)
print("[OK] SCRIPT COMPLETADO EXITOSAMENTE")
print("=" * 60)