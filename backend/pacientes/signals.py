# backend/pacientes/signals.py - ACTUALIZADO CON TIPO DE ATENCIÓN
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Paciente


@receiver(post_save, sender=Paciente)
def crear_ruta_clinica_con_tipo_atencion(sender, instance, created, **kwargs):
    """
    Signal que:
    1. Asigna automáticamente el tipo de atención más apropiado
    2. Crea la ruta clínica con las etapas específicas del tipo de atención
    """
    if created:
        # Importar aquí para evitar imports circulares
        from rutas_clinicas.models import RutaClinica
        from tipos_atencion.models import TipoAtencion
        
        # Verificar que el paciente no tenga ya una ruta activa
        rutas_existentes = RutaClinica.objects.filter(
            paciente=instance,
            estado__in=['INICIADA', 'EN_PROGRESO']
        ).exists()
        
        if not rutas_existentes:
            # 1. Asignar tipo de atención automáticamente si no tiene
            if not instance.tipo_atencion:
                tipo_sugerido = TipoAtencion.obtener_tipo_sugerido(
                    nivel_urgencia=instance.nivel_urgencia,
                    especialista_requerido=instance.requiere_especialista
                )
                
                if tipo_sugerido:
                    instance.tipo_atencion = tipo_sugerido
                    instance.save(update_fields=['tipo_atencion'])
                else:
                    # Si no hay tipo de atención disponible, usar uno por defecto
                    tipo_default = TipoAtencion.objects.filter(
                        nivel='PRIMARIA',
                        activo=True
                    ).first()
                    
                    if tipo_default:
                        instance.tipo_atencion = tipo_default
                        instance.save(update_fields=['tipo_atencion'])
                    else:
                        print(f"⚠️  ADVERTENCIA: No hay tipos de atención configurados en el sistema")
                        return
            
            # 2. Crear la ruta clínica con el tipo de atención
            ruta = RutaClinica.objects.create(
                paciente=instance,
                tipo_atencion=instance.tipo_atencion,
                # Las etapas se tomarán automáticamente del tipo de atención al iniciar
                metadatos_adicionales={
                    'creada_automaticamente': True,
                    'motivo_ingreso': instance.motivo_consulta or 'Ingreso estándar',
                    'diagnostico_presuntivo': instance.diagnostico_presuntivo,
                }
            )
            
            # 3. Iniciar la ruta automáticamente
            try:
                ruta.iniciar_ruta()
                print(f"✅ Ruta clínica creada automáticamente para {instance.nombre_completo}")
                print(f"   Tipo de Atención: {instance.tipo_atencion.nombre}")
                print(f"   Total de Etapas: {len(instance.tipo_atencion.etapas_flujo)}")
            except ValueError as e:
                print(f"❌ ERROR: {str(e)}")
                ruta.delete()  # Eliminar ruta si no se puede iniciar