import os
import shutil
from pathlib import Path

# Ubicación base
BASE_DIR = Path(__file__).resolve().parent

def resetear_migraciones():
    print("\n🧹 1. ELIMINANDO MIGRACIONES CORRUPTAS...")
    
    # Buscar carpetas 'migrations' en todas las apps
    count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        if 'migrations' in dirs:
            migrations_path = Path(root) / 'migrations'
            # Eliminar todos los .py excepto __init__.py
            for file in migrations_path.glob('*.py'):
                if file.name != '__init__.py':
                    file.unlink()
                    print(f"   -> Eliminado: {file.parent.name}/{file.name}")
                    count += 1
    
    print(f"✅ {count} archivos eliminados.")

def crear_nuevas_migraciones():
    print("\n🔨 2. GENERANDO MIGRACIONES LIMPIAS...")
    # Ejecutar makemigrations
    ret = os.system("python manage.py makemigrations")
    if ret == 0:
        print("✅ Nuevos archivos de migración creados exitosamente.")
    else:
        print("❌ Error al ejecutar makemigrations.")

if __name__ == "__main__":
    resetear_migraciones()
    crear_nuevas_migraciones()
    print("\n✨ LISTO. Ahora la estructura del código es coherente.")