import os
import json
import django
import random
from faker import Faker
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

# Configuración del entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from pacientes.models import Paciente
from atenciones.models import Atencion
from boxes.models import Box
from rutas_clinicas.models import RutaClinica
from rest_framework.authtoken.models import Token

fake = Faker('es_CL')

def formatear_rut_chileno(rut_raw):
    """Formatea RUT como XX.XXX.XXX-X"""
    rut_limpio = rut_raw.replace('.', '').replace('-', '').upper()
    if len(rut_limpio) < 2: return rut_raw
    cuerpo, dv = rut_limpio[:-1], rut_limpio[-1]
    try:
        cuerpo_fmt = "{:,}".format(int(cuerpo)).replace(",", ".")
    except ValueError: return rut_raw
    return f"{cuerpo_fmt}-{dv}"

def limpiar_datos():
    print("\n🧹 LIMPIEZA COMPLETA ----------------")
    try:
        with transaction.atomic():
            RutaClinica.objects.all().delete()
            Atencion.objects.all().delete()
            Paciente.objects.all().delete()
            Token.objects.all().delete()
            User.objects.filter(username__startswith='medico_').delete()
            User.objects.filter(username__startswith='secretaria_').delete()
            Box.objects.update(estado='DISPONIBLE')
        print("✅ Base de datos limpia.")
    except Exception as e:
        print(f"⚠️ Error limpiando: {e}")

def crear_infraestructura_y_personal(num_medicos, num_secretarias):
    print("\n🏗️  INFRAESTRUCTURA Y PERSONAL -------")
    boxes = []
    # Creamos más boxes para soportar el flujo de varias etapas
    for i in range(20): 
        b, _ = Box.objects.get_or_create(nombre=f"Box {i+1}", defaults={'estado': 'DISPONIBLE', 'numero': i+1})
        boxes.append(b)

    medicos = []
    token_map = {}
    
    with transaction.atomic():
        for i in range(num_medicos):
            username = f"medico_{i}"
            email = f"medico{i}@nexalud.medico.com"
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(username, email, 'password123', 
                                           first_name=fake.first_name(), last_name=fake.last_name(), 
                                           rol='MEDICO', especialidad='MEDICINA_GENERAL')
                u.full_clean(); u.save()
            else:
                u = User.objects.get(username=username)
            
            t, _ = Token.objects.get_or_create(user=u)
            token_map[username] = t.key
            medicos.append(u)
            
        # Admin
        if not User.objects.filter(username='admin').exists():
            adm = User.objects.create_superuser('admin', 'admin@nexalud.admin.com', 'password123')
            t, _ = Token.objects.get_or_create(user=adm)
            token_map['admin'] = t.key

    with open('tokens.json', 'w') as f:
        json.dump(token_map, f)
    
    print(f"   -> {len(medicos)} Médicos listos.")
    return medicos, boxes

