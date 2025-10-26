# backend/pacientes/migrations/0002_mejoras_estado_y_etapa.py
# MIGRACIÓN PARA LOS NUEVOS CAMPOS

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0001_initial'),
    ]

    operations = [
        # Paso 1: Renombrar estado_actual a estado_sistema
        migrations.RenameField(
            model_name='paciente',
            old_name='estado_actual',
            new_name='estado_sistema',
        ),
        
        # Paso 2: Actualizar choices del campo estado_sistema
        migrations.AlterField(
            model_name='paciente',
            name='estado_sistema',
            field=models.CharField(
                choices=[
                    ('ACTIVO', 'Activo en el Sistema'),
                    ('PAUSADO', 'Proceso Pausado'),
                    ('INACTIVO', 'Inactivo'),
                    ('DADO_ALTA', 'Dado de Alta'),
                    ('DERIVADO', 'Derivado a Otro Centro'),
                    ('FALLECIDO', 'Fallecido'),
                ],
                default='ACTIVO',
                max_length=20,
                db_index=True,
                help_text='Estado administrativo del paciente en el sistema'
            ),
        ),
        
        # Paso 3: Agregar nuevo campo etapa_actual
        migrations.AddField(
            model_name='paciente',
            name='etapa_actual',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ADMISION', 'Admisión/Recepción'),
                    ('TRIAJE', 'Triaje'),
                    ('CONSULTA_MEDICA', 'Consulta Médica'),
                    ('PROCESO_EXAMEN', 'Proceso del Examen'),
                    ('REVISION_EXAMEN', 'Revisión del Examen'),
                    ('HOSPITALIZACION', 'Hospitalización'),
                    ('OPERACION', 'Operación'),
                    ('RECUPERACION', 'Recuperación'),
                    ('ALTA', 'Alta Médica'),
                ],
                max_length=30,
                null=True,
                db_index=True,
                help_text='Etapa clínica actual del paciente (vinculada a su ruta clínica)'
            ),
        ),
        
        # Paso 4: Agregar campo esta_pausado
        migrations.AddField(
            model_name='paciente',
            name='esta_pausado',
            field=models.BooleanField(
                default=False,
                help_text='Indica si el proceso del paciente está pausado'
            ),
        ),
        
        # Paso 5: Agregar campo motivo_pausa
        migrations.AddField(
            model_name='paciente',
            name='motivo_pausa',
            field=models.TextField(
                blank=True,
                help_text='Motivo por el cual se pausó el proceso'
            ),
        ),
        
        # Paso 6: Agregar campo fecha_pausa
        migrations.AddField(
            model_name='paciente',
            name='fecha_pausa',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Fecha y hora en que se pausó el proceso'
            ),
        ),
        
        # Paso 7: Actualizar índices
        migrations.AddIndex(
            model_name='paciente',
            index=models.Index(fields=['etapa_actual'], name='pacientes_etapa_a_idx'),
        ),
    ]
