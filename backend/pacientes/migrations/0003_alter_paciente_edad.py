# backend/pacientes/migrations/0003_alter_paciente_edad.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0002_alter_paciente_apellido_materno_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paciente',
            name='edad',
            field=models.PositiveIntegerField(
                default=0,
                editable=False,
                help_text='Edad calculada automáticamente desde fecha de nacimiento'
            ),
        ),
    ]