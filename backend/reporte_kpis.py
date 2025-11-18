import os
import django
from django.db.models import Avg, Count, F
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from atenciones.models import Atencion
from boxes.models import Box
from rutas_clinicas.models import RutaClinica

def generar_reporte():
    print("\n============================================")
    print(f"📊 REPORTE DE KPIs NEXALUD - {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    print("============================================\n")

    # 1. VOLUMEN DE ATENCIÓN
    total_atenciones = Atencion.objects.count()
    completadas = Atencion.objects.filter(estado='COMPLETADA').count()
    tasa_completitud = (completadas / total_atenciones * 100) if total_atenciones > 0 else 0
    
    print(f"1️⃣  VOLUMEN DE OPERACIÓN")
    print(f"    • Total Citas Agendadas: {total_atenciones}")
    print(f"    • Citas Completadas con Éxito: {completadas}")
    print(f"    • Tasa de Cumplimiento: {tasa_completitud:.1f}%")

    # 2. TIEMPOS DE ESPERA (KPI CRÍTICO)
    # Calculamos diferencia entre Hora Programada y Hora Real de Inicio
    atenciones_con_tiempos = Atencion.objects.filter(
        estado='COMPLETADA', 
        inicio_cronometro__isnull=False
    ).annotate(
        espera=F('inicio_cronometro') - F('fecha_hora_inicio')
    )
    
    if atenciones_con_tiempos.exists():
        promedio_espera = sum([a.espera.total_seconds() for a in atenciones_con_tiempos], 0) / atenciones_con_tiempos.count()
        promedio_minutos = promedio_espera / 60
    else:
        promedio_minutos = 0

    print(f"\n2️⃣  TIEMPOS DE ESPERA (KPI Proyecto)")
    print(f"    • Tiempo Promedio de Espera Real: {promedio_minutos:.1f} minutos")
    if promedio_minutos < 15:
        print("      ✅ OBJETIVO CUMPLIDO (< 15 min)")
    else:
        print("      ⚠️ ALERTA: Espera elevada")

    # 3. DURACIÓN DE ATENCIÓN
    duracion_promedio = Atencion.objects.filter(estado='COMPLETADA').aggregate(Avg('duracion_real'))['duracion_real__avg'] or 0
    
    print(f"\n3️⃣  EFICIENCIA MÉDICA")
    print(f"    • Duración Promedio de Consulta: {duracion_promedio:.1f} minutos")

    # 4. USO DE BOXES
    boxes_total = Box.objects.count()
    boxes_ocupados = Box.objects.filter(estado='OCUPADO').count()
    ocupacion_actual = (boxes_ocupados / boxes_total * 100) if boxes_total > 0 else 0
    
    print(f"\n4️⃣  INFRAESTRUCTURA (Tiempo Real)")
    print(f"    • Ocupación Actual de Boxes: {ocupacion_actual:.1f}% ({boxes_ocupados}/{boxes_total})")

    print("\n============================================")

if __name__ == '__main__':
    generar_reporte()