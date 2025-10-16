# backend/pacientes/migrations/0002_add_medical_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paciente',
            name='tipo_sangre',
            field=models.CharField(
                choices=[
                    ('A+', 'A Positivo'), ('A-', 'A Negativo'),
                    ('B+', 'B Positivo'), ('B-', 'B Negativo'),
                    ('AB+', 'AB Positivo'), ('AB-', 'AB Negativo'),
                    ('O+', 'O Positivo'), ('O-', 'O Negativo'),
                    ('DESCONOCIDO', 'Desconocido')
                ],
                default='DESCONOCIDO',
                help_text='Tipo de sangre del paciente',
                max_length=15
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='peso',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Peso en kilogramos',
                max_digits=5,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='altura',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Altura en centímetros',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='alergias',
            field=models.TextField(
                blank=True,
                help_text='Alergias conocidas del paciente'
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='condiciones_preexistentes',
            field=models.TextField(
                blank=True,
                help_text='Condiciones médicas preexistentes'
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='medicamentos_actuales',
            field=models.TextField(
                blank=True,
                help_text='Medicamentos que toma actualmente'
            ),
        ),
        migrations.AddIndex(
            model_name='paciente',
            index=models.Index(fields=['nivel_urgencia'], name='pacientes_nivel_u_idx'),
        ),
    ]
