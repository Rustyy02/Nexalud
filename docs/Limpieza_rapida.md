# Ejecutar en el teminal

python manage.py shell


from boxes.models import Box, OcupacionManual
from pacientes.models import Paciente
from atenciones.models import Medico, Atencion
from rutas_clinicas.models import RutaClinica

# Eliminar en orden correcto
Atencion.objects.all().delete()
RutaClinica.objects.all().delete()
Paciente.objects.all().delete()
Medico.objects.all().delete()
OcupacionManual.objects.all().delete()
Box.objects.all().delete()

print("✅ Todos los datos han sido eliminados")
exit()

