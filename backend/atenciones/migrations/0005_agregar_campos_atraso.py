# backend/atenciones/migrations/0005_agregar_campos_atraso.py
# Migración para agregar campos de control de atrasos

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atenciones', '0002_alter_atencion_medico'),
    ]

    operations = [
        migrations.AddField(
            model_name='atencion',
            name='atraso_reportado',
            field=models.BooleanField(
                default=False,
                help_text='Indica si el médico reportó un atraso del paciente'
            ),
        ),
        migrations.AddField(
            model_name='atencion',
            name='fecha_reporte_atraso',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Momento en que se reportó el atraso'
            ),
        ),
        migrations.AddField(
            model_name='atencion',
            name='motivo_atraso',
            field=models.TextField(
                blank=True,
                help_text='Motivo del atraso reportado por el médico'
            ),
        ),
    ]