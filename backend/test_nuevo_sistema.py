# backend/test_nuevo_sistema.py
"""
Script de testing para verificar el funcionamiento del nuevo sistema
de estados y rutas clínicas automáticas.

Uso:
    python manage.py shell < test_nuevo_sistema.py
"""

from pacientes.models import Paciente
from rutas_clinicas.models import RutaClinica
from datetime import date
from decimal import Decimal
from django.utils import timezone

print("\n" + "="*70)
print("🧪 INICIANDO TESTS DEL NUEVO SISTEMA")
print("="*70 + "\n")

# ============================================
# TEST 1: Creación Automática de Ruta
# ============================================

print("📋 TEST 1: Creación Automática de Ruta Clínica")
print("-" * 70)

# Crear un paciente de prueba
paciente_test = Paciente.objects.create(
    rut='11.111.111-1',
    nombre='Test',
    apellido_paterno='Automático',
    apellido_materno='Sistema',
    fecha_nacimiento=date(1990, 1, 1),
    genero='M',
    telefono='+56911111111',
    correo='test@sistema.cl',
    direccion_calle='Calle Test 123',
    direccion_comuna='Test',
    direccion_ciudad='Test',
    direccion_region='V',
    seguro_medico='FONASA_B',
    tipo_sangre='O+',
    peso=Decimal('75.5'),
    altura=175,
    nivel_urgencia='MEDIA',
)

print(f"✅ Paciente creado: {paciente_test.nombre_completo}")
print(f"   ID: {paciente_test.id}")
print(f"   Estado Sistema: {paciente_test.estado_sistema} ({paciente_test.get_estado_sistema_display()})")
print(f"   Etapa Actual: {paciente_test.etapa_actual} ({paciente_test.get_etapa_actual_display()})")

# Verificar que se creó la ruta automáticamente
rutas = RutaClinica.objects.filter(paciente=paciente_test)
print(f"\n🔍 Rutas creadas automáticamente: {rutas.count()}")

if rutas.exists():
    ruta = rutas.first()
    print(f"✅ Ruta creada automáticamente")
    print(f"   ID: {ruta.id}")
    print(f"   Estado: {ruta.estado} ({ruta.get_estado_display()})")
    print(f"   Etapa Actual: {ruta.etapa_actual} ({ruta.get_etapa_actual_display()})")
    print(f"   Progreso: {ruta.porcentaje_completado:.2f}%")
    print(f"   Total Etapas: {len(ruta.etapas_seleccionadas)}")
else:
    print("❌ ERROR: No se creó la ruta automáticamente")

print("\n✅ TEST 1 COMPLETADO\n")

# ============================================
# TEST 2: Sincronización Paciente ↔ Ruta
# ============================================

print("📋 TEST 2: Sincronización Paciente ↔ Ruta")
print("-" * 70)

print(f"Estado inicial:")
print(f"  Paciente - Etapa: {paciente_test.etapa_actual}")
print(f"  Ruta - Etapa: {ruta.etapa_actual}")
print(f"  ¿Sincronizados? {'✅ SÍ' if paciente_test.etapa_actual == ruta.etapa_actual else '❌ NO'}")

# Avanzar la ruta
print(f"\n🔄 Avanzando a la siguiente etapa...")
resultado = ruta.avanzar_etapa(
    observaciones="Test de avance automático",
    usuario=None
)

if resultado:
    # Refrescar el paciente desde la BD
    paciente_test.refresh_from_db()
    ruta.refresh_from_db()
    
    print(f"✅ Etapa avanzada correctamente")
    print(f"\nEstado después del avance:")
    print(f"  Paciente - Etapa: {paciente_test.etapa_actual} ({paciente_test.get_etapa_actual_display()})")
    print(f"  Ruta - Etapa: {ruta.etapa_actual} ({ruta.get_etapa_actual_display()})")
    print(f"  ¿Sincronizados? {'✅ SÍ' if paciente_test.etapa_actual == ruta.etapa_actual else '❌ NO'}")
    print(f"  Progreso: {ruta.porcentaje_completado:.2f}%")
else:
    print("❌ ERROR: No se pudo avanzar la etapa")

print("\n✅ TEST 2 COMPLETADO\n")

# ============================================
# TEST 3: Sistema de Pausa
# ============================================

print("📋 TEST 3: Sistema de Pausa")
print("-" * 70)

print(f"Estado antes de pausar:")
print(f"  Paciente - Estado Sistema: {paciente_test.estado_sistema}")
print(f"  Paciente - Está Pausado: {paciente_test.esta_pausado}")
print(f"  Ruta - Estado: {ruta.estado}")
print(f"  Ruta - Está Pausado: {ruta.esta_pausado}")

# Pausar el proceso
print(f"\n⏸  Pausando el proceso...")
ruta.pausar_ruta(
    motivo="Test de pausa del sistema",
    usuario=None
)

# Refrescar desde BD
paciente_test.refresh_from_db()
ruta.refresh_from_db()

print(f"✅ Proceso pausado")
print(f"\nEstado después de pausar:")
print(f"  Paciente - Estado Sistema: {paciente_test.estado_sistema} ({paciente_test.get_estado_sistema_display()})")
print(f"  Paciente - Está Pausado: {paciente_test.esta_pausado}")
print(f"  Paciente - Motivo: {paciente_test.motivo_pausa}")
print(f"  Ruta - Estado: {ruta.estado} ({ruta.get_estado_display()})")
print(f"  Ruta - Está Pausado: {ruta.esta_pausado}")
print(f"  Ruta - Motivo: {ruta.motivo_pausa}")

# Reanudar el proceso
print(f"\n▶  Reanudando el proceso...")
resultado_reanudar = ruta.reanudar_ruta(usuario=None)

if resultado_reanudar:
    # Refrescar desde BD
    paciente_test.refresh_from_db()
    ruta.refresh_from_db()
    
    print(f"✅ Proceso reanudado correctamente")
    print(f"\nEstado después de reanudar:")
    print(f"  Paciente - Estado Sistema: {paciente_test.estado_sistema} ({paciente_test.get_estado_sistema_display()})")
    print(f"  Paciente - Está Pausado: {paciente_test.esta_pausado}")
    print(f"  Ruta - Estado: {ruta.estado} ({ruta.get_estado_display()})")
    print(f"  Ruta - Está Pausado: {ruta.esta_pausado}")
else:
    print("❌ ERROR: No se pudo reanudar el proceso")

print("\n✅ TEST 3 COMPLETADO\n")

# ============================================
# TEST 4: Timeline Completo
# ============================================

print("📋 TEST 4: Timeline Completo")
print("-" * 70)

timeline = ruta.obtener_timeline_completo()
print(f"Total de etapas en el timeline: {len(timeline)}")
print(f"\nDetalle de etapas:\n")

for etapa in timeline:
    icono = "✅" if etapa['estado'] == 'COMPLETADA' else "🔵" if etapa['es_actual'] else "⚪"
    print(f"{icono} {etapa['orden']}. {etapa['etapa_label']}")
    print(f"   Estado: {etapa['estado']}")
    print(f"   Es Actual: {etapa['es_actual']}")
    print(f"   Es Requerida: {etapa['es_requerida']}")
    if etapa['fecha_inicio']:
        print(f"   Inicio: {etapa['fecha_inicio']}")
    if etapa['fecha_fin']:
        print(f"   Fin: {etapa['fecha_fin']}")
    print()

print("✅ TEST 4 COMPLETADO\n")

# ============================================
# TEST 5: Historial de Cambios
# ============================================

print("📋 TEST 5: Historial de Cambios")
print("-" * 70)

historial = ruta.historial_cambios
print(f"Total de cambios registrados: {len(historial)}")
print(f"\nDetalle de cambios:\n")

for i, cambio in enumerate(historial, 1):
    print(f"#{i} - {cambio['accion']}")
    print(f"   Timestamp: {cambio['timestamp']}")
    print(f"   Usuario: {cambio['usuario']}")
    if 'etapa' in cambio:
        print(f"   Etapa: {cambio['etapa']}")
    if 'desde' in cambio and 'hacia' in cambio:
        print(f"   Transición: {cambio['desde']} → {cambio['hacia']}")
    if 'motivo' in cambio:
        print(f"   Motivo: {cambio['motivo']}")
    print()

print("✅ TEST 5 COMPLETADO\n")

# ============================================
# RESUMEN FINAL
# ============================================

print("="*70)
print("📊 RESUMEN FINAL")
print("="*70)

print(f"\n✅ Paciente de Test:")
print(f"   Nombre: {paciente_test.nombre_completo}")
print(f"   Estado Sistema: {paciente_test.get_estado_sistema_display()}")
print(f"   Etapa Actual: {paciente_test.get_etapa_actual_display()}")
print(f"   Está Pausado: {paciente_test.esta_pausado}")

print(f"\n✅ Ruta Clínica:")
print(f"   Estado: {ruta.get_estado_display()}")
print(f"   Progreso: {ruta.porcentaje_completado:.2f}%")
print(f"   Etapas Completadas: {len(ruta.etapas_completadas)}/{len(ruta.etapas_seleccionadas)}")
print(f"   Tiempo Transcurrido: {ruta.obtener_tiempo_total_real()}")

print(f"\n✅ Verificación de Sincronización:")
if paciente_test.etapa_actual == ruta.etapa_actual:
    print(f"   ✅ Paciente y Ruta están SINCRONIZADOS")
else:
    print(f"   ❌ ERROR: Paciente y Ruta NO están sincronizados")
    print(f"      Paciente: {paciente_test.etapa_actual}")
    print(f"      Ruta: {ruta.etapa_actual}")

print("\n" + "="*70)
print("🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
print("="*70 + "\n")

print("🧹 Limpieza (opcional):")
print(f"   Para eliminar el paciente de prueba, ejecuta:")
print(f"   >>> Paciente.objects.get(rut='11.111.111-1').delete()")
print()
