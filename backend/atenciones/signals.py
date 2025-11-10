from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Atencion

@receiver(post_save, sender=Atencion)
def gestionar_estado_box_al_guardar(sender, instance, created, **kwargs):
    
    # Gestiona el estado del box automáticamente cuando se guarda una atención.
    
    # Si la atención acaba de ser creada y está EN_CURSO, ocupar el box
    if created and instance.estado == 'EN_CURSO' and instance.inicio_cronometro:
        instance.box.ocupar(instance.inicio_cronometro)
    
    # Si la atención se completó o canceló, liberar el box
    if instance.estado in ['COMPLETADA', 'CANCELADA'] and instance.box.estado == 'OCUPADO':
        instance.box.liberar()