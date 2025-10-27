# backend/pacientes/migrations/0002_agregar_etapa_actual.py
# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0001_initial'),
    ]

    operations = [
        # Modificar ESTADO_CHOICES
        migrations.AlterField(
            model_name='paciente',
            name='estado_actual',
            field=models.CharField(
                choices=[
                    ('EN_ESPERA', 'En Espera'),
                    ('ACTIVO', 'Activo'),
                    ('PROCESO_PAUSADO', 'Proceso Pausado'),
                    ('ALTA_COMPLETA', 'Alta Completa'),
                    ('ALTA_MEDICA', 'Alta Médica'),
                    ('PROCESO_INCOMPLETO', 'Proceso Incompleto'),
                    ('INACTIVO', 'Inactivo'),
                ],
                default='EN_ESPERA',
                help_text='Estado general del paciente en el sistema',
                max_length=20
            ),
        ),
        
        # Agregar campo etapa_actual
        migrations.AddField(
            model_name='paciente',
            name='etapa_actual',
            field=models.CharField(
                blank=True,
                choices=[
                    ('CONSULTA_MEDICA', 'Consulta Médica'),
                    ('PROCESO_EXAMEN', 'Proceso del Examen'),
                    ('REVISION_EXAMEN', 'Revisión del Examen'),
                    ('HOSPITALIZACION', 'Hospitalización'),
                    ('OPERACION', 'Operación'),
                    ('ALTA', 'Alta Médica'),
                ],
                help_text='Etapa actual del flujo clínico (sincronizada con RutaClinica)',
                max_length=30,
                null=True
            ),
        ),
        
        # Agregar índice para etapa_actual
        migrations.AddIndex(
            model_name='paciente',
            index=models.Index(fields=['etapa_actual'], name='pacientes_etapa_a_idx'),
        ),
    ]
