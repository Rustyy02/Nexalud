# backend/rutas_clinicas/migrations/0005_mejorar_rutaclinica.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rutas_clinicas', '0004_alter_rutaclinica_etapa_actual'),
    ]

    operations = [
        # Agregar campo de historial de cambios
        migrations.AddField(
            model_name='rutaclinica',
            name='historial_cambios',
            field=models.JSONField(
                default=list,
                help_text='Registro de todos los cambios de etapa'
            ),
        ),
    ]