def generar_paciente_y_ruta(estado_inicial='CONSULTA_MEDICA'):
    """
    Crea un paciente y una ruta clínica COMPLETA con pasos intermedios.
    """
    rut_fmt = formatear_rut_chileno(fake.unique.rut())
    p = Paciente(
        rut=rut_fmt,
        nombre=fake.first_name(),
        apellido_paterno=fake.last_name(),
        apellido_materno=fake.last_name(),
        fecha_nacimiento=fake.date_of_birth(minimum_age=5, maximum_age=90),
        estado_actual='EN_ESPERA',
        genero=random.choice(['M', 'F']),
        direccion_region='RM',
        direccion_codigo_postal=fake.postcode()[:10],
        correo=fake.email()
    )
    p.full_clean(); p.save()
    
    # --- CORRECCIÓN CLAVE: Ruta más larga ---
    etapas_full = ['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'REVISION_EXAMEN', 'ALTA']
    
    ruta = RutaClinica.objects.create(
        paciente=p,
        etapas_seleccionadas=etapas_full, # Ahora tiene pasos intermedios
        etapa_actual=estado_inicial,
        estado='INICIADA'
    )
    
    # Si pedimos iniciar en una etapa avanzada (para historial), 
    # debemos marcar las anteriores como completadas
    try:
        idx_objetivo = etapas_full.index(estado_inicial)
        ruta.indice_etapa_actual = idx_objetivo
        ruta.etapas_completadas = etapas_full[:idx_objetivo]
    except ValueError: pass
    
    ruta.iniciar_ruta(etapa_inicial=estado_inicial) # Usa el método del modelo para timestamps
    return p, ruta

def generar_historial(medicos, boxes, dias_atras=7, atenciones_por_dia=40):
    print(f"\n📜 GENERANDO HISTORIAL ({dias_atras} días) --")
    
    # Para el historial, creamos rutas que ya terminaron o están avanzadas
    estados_finales = ['COMPLETADA', 'COMPLETADA', 'COMPLETADA', 'CANCELADA']
    count = 0
    
    with transaction.atomic():
        for d in range(1, dias_atras + 1):
            fecha_base = timezone.now() - timedelta(days=d)
            
            for _ in range(atenciones_por_dia):
                try:
                    # Historial: Variedad de etapas
                    etapa_random = random.choice(['CONSULTA_MEDICA', 'PROCESO_EXAMEN', 'ALTA'])
                    p, ruta = generar_paciente_y_ruta(estado_inicial=etapa_random)
                    
                    estado_simulado = random.choice(estados_finales)
                    hora_inicio = fecha_base.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
                    
                    Atencion.objects.create(
                        paciente=p,
                        medico=random.choice(medicos),
                        box=random.choice(boxes),
                        estado=estado_simulado,
                        fecha_hora_inicio=hora_inicio,
                        duracion_planificada=30,
                        inicio_cronometro=hora_inicio if estado_simulado == 'COMPLETADA' else None,
                        fin_cronometro=hora_inicio + timedelta(minutes=30) if estado_simulado == 'COMPLETADA' else None,
                        duracion_real=30 if estado_simulado == 'COMPLETADA' else None
                    )
                    
                    if estado_simulado == 'COMPLETADA':
                        ruta.estado = 'COMPLETADA'
                        ruta.porcentaje_completado = 100.0
                        p.estado_actual = 'ALTA_COMPLETA'
                    else:
                        ruta.estado = 'CANCELADA'
                        p.estado_actual = 'PROCESO_CANCELADO'
                    
                    p.save(); ruta.save()
                    count += 1
                except Exception: pass
    print(f"✅ Historial generado: {count} registros históricos.")

def generar_carga_futura_gradual(medicos, boxes, num_pacientes=300):
    print("\n🔮 GENERANDO AGENDA FUTURA (Con Etapas) ----")
    count = 0
    with transaction.atomic():
        for i in range(num_pacientes):
            try:
                # Creamos pacientes iniciando su ruta desde cero
                p, ruta = generar_paciente_y_ruta(estado_inicial='CONSULTA_MEDICA')
                
                # Distribución temporal: 4 horas
                minutos_futuros = random.randint(2, 240)
                inicio = timezone.now() + timedelta(minutes=minutos_futuros)
                
                Atencion.objects.create(
                    paciente=p,
                    medico=random.choice(medicos),
                    box=random.choice(boxes),
                    estado='PROGRAMADA',
                    fecha_hora_inicio=inicio,
                    duracion_planificada=30
                )
                count += 1
            except Exception: pass
            
    print(f"✅ Agenda lista: {count} citas programadas (Rutas de 4 etapas).")

if __name__ == '__main__':
    limpiar_datos()
    medicos, boxes = crear_infraestructura_y_personal(num_medicos=50, num_secretarias=5)
    generar_historial(medicos, boxes, dias_atras=7, atenciones_por_dia=40)
    generar_carga_futura_gradual(medicos, boxes, num_pacientes=300)
    print("\n✨ LISTO PARA LOCUST.")