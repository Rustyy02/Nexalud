from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from .models import RutaClinica

@receiver(pre_delete, sender=RutaClinica)
def limpiar_etapa_paciente_al_eliminar_ruta(sender, instance, **kwargs):
    
    # Limpia el campo etapa_actual del paciente cuando se elimina una ruta clínica.
    
    # Solo limpia si:
    # - El paciente existe
    # - No hay otras rutas activas para ese paciente
    
    # Esto mantiene la consistencia entre el paciente y sus rutas clínicas.
    
    if not instance.paciente:
        return
    
    # Verificar si hay otras rutas activas para este paciente
    otras_rutas_activas = RutaClinica.objects.filter(
        paciente=instance.paciente,
        estado__in=['PENDIENTE', 'EN_PROGRESO', 'PAUSADA']
    ).exclude(id=instance.id).exists()
    
    # Solo limpiar si esta es la última ruta activa
    if not otras_rutas_activas:
        instance.paciente.etapa_actual = None
        instance.paciente.save(update_fields=['etapa_actual'])
        
        print(f"✅ Limpiado etapa_actual del paciente {instance.paciente.id} al eliminar ruta clínica {instance.id}")


@receiver(post_save, sender=RutaClinica)
def verificar_consistencia_etapa(sender, instance, created, **kwargs):
    
    # Verifica que la etapa_actual del paciente esté sincronizada
    # con la ruta clínica cuando se guarda.
    
    # Esto es una capa adicional de seguridad para mantener la consistencia.
    
    if instance.paciente and instance.estado == 'EN_PROGRESO':
        # Si la ruta está en progreso, asegurar que el paciente tenga la etapa correcta
        if instance.paciente.etapa_actual != instance.etapa_actual:
            instance.paciente.etapa_actual = instance.etapa_actual
            instance.paciente.save(update_fields=['etapa_actual'])
            
            print(f"✅ Sincronizado etapa_actual del paciente {instance.paciente.id} con ruta clínica {instance.id}")
