# backend/fix_peso_pacientes.py
from pacientes.models import Paciente

# Buscar pacientes con peso inválido
pacientes_con_error = Paciente.objects.all()

for p in pacientes_con_error:
    try:
        # Intentar acceder al peso
        if p.peso is not None:
            float(p.peso)
    except (ValueError, TypeError):
        print(f"❌ Paciente {p.id} tiene peso inválido: {p.peso}")
        p.peso = None  # Establecer a NULL
        p.save()
        print(f"✅ Corregido")