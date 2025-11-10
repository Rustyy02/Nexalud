"""
Script para verificar atenciones en la base de datos
Ejecutar con: python manage.py shell < verificar_atenciones.py
"""

from atenciones.models import Atencion
from users.models import User
from django.utils import timezone

print("\n" + "="*60)
print("VERIFICACIÓN DE ATENCIONES")
print("="*60)

# Listar todos los médicos
print("\n📋 MÉDICOS DISPONIBLES:")
medicos = User.objects.filter(rol='MEDICO')
print(f"Total de médicos: {medicos.count()}")
for medico in medicos:
    print(f"  - {medico.username} ({medico.get_full_name()}) - ID: {medico.id}")

# Listar todas las atenciones
print("\n📅 ATENCIONES REGISTRADAS:")
atenciones = Atencion.objects.all().select_related('paciente', 'medico', 'box')
print(f"Total de atenciones: {atenciones.count()}")

if atenciones.exists():
    for atencion in atenciones:
        print(f"\n  📌 Atención #{str(atencion.id)[:8]}")
        print(f"     Paciente: {atencion.paciente.identificador_hash[:12]}")
        print(f"     Médico: {atencion.medico.username} ({atencion.medico.get_full_name()})")
        print(f"     Box: {atencion.box.numero}")
        print(f"     Fecha: {atencion.fecha_hora_inicio}")
        print(f"     Duración: {atencion.duracion_planificada} min")
        print(f"     Estado: {atencion.get_estado_display()}")
        print(f"     Tipo: {atencion.get_tipo_atencion_display()}")
else:
    print("  ⚠️ No hay atenciones registradas")

# Atenciones de hoy
print("\n📆 ATENCIONES DE HOY:")
hoy = timezone.now().date()
atenciones_hoy = Atencion.objects.filter(fecha_hora_inicio__date=hoy)
print(f"Total hoy: {atenciones_hoy.count()}")

# Atenciones por médico
print("\n👨‍⚕️ ATENCIONES POR MÉDICO:")
for medico in medicos:
    count = Atencion.objects.filter(medico=medico).count()
    hoy_count = Atencion.objects.filter(medico=medico, fecha_hora_inicio__date=hoy).count()
    print(f"  - {medico.username}: {count} total ({hoy_count} hoy)")

print("\n" + "="*60)
print("FIN DE VERIFICACIÓN")
print("="*60 + "\n")
