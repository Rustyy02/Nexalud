from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Atencion

# --- TUS FUNCIONES ORIGINALES (MANTENIDAS) ---

@receiver(post_save, sender=Atencion)
def gestionar_estado_box_al_guardar(sender, instance, created, **kwargs):
    """
    Gestiona el estado del box automáticamente cuando se guarda una atención.
    """
    # Si la atención acaba de ser creada y está EN_CURSO, ocupar el box
    if created and instance.estado == 'EN_CURSO' and instance.inicio_cronometro:
        instance.box.ocupar(instance.inicio_cronometro)
    
    # Si la atención se completó o canceló, liberar el box
    if instance.estado in ['COMPLETADA', 'CANCELADA'] and instance.box.estado == 'OCUPADO':
        instance.box.liberar()

@receiver(post_save, sender=Atencion)
def crear_ruta_clinica_automatica(sender, instance, created, **kwargs):
    """
    Crea automáticamente una ruta clínica cuando se crea una atención
    para un paciente que no tiene ruta clínica activa.
    """
    if not created:
        return
    
    from rutas_clinicas.models import RutaClinica
    
    # Verificar si el paciente ya tiene una ruta clínica activa
    rutas_activas = RutaClinica.objects.filter(
        paciente=instance.paciente,
        estado__in=['INICIADA', 'EN_PROGRESO', 'PAUSADA']
    ).exists()
    
    if not rutas_activas:
        # print(f"🔍 Paciente {instance.paciente.identificador_hash[:8]} sin ruta clínica")
        # print(f"✨ Creando ruta clínica automática...")
        
        try:
            # Ruta clínica con todas las etapas
            nueva_ruta = RutaClinica.objects.create(
                paciente=instance.paciente,
                etapas_seleccionadas=[
                    'CONSULTA_MEDICA',
                    'PROCESO_EXAMEN',
                    'REVISION_EXAMEN',
                    'HOSPITALIZACION',
                    'OPERACION',
                    'ALTA'
                ],
                estado='INICIADA',
                metadatos_adicionales={
                    'creada_automaticamente': True,
                    'creada_desde_atencion': str(instance.id),
                    'fecha_creacion_automatica': timezone.now().isoformat(),
                    'medico_atencion': instance.medico.get_full_name() if instance.medico else 'N/A'
                }
            )
            
            # Iniciar la ruta automáticamente en CONSULTA_MEDICA
            nueva_ruta.iniciar_ruta(
                usuario=instance.medico,
                etapa_inicial='CONSULTA_MEDICA'
            )
            
            # Actualizar el estado del paciente
            instance.paciente.estado_actual = 'ACTIVO'
            instance.paciente.etapa_actual = 'CONSULTA_MEDICA'
            instance.paciente.save(update_fields=['estado_actual', 'etapa_actual'])
            
        except Exception as e:
            print(f" Error al crear ruta clínica automática: {str(e)}")

# --- NUEVA FUNCIONALIDAD (AGREGADA) ---

@receiver(post_save, sender=Atencion)
def avanzar_ruta_al_completar_atencion(sender, instance, created, **kwargs):
    """
    Signal: Cuando una atención se marca como COMPLETADA,
    avanza automáticamente la ruta clínica asociada a la siguiente etapa.
    """
    # Solo actuamos si es una actualización (no creación) y el estado es COMPLETADA
    if not created and instance.estado == 'COMPLETADA':
        
        # Intentamos obtener la ruta asociada a la atención (si existe relación directa)
        ruta = getattr(instance, 'ruta_clinica', None)
        
        # Si no tiene relación directa, buscamos la ruta activa del paciente
        if not ruta:
            from rutas_clinicas.models import RutaClinica
            ruta = RutaClinica.objects.filter(
                paciente=instance.paciente,
                estado='EN_PROGRESO'
            ).first()
        
        if ruta and ruta.estado == 'EN_PROGRESO':
            # print(f"⚡ SIGNAL: Atención {instance.id} completada -> Avanzando Ruta {ruta.id}")
            
            medico_nombre = instance.medico.get_full_name() if instance.medico else "Sistema"
            
            # Avanzamos la etapa usando el método del modelo
            exito = ruta.avanzar_etapa(
                observaciones=f"Avance automático tras atención con {medico_nombre}",
                usuario=instance.medico
            )
            
            if exito:
                print(f"   ✅ Paciente {instance.paciente.rut} avanzó a: {ruta.etapa_actual}")
                # También actualizamos el paciente para reflejar el cambio en el frontend
                instance.paciente.etapa_actual = ruta.etapa_actual
                instance.paciente.save(update_fields=['etapa_actual'])