import os
import sys
import django
import random
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Importar modelos después de configurar Django
from django.utils import timezone
from boxes.models import Box
from pacientes.models import Paciente
from atenciones.models import Atencion
from rutas_clinicas.models import RutaClinica
from users.models import User

print("=" * 80)
print("INICIANDO CREACIÓN DE DATOS DE PRUEBA - VERSIÓN ACTUALIZADA")
print("=" * 80)

# ============================================
# 1. CREAR BOXES (SIN CAMBIOS - PERFECTO)
# ============================================
print("\n1. Creando Boxes...")

boxes_data = [
    {
        'numero': 'BOX-001',
        'nombre': 'Box Medicina General 1',
        'especialidad': 'GENERAL',
        'equipamiento': ['Camilla', 'Tensiómetro', 'Estetoscopio', 'Termómetro'],
    },
    {
        'numero': 'BOX-002',
        'nombre': 'Box Medicina General 2',
        'especialidad': 'GENERAL',
        'equipamiento': ['Camilla', 'Tensiómetro', 'Estetoscopio'],
    },
    {
        'numero': 'BOX-003',
        'nombre': 'Box Cardiología',
        'especialidad': 'CARDIOLOGIA',
        'equipamiento': ['Electrocardiógrafo', 'Monitor Cardíaco', 'Desfibrilador'],
    },
    {
        'numero': 'BOX-004',
        'nombre': 'Box Pediatría',
        'especialidad': 'PEDIATRIA',
        'equipamiento': ['Camilla Pediátrica', 'Juguetes', 'Tallímetro', 'Balanza'],
    },
    {
        'numero': 'BOX-005',
        'nombre': 'Box Traumatología',
        'especialidad': 'TRAUMATOLOGIA',
        'equipamiento': ['Camilla Ortopédica', 'Rayos X Portátil', 'Yeso'],
    },
    {
        'numero': 'SALA-RAD',
        'nombre': 'Sala de Radiología',
        'especialidad': 'RADIOLOGIA',
        'equipamiento': ['Equipo de Rayos X', 'Escáner', 'Protección Plomada'],
    },
    {
        'numero': 'LAB-001',
        'nombre': 'Laboratorio Clínico',
        'especialidad': 'LABORATORIO',
        'equipamiento': ['Microscopio', 'Centrífuga', 'Refrigerador'],
    },
    {
        'numero': 'PROC-001',
        'nombre': 'Sala de Procedimientos',
        'especialidad': 'PROCEDIMIENTOS',
        'equipamiento': ['Mesa Quirúrgica', 'Lámpara Quirúrgica', 'Instrumental'],
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
    status = "✅ Creado" if created else "ℹ️  Ya existe"
    print(f"   {status}: {box.numero} - {box.nombre}")

print(f"\n✅ Total de boxes: {len(boxes_creados)}")

# ============================================
# 2. CREAR 30 PACIENTES DIVERSOS
# ============================================
print("\n2. Creando 30 Pacientes Diversos...")

# Nombres variados SIN TILDES
nombres_masculinos = ['Juan', 'Pedro', 'Carlos', 'Jose', 'Luis', 'Francisco', 'Diego', 'Mateo', 
                      'Miguel', 'Gabriel', 'Daniel', 'Alejandro', 'Sebastian', 'Martin', 'Fernando']
nombres_femeninos = ['Maria', 'Ana', 'Carmen', 'Lucia', 'Isabel', 'Sofia', 'Valentina', 'Camila',
                    'Fernanda', 'Daniela', 'Andrea', 'Paula', 'Carolina', 'Claudia', 'Patricia']

apellidos_p = ['Gonzalez', 'Rodriguez', 'Perez', 'Sanchez', 'Ramirez', 'Torres', 'Flores', 'Rivera', 
               'Gomez', 'Diaz', 'Martinez', 'Hernandez', 'Lopez', 'Garcia', 'Castro', 'Morales', 
               'Rojas', 'Silva', 'Munoz', 'Fernandez']
apellidos_m = ['Silva', 'Munoz', 'Rojas', 'Fernandez', 'Lopez', 'Hernandez', 'Castro', 'Morales', 
               'Vega', 'Nunez', 'Ortiz', 'Jimenez', 'Ruiz', 'Alvarez', 'Vargas', 'Soto', 'Pena', 
               'Guzman', 'Carrasco', 'Espinoza']

comunas = ['Valparaiso', 'Vina del Mar', 'Quilpue', 'Villa Alemana', 'Concon', 'Casablanca', 
           'Quintero', 'Puchuncavi', 'Limache', 'Olmue']

seguros = ['FONASA_A', 'FONASA_B', 'FONASA_C', 'FONASA_D', 'ISAPRE_BANMEDICA', 'ISAPRE_COLMENA', 
           'ISAPRE_CONSALUD', 'PARTICULAR']

def generar_rut_valido():
    """Genera un RUT chileno válido"""
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
print("\n   Generando pacientes con características diversas...")

for i in range(30):
    # Generar RUT único
    rut = generar_rut_valido()
    while Paciente.objects.filter(rut=rut).exists():
        rut = generar_rut_valido()
    
    # Características diversas
    genero = random.choice(['M', 'F'])
    nombres = nombres_masculinos if genero == 'M' else nombres_femeninos
    nombre = random.choice(nombres)
    
    # Edad variada (18-85 años)
    edad = random.randint(18, 85)
    fecha_nac = datetime.now().date() - timedelta(days=edad*365 + random.randint(0, 365))
    
    # Estados variados PERO TODOS ACTIVOS (activo=True)
    estados_posibles = ['EN_ESPERA', 'ACTIVO', 'PROCESO_PAUSADO']
    estado_actual = random.choice(estados_posibles)
    
    # Niveles de urgencia variados
    urgencias = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA']
    urgencia = random.choice(urgencias)
    
    try:
        paciente = Paciente.objects.create(
            rut=rut,
            nombre=nombre,
            apellido_paterno=random.choice(apellidos_p),
            apellido_materno=random.choice(apellidos_m),
            fecha_nacimiento=fecha_nac,
            genero=genero,
            correo=f'paciente{i+1}@mail.cl',
            telefono=f'+5691234{random.randint(1000, 9999)}',
            direccion_calle=f'Calle {random.randint(1, 100)} #{random.randint(100, 999)}',
            direccion_comuna=random.choice(comunas),
            direccion_ciudad='Valparaiso',
            direccion_region='V',
            seguro_medico=random.choice(seguros),
            tipo_sangre=random.choice(['O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-']),
            peso=round(random.uniform(50, 110), 1),
            altura=random.randint(150, 195),
            nivel_urgencia=urgencia,
            estado_actual=estado_actual,
            activo=True,  # ✅ TODOS ACTIVOS
            alergias=random.choice(['', 'Penicilina', 'Polen', 'Lactosa', '']) if random.random() > 0.7 else '',
        )
        pacientes_creados.append(paciente)
        
        urgencia_emoji = {'BAJA': '🟢', 'MEDIA': '🟡', 'ALTA': '🟠', 'CRITICA': '🔴'}
        print(f"   ✅ [{i+1:2d}/30] {paciente.nombre_completo:35} | {genero} | {edad:2d} años | {urgencia_emoji[urgencia]} {urgencia:8} | {estado_actual}")
        
    except Exception as e:
        print(f"   ❌ Error al crear paciente {i+1}: {e}")

print(f"\n✅ Total de pacientes creados: {len(pacientes_creados)}")
print(f"   📊 Todos los pacientes tienen activo=True")
print(f"   📊 Estados: EN_ESPERA: {sum(1 for p in pacientes_creados if p.estado_actual == 'EN_ESPERA')}")
print(f"   📊          ACTIVO: {sum(1 for p in pacientes_creados if p.estado_actual == 'ACTIVO')}")
print(f"   📊          PROCESO_PAUSADO: {sum(1 for p in pacientes_creados if p.estado_actual == 'PROCESO_PAUSADO')}")

# ============================================
# 3. CREAR RUTAS CLÍNICAS PARA TODOS
# ============================================
print("\n3. Creando Rutas Clínicas para TODOS los pacientes...")

ETAPAS_COMPLETAS = [
    'CONSULTA_MEDICA',
    'PROCESO_EXAMEN',
    'REVISION_EXAMEN',
    'HOSPITALIZACION',
    'OPERACION',
    'ALTA'
]

rutas_creadas = []
print("\n   Distribuyendo pacientes en diferentes etapas...")

for i, paciente in enumerate(pacientes_creados):
    try:
        # Crear ruta con fecha de inicio variada (últimos 7 días)
        dias_atras = random.randint(0, 7)
        fecha_inicio = timezone.now() - timedelta(days=dias_atras, hours=random.randint(0, 23))
        
        ruta = RutaClinica.objects.create(
            paciente=paciente,
            etapas_seleccionadas=ETAPAS_COMPLETAS,
            fecha_inicio=fecha_inicio,
            estado='INICIADA',
        )
        
        # Determinar etapa inicial de forma distribuida
        # Distribuir equitativamente entre las etapas
        if i < 5:  # Primeros 5 en CONSULTA_MEDICA
            indice_inicio = 0
        elif i < 10:  # Siguientes 5 en PROCESO_EXAMEN
            indice_inicio = 1
        elif i < 15:  # Siguientes 5 en REVISION_EXAMEN
            indice_inicio = 2
        elif i < 20:  # Siguientes 5 en HOSPITALIZACION
            indice_inicio = 3
        elif i < 25:  # Siguientes 5 en OPERACION
            indice_inicio = 4
        else:  # Últimos 5 en diferentes etapas
            indice_inicio = random.randint(0, 4)
        
        etapa_inicial = ETAPAS_COMPLETAS[indice_inicio]
        
        # Iniciar la ruta
        ruta.iniciar_ruta(etapa_inicial=etapa_inicial)
        
        # Decidir si avanzar 0-2 etapas más (70% probabilidad)
        if random.random() > 0.3 and ruta.indice_etapa_actual < len(ETAPAS_COMPLETAS) - 1:
            pasos = random.randint(0, 2)
            for paso in range(pasos):
                if ruta.indice_etapa_actual < len(ETAPAS_COMPLETAS) - 1:
                    ruta.avanzar_etapa(observaciones=f"Avance automático {paso + 1}")
        
        # 10% de probabilidad de pausar la ruta
        if random.random() < 0.1 and ruta.estado == 'EN_PROGRESO':
            ruta.pausar_ruta(motivo="Pausa temporal para evaluación")
        
        # 5% de probabilidad de completar la ruta
        if random.random() < 0.05 and ruta.estado == 'EN_PROGRESO':
            while ruta.indice_etapa_actual < len(ETAPAS_COMPLETAS):
                ruta.avanzar_etapa(observaciones="Completado rápidamente")
        
        rutas_creadas.append(ruta)
        
        estado_emoji = {
            'INICIADA': '🆕',
            'EN_PROGRESO': '▶️',
            'PAUSADA': '⏸️',
            'COMPLETADA': '✅',
            'CANCELADA': '❌'
        }
        
        etapa_display = ruta.get_etapa_actual_display() if ruta.etapa_actual else 'COMPLETADA'
        print(f"   {estado_emoji.get(ruta.estado, '•')} [{i+1:2d}/30] {paciente.nombre_completo:35} | {ruta.get_estado_display():12} | {etapa_display:20} | {ruta.porcentaje_completado:5.1f}%")
        
    except Exception as e:
        print(f"   ❌ Error al crear ruta para {paciente.nombre_completo}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n✅ Total de rutas creadas: {len(rutas_creadas)}")
print(f"   📊 Distribución por estado:")
for estado_key, estado_label in RutaClinica.ESTADO_CHOICES:
    count = sum(1 for r in rutas_creadas if r.estado == estado_key)
    if count > 0:
        print(f"      • {estado_label}: {count}")

# ============================================
# 4. CREAR 15 ATENCIONES EN NOVIEMBRE 2025
# ============================================
print("\n4. Creando 15 Atenciones distribuidas en Noviembre 2025...")

tipos_atencion = ['CONSULTA_GENERAL', 'CONSULTA_ESPECIALIDAD', 'CONTROL', 'PROCEDIMIENTO', 'EXAMEN']
duraciones_minutos = [15, 20, 30, 45, 60]

atenciones_creadas = []

# Definir el rango de fechas: Noviembre 2025
noviembre_inicio = timezone.datetime(2025, 11, 1, 8, 0, 0)
noviembre_fin = timezone.datetime(2025, 11, 30, 18, 0, 0)

# Asegurar que las fechas son timezone-aware
noviembre_inicio = timezone.make_aware(noviembre_inicio)
noviembre_fin = timezone.make_aware(noviembre_fin)

print("\n   Generando atenciones del 1 al 30 de Noviembre 2025...")

for i in range(15):
    try:
        # Seleccionar paciente, médico y box aleatorios
        paciente = random.choice(pacientes_creados)
        medico = random.choice(User.objects.filter(rol='MEDICO', is_active=True))
        box = random.choice(boxes_creados)
        
        # Generar fecha aleatoria en noviembre 2025
        dias_diferencia = (noviembre_fin - noviembre_inicio).days
        dia_aleatorio = random.randint(0, dias_diferencia)
        hora_aleatoria = random.randint(8, 17)  # Entre 8 AM y 5 PM
        minuto_aleatorio = random.choice([0, 15, 30, 45])  # Cada 15 minutos
        
        fecha_hora_inicio = noviembre_inicio + timedelta(
            days=dia_aleatorio,
            hours=hora_aleatoria - 8,  # Ajustar desde las 8 AM
            minutes=minuto_aleatorio
        )
        
        # Duración
        duracion = random.choice(duraciones_minutos)
        fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=duracion)
        
        # Tipo de atención
        tipo = random.choice(tipos_atencion)
        
        # Crear atención
        atencion = Atencion.objects.create(
            paciente=paciente,
            medico=medico,
            box=box,
            fecha_hora_inicio=fecha_hora_inicio,
            fecha_hora_fin=fecha_hora_fin,
            duracion_planificada=duracion,
            tipo_atencion=tipo,
            estado='PROGRAMADA',
            observaciones=f'Atención generada automáticamente #{i+1}'
        )
        
        # Asignar estados variados según la fecha
        ahora = timezone.now()
        
        if fecha_hora_inicio < ahora:  # Atención en el pasado
            estado_aleatorio = random.random()
            
            if estado_aleatorio < 0.6:  # 60% completadas
                atencion.iniciar_cronometro()
                atencion.finalizar_cronometro()
            elif estado_aleatorio < 0.8:  # 20% canceladas
                atencion.estado = 'CANCELADA'
                atencion.observaciones += " - Cancelada por el paciente"
                atencion.save()
            else:  # 20% no presentado
                atencion.estado = 'NO_PRESENTADO'
                atencion.observaciones += " - Paciente no se presentó"
                atencion.save()
        else:  # Atención futura
            if random.random() < 0.3:  # 30% en espera
                atencion.estado = 'EN_ESPERA'
                atencion.save()
        
        atenciones_creadas.append(atencion)
        
        estado_emoji = {
            'PROGRAMADA': '📅',
            'EN_ESPERA': '⏳',
            'EN_CURSO': '▶️',
            'COMPLETADA': '✅',
            'CANCELADA': '❌',
            'NO_PRESENTADO': '🚫'
        }
        
        fecha_str = fecha_hora_inicio.strftime('%d/%m %H:%M')
        print(f"   {estado_emoji.get(atencion.estado, '•')} [{i+1:2d}/15] {fecha_str} | {tipo:25} | {paciente.nombre_completo:30} | {atencion.get_estado_display()}")
        
    except Exception as e:
        print(f"   ❌ Error al crear atención {i+1}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n✅ Total de atenciones creadas: {len(atenciones_creadas)}")
print(f"   📊 Distribución por estado:")
for estado_key, estado_label in Atencion.ESTADO_CHOICES:
    count = sum(1 for a in atenciones_creadas if a.estado == estado_key)
    if count > 0:
        print(f"      • {estado_label}: {count}")

# ============================================
# RESUMEN FINAL DETALLADO
# ============================================
print("\n" + "=" * 80)
print("RESUMEN FINAL DE DATOS CREADOS")
print("=" * 80)

print(f"\n📦 [BOXES] Total: {Box.objects.count()}")
print(f"   • Disponibles: {Box.objects.filter(estado='DISPONIBLE').count()}")
print(f"   • Ocupados: {Box.objects.filter(estado='OCUPADO').count()}")
print(f"   • En mantenimiento: {Box.objects.filter(estado='MANTENIMIENTO').count()}")

print(f"\n👨‍⚕️ [MÉDICOS] Total: {User.objects.filter(rol='MEDICO').count()}")
print(f"   • Activos: {User.objects.filter(rol='MEDICO', is_active=True).count()}")

print(f"\n👥 [PACIENTES] Total: {Paciente.objects.count()}")
print(f"   ✅ TODOS con activo=True: {Paciente.objects.filter(activo=True).count()}")
print(f"   • Estado EN_ESPERA: {Paciente.objects.filter(estado_actual='EN_ESPERA').count()}")
print(f"   • Estado ACTIVO: {Paciente.objects.filter(estado_actual='ACTIVO').count()}")
print(f"   • Estado PROCESO_PAUSADO: {Paciente.objects.filter(estado_actual='PROCESO_PAUSADO').count()}")
print(f"   • Con etapa asignada: {Paciente.objects.exclude(etapa_actual=None).count()}")

print(f"\n🗺️ [RUTAS CLÍNICAS] Total: {RutaClinica.objects.count()}")
print(f"   • Iniciadas: {RutaClinica.objects.filter(estado='INICIADA').count()}")
print(f"   • En Progreso: {RutaClinica.objects.filter(estado='EN_PROGRESO').count()}")
print(f"   • Pausadas: {RutaClinica.objects.filter(estado='PAUSADA').count()}")
print(f"   • Completadas: {RutaClinica.objects.filter(estado='COMPLETADA').count()}")
print(f"   • Canceladas: {RutaClinica.objects.filter(estado='CANCELADA').count()}")

print("\n   [DISTRIBUCIÓN POR ETAPA]")
for etapa_key, etapa_label in RutaClinica.ETAPAS_CHOICES:
    count = RutaClinica.objects.filter(etapa_actual=etapa_key).count()
    if count > 0:
        print(f"      • {etapa_label}: {count} pacientes")

print(f"\n📋 [ATENCIONES] Total: {Atencion.objects.count()}")
print(f"   • Programadas: {Atencion.objects.filter(estado='PROGRAMADA').count()}")
print(f"   • En Espera: {Atencion.objects.filter(estado='EN_ESPERA').count()}")
print(f"   • En Curso: {Atencion.objects.filter(estado='EN_CURSO').count()}")
print(f"   • Completadas: {Atencion.objects.filter(estado='COMPLETADA').count()}")
print(f"   • Canceladas: {Atencion.objects.filter(estado='CANCELADA').count()}")
print(f"   • No Presentado: {Atencion.objects.filter(estado='NO_PRESENTADO').count()}")

print("\n" + "=" * 80)
print(" SCRIPT COMPLETADO EXITOSAMENTE")
print("=" * 80)
print("\n📝 Datos generados:")
print(f"   • {len(boxes_creados)} boxes disponibles")
print(f"   • {len(pacientes_creados)} pacientes diversos (TODOS activo=True)")
print(f"   • {len(rutas_creadas)} rutas clínicas en diferentes etapas")
print(f"   • {len(atenciones_creadas)} atenciones en Noviembre 2025")
