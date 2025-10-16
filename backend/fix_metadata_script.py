# backend/fix_metadatos.py
# Script para corregir metadatos_adicionales que sean listas
# Ejecutar con: python manage.py shell < fix_metadatos.py

from pacientes.models import Paciente

print("\n" + "="*60)
print("CORRIGIENDO METADATOS_ADICIONALES EN PACIENTES")
print("="*60 + "\n")

pacientes = Paciente.objects.all()
total = pacientes.count()
corregidos = 0

for paciente in pacientes:
    # Si metadatos_adicionales es una lista, convertir a dict
    if isinstance(paciente.metadatos_adicionales, list):
        print(f"❌ Paciente {paciente.identificador_hash[:8]} tiene metadatos como LISTA")
        
        # Convertir a dict vacío
        paciente.metadatos_adicionales = {}
        
        # Si necesitas migrar datos de la lista al dict, hazlo aquí
        # Por ejemplo:
        # if old_list:
        #     paciente.metadatos_adicionales = {'datos': old_list}
        
        paciente.save()
        corregidos += 1
        print(f"✓ Corregido a DICT vacío\n")
    
    # Si es None, convertir a dict
    elif paciente.metadatos_adicionales is None:
        print(f"⚠️ Paciente {paciente.identificador_hash[:8]} tiene metadatos como None")
        paciente.metadatos_adicionales = {}
        paciente.save()
        corregidos += 1
        print(f"✓ Corregido a DICT vacío\n")
    
    # Si ya es dict, verificar
    elif isinstance(paciente.metadatos_adicionales, dict):
        print(f"✓ Paciente {paciente.identificador_hash[:8]} tiene metadatos correctos (DICT)")

print("="*60)
print(f"RESUMEN:")
print(f"Total de pacientes: {total}")
print(f"Pacientes corregidos: {corregidos}")
print(f"Pacientes correctos: {total - corregidos}")
print("="*60 + "\n")
