# backend/pacientes/migrations/0003_migrar_estados_existentes.py
# MIGRACIÓN DE DATOS: Convierte estados antiguos al nuevo formato

from django.db import migrations


def migrar_estados_a_nuevo_formato(apps, schema_editor):
    """
    Migra los estados antiguos al nuevo formato separado.
    """
    Paciente = apps.get_model('pacientes', 'Paciente')
    
    # Mapeo de estados antiguos a nuevos
    mapeo_estados = {
        'EN_ESPERA': ('ACTIVO', 'ADMISION'),
        'EN_CONSULTA': ('ACTIVO', 'CONSULTA_MEDICA'),
        'EN_EXAMEN': ('ACTIVO', 'PROCESO_EXAMEN'),
        'PROCESO_PAUSADO': ('PAUSADO', None),
        'ALTA_COMPLETA': ('DADO_ALTA', 'ALTA'),
        'PROCESO_INCOMPLETO': ('INACTIVO', None),
    }
    
    for paciente in Paciente.objects.all():
        # Obtener el estado antiguo del metadatos si existe
        estado_antiguo = paciente.metadatos_adicionales.get('estado_actual_antiguo')
        
        if not estado_antiguo:
            # Si no hay estado antiguo guardado, intentar inferirlo del estado_sistema actual
            estado_antiguo = paciente.estado_sistema
        
        # Aplicar el mapeo
        if estado_antiguo in mapeo_estados:
            nuevo_estado_sistema, nueva_etapa = mapeo_estados[estado_antiguo]
            paciente.estado_sistema = nuevo_estado_sistema
            paciente.etapa_actual = nueva_etapa
            
            # Actualizar esta_pausado si corresponde
            if nuevo_estado_sistema == 'PAUSADO':
                paciente.esta_pausado = True
                if not paciente.motivo_pausa:
                    paciente.motivo_pausa = 'Migrado desde estado antiguo'
            
            # Guardar en metadatos el estado original para referencia
            if not isinstance(paciente.metadatos_adicionales, dict):
                paciente.metadatos_adicionales = {}
            paciente.metadatos_adicionales['estado_original'] = estado_antiguo
            paciente.metadatos_adicionales['migrado'] = True
            
            paciente.save()


def revertir_migracion(apps, schema_editor):
    """
    Revierte la migración de estados (opcional)
    """
    Paciente = apps.get_model('pacientes', 'Paciente')
    
    for paciente in Paciente.objects.all():
        if paciente.metadatos_adicionales.get('migrado'):
            # Restaurar estado original si existe
            estado_original = paciente.metadatos_adicionales.get('estado_original')
            if estado_original:
                paciente.estado_sistema = estado_original
                paciente.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pacientes', '0002_mejoras_estado_y_etapa'),
    ]

    operations = [
        migrations.RunPython(
            migrar_estados_a_nuevo_formato,
            revertir_migracion
        ),
    ]
