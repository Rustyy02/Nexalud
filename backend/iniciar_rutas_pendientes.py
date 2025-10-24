#!/usr/bin/env python3
"""
🚀 Script para Iniciar Todas las Rutas Pendientes

Este script encuentra todas las rutas que están en estado INICIADA
pero no tienen etapa_actual (no han sido iniciadas correctamente)
y las inicia automáticamente.

Uso:
    python iniciar_rutas_pendientes.py

Ubicación: backend/
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
django.setup()

from rutas_clinicas.models import RutaClinica
from django.db import transaction


def iniciar_rutas_pendientes():
    """Inicia todas las rutas pendientes"""
    
    print("\n" + "="*70)
    print("🚀 INICIAR RUTAS CLÍNICAS PENDIENTES")
    print("="*70)
    
    # Buscar rutas sin iniciar
    rutas_pendientes = RutaClinica.objects.filter(
        estado='INICIADA',
        etapa_actual__isnull=True
    )
    
    total = rutas_pendientes.count()
    
    if total == 0:
        print("\n✅ No hay rutas pendientes de iniciar.")
        print("   Todas las rutas están correctamente iniciadas.")
        return
    
    print(f"\n📋 Se encontraron {total} ruta(s) pendiente(s) de iniciar:")
    
    for ruta in rutas_pendientes:
        print(f"\n   🔹 Ruta ID: {str(ruta.id)[:8]}...")
        print(f"      Paciente: {ruta.paciente.identificador_hash[:12]}")
        print(f"      Estado: {ruta.estado}")
        print(f"      Etapa actual: {ruta.etapa_actual}")
    
    # Confirmar
    print("\n" + "-"*70)
    respuesta = input(f"\n¿Iniciar estas {total} ruta(s)? (s/n): ").strip().lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("\n❌ Operación cancelada.")
        return
    
    # Iniciar rutas
    print("\n" + "="*70)
    print("⚙️  INICIANDO RUTAS...")
    print("="*70)
    
    exitosas = 0
    fallidas = 0
    
    for ruta in rutas_pendientes:
        try:
            with transaction.atomic():
                # Iniciar la ruta
                ruta.iniciar_ruta()
                
                print(f"\n✅ Ruta {str(ruta.id)[:8]}... iniciada correctamente")
                print(f"   Estado: {ruta.estado}")
                print(f"   Etapa actual: {ruta.etapa_actual}")
                print(f"   Progreso: {ruta.porcentaje_completado:.1f}%")
                
                exitosas += 1
                
        except Exception as e:
            print(f"\n❌ Error al iniciar ruta {str(ruta.id)[:8]}...")
            print(f"   Error: {str(e)}")
            fallidas += 1
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    print(f"✅ Exitosas: {exitosas}")
    print(f"❌ Fallidas: {fallidas}")
    print(f"📋 Total: {total}")
    
    if exitosas > 0:
        print(f"\n🎉 ¡{exitosas} ruta(s) iniciada(s) correctamente!")
        print("\n💡 Ahora recarga la página en el navegador para ver los cambios.")
    
    print("="*70 + "\n")


def verificar_rutas_actuales():
    """Verifica el estado actual de todas las rutas"""
    
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN DE RUTAS ACTUALES")
    print("="*70)
    
    todas_rutas = RutaClinica.objects.all()
    
    if not todas_rutas.exists():
        print("\n⚠️  No hay rutas en la base de datos.")
        return
    
    iniciadas_ok = 0
    pendientes = 0
    en_progreso = 0
    completadas = 0
    
    print("\n📊 Estado de las rutas:")
    
    for ruta in todas_rutas:
        print(f"\n🔹 Ruta {str(ruta.id)[:8]}...")
        print(f"   Estado: {ruta.estado}")
        print(f"   Etapa actual: {ruta.etapa_actual or 'N/A'}")
        print(f"   Progreso: {ruta.porcentaje_completado:.1f}%")
        
        if ruta.estado == 'INICIADA' and not ruta.etapa_actual:
            print("   ⚠️  NECESITA SER INICIADA")
            pendientes += 1
        elif ruta.estado == 'EN_PROGRESO':
            print("   ✅ EN PROGRESO")
            en_progreso += 1
        elif ruta.estado == 'COMPLETADA':
            print("   ✓  COMPLETADA")
            completadas += 1
        else:
            print("   ℹ️  INICIADA CORRECTAMENTE")
            iniciadas_ok += 1
    
    # Resumen
    print("\n" + "-"*70)
    print("📈 Resumen:")
    print(f"   Total rutas: {todas_rutas.count()}")
    print(f"   En progreso: {en_progreso}")
    print(f"   Completadas: {completadas}")
    print(f"   Iniciadas OK: {iniciadas_ok}")
    print(f"   ⚠️  Pendientes de iniciar: {pendientes}")
    print("="*70 + "\n")
    
    return pendientes > 0


def main():
    """Función principal"""
    
    try:
        # Verificar estado actual
        tiene_pendientes = verificar_rutas_actuales()
        
        if tiene_pendientes:
            # Iniciar rutas pendientes
            iniciar_rutas_pendientes()
        else:
            print("✅ No hay acciones necesarias.\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario.\n")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
