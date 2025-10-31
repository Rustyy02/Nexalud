# backend/rutas_clinicas/viewsets.py - VERSIÓN CORREGIDA
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import RutaClinica
from .serializers import (
    RutaClinicaSerializer,
    RutaClinicaListSerializer,
    RutaClinicaCreateSerializer,
    TimelineSerializer,
    RutaAccionSerializer
)


class RutaClinicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet corregido para gestionar rutas clínicas con flujo lineal
    """
    queryset = RutaClinica.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RutaClinicaListSerializer
        elif self.action == 'create':
            return RutaClinicaCreateSerializer
        elif self.action == 'timeline':
            return TimelineSerializer
        elif self.action in ['pausar', 'reanudar', 'avanzar', 'retroceder']:
            return RutaAccionSerializer
        return RutaClinicaSerializer
    
    def get_queryset(self):
        queryset = RutaClinica.objects.select_related('paciente')
        
        # Filtros
        estado = self.request.query_params.get('estado')
        paciente_id = self.request.query_params.get('paciente')
        etapa_actual = self.request.query_params.get('etapa')
        pausado = self.request.query_params.get('pausado')
        con_retraso = self.request.query_params.get('con_retraso')
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        if etapa_actual:
            queryset = queryset.filter(etapa_actual=etapa_actual)
        if pausado is not None:
            pausado_bool = pausado.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(esta_pausado=pausado_bool)
        
        # Filtro de rutas con retraso
        if con_retraso and con_retraso.lower() in ['true', '1', 'yes']:
            rutas_con_retraso = []
            for ruta in queryset.filter(estado='EN_PROGRESO'):
                if ruta.detectar_retrasos():
                    rutas_con_retraso.append(ruta.id)
            queryset = queryset.filter(id__in=rutas_con_retraso)
        
        return queryset.order_by('-fecha_inicio')
    
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva ruta clínica con validaciones mejoradas
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Crear y obtener la instancia
        ruta = serializer.save()
        
        # Retornar con el serializer completo
        output_serializer = RutaClinicaSerializer(ruta)
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    # ============================================
    # ACCIONES PRINCIPALES CORREGIDAS
    # ============================================
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """
        Inicia la ruta clínica con etapa opcional
        Body opcional: {"etapa_inicial": "HOSPITALIZACION"}
        """
        ruta = self.get_object()
        usuario = request.user
        etapa_inicial = request.data.get('etapa_inicial')
        
        # Validar que la ruta no esté ya iniciada
        if ruta.estado != 'INICIADA':
            return Response({
                'success': False,
                'mensaje': f'La ruta ya está {ruta.get_estado_display()}. No se puede iniciar nuevamente.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Iniciar con etapa especificada o por defecto
        if ruta.iniciar_ruta(usuario=usuario, etapa_inicial=etapa_inicial):
            # Recargar para obtener datos actualizados
            ruta.refresh_from_db()
            
            return Response({
                'success': True,
                'mensaje': 'Ruta iniciada correctamente',
                'estado': ruta.estado,
                'etapa_actual': ruta.get_etapa_actual_display(),
                'etapa_key': ruta.etapa_actual,
                'indice_etapa': ruta.indice_etapa_actual,
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'etapa_paciente': ruta.paciente.get_etapa_actual_display() if ruta.paciente.etapa_actual else None,
                'porcentaje_completado': ruta.porcentaje_completado,
                'etapas_completadas': ruta.etapas_completadas,
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo iniciar la ruta.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def avanzar(self, request, pk=None):
        """
        Avanza a la siguiente etapa de forma lineal
        Body opcional: {"observaciones": "texto"}
        """
        ruta = self.get_object()
        usuario = request.user
        observaciones = request.data.get('observaciones', '')
        
        # Validaciones previas
        if ruta.estado != 'EN_PROGRESO':
            return Response({
                'success': False,
                'mensaje': f'No se puede avanzar. La ruta está {ruta.get_estado_display()}',
                'estado_actual': ruta.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not ruta.etapa_actual:
            return Response({
                'success': False,
                'mensaje': 'No hay etapa actual configurada. Inicie la ruta primero.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Intentar avanzar
        if ruta.avanzar_etapa(observaciones=observaciones, usuario=usuario):
            # Recargar para obtener datos actualizados
            ruta.refresh_from_db()
            
            return Response({
                'success': True,
                'mensaje': 'Ruta completada exitosamente' if ruta.estado == 'COMPLETADA' else 'Etapa avanzada correctamente',
                'etapa_actual': ruta.get_etapa_actual_display() if ruta.etapa_actual else None,
                'etapa_key': ruta.etapa_actual,
                'indice_etapa': ruta.indice_etapa_actual,
                'porcentaje_completado': ruta.porcentaje_completado,
                'estado': ruta.estado,
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'etapa_paciente': ruta.paciente.get_etapa_actual_display() if ruta.paciente.etapa_actual else None,
                'completada': ruta.estado == 'COMPLETADA',
                'etapas_completadas': ruta.etapas_completadas,
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se puede avanzar más. La ruta ya está en la última etapa.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def retroceder(self, request, pk=None):
        """
        Retrocede a la etapa anterior o reactiva una ruta completada
        Body opcional: {"motivo": "texto"}
        """
        ruta = self.get_object()
        usuario = request.user
        motivo = request.data.get('motivo', '')
        
        # Validar estado
        if ruta.estado not in ['EN_PROGRESO', 'COMPLETADA']:
            return Response({
                'success': False,
                'mensaje': f'No se puede retroceder. La ruta está {ruta.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Si está completada, informar que se reactivará
        mensaje_base = 'Ruta reactivada en la última etapa' if ruta.estado == 'COMPLETADA' else 'Se retrocedió a la etapa anterior'
        
        if ruta.retroceder_etapa(motivo=motivo, usuario=usuario):
            # Recargar para obtener datos actualizados
            ruta.refresh_from_db()
            
            return Response({
                'success': True,
                'mensaje': mensaje_base,
                'etapa_actual': ruta.get_etapa_actual_display(),
                'etapa_key': ruta.etapa_actual,
                'indice_etapa': ruta.indice_etapa_actual,
                'porcentaje_completado': ruta.porcentaje_completado,
                'estado': ruta.estado,
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'etapa_paciente': ruta.paciente.get_etapa_actual_display() if ruta.paciente.etapa_actual else None,
                'etapas_completadas': ruta.etapas_completadas,
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se puede retroceder más. Ya está en la primera etapa.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """
        Pausa la ruta clínica
        Body: {"motivo": "texto"}
        """
        ruta = self.get_object()
        usuario = request.user
        serializer = RutaAccionSerializer(data=request.data)
        
        if serializer.is_valid():
            motivo = serializer.validated_data.get('motivo', 'Sin motivo especificado')
            
            if ruta.pausar_ruta(motivo=motivo, usuario=usuario):
                ruta.refresh_from_db()
                
                return Response({
                    'success': True,
                    'estado': ruta.estado,
                    'mensaje': f'Ruta pausada: {motivo}',
                    'esta_pausado': ruta.esta_pausado,
                    'estado_paciente': ruta.paciente.get_estado_actual_display(),
                    'etapa_actual': ruta.get_etapa_actual_display()
                })
            
            return Response({
                'success': False,
                'mensaje': f'No se puede pausar. La ruta está {ruta.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """Reanuda una ruta pausada"""
        ruta = self.get_object()
        usuario = request.user
        
        if ruta.reanudar_ruta(usuario=usuario):
            ruta.refresh_from_db()
            
            return Response({
                'success': True,
                'estado': ruta.estado,
                'mensaje': 'Ruta reanudada exitosamente',
                'esta_pausado': ruta.esta_pausado,
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'etapa_actual': ruta.get_etapa_actual_display()
            })
        
        return Response({
            'success': False,
            'mensaje': f'La ruta no está pausada. Estado actual: {ruta.get_estado_display()}',
            'estado_actual': ruta.estado
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # INFORMACIÓN Y ANÁLISIS
    # ============================================
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        Obtiene el timeline completo con validaciones mejoradas
        """
        try:
            ruta = self.get_object()
            
            # Obtener timeline
            timeline_data = ruta.obtener_timeline_completo()
            
            # Calcular estadísticas
            etapas_completadas = sum(1 for etapa in timeline_data if etapa['estado'] == 'COMPLETADA')
            tiempo_total_minutos = 0
            retrasos = []
            
            for etapa in timeline_data:
                # Calcular tiempo real si existe
                if etapa.get('duracion_real'):
                    tiempo_total_minutos += etapa['duracion_real']
                
                # Detectar retrasos
                if etapa.get('retrasada'):
                    retrasos.append({
                        'etapa': etapa['etapa_key'],
                        'etapa_label': etapa['etapa_label'],
                        'retraso_minutos': 0,  # Se calculará en el modelo
                    })
            
            # Validar si se puede avanzar/retroceder
            puede_avanzar = (
                ruta.estado == 'EN_PROGRESO' and 
                ruta.etapa_actual is not None and
                ruta.indice_etapa_actual < len(ruta.etapas_seleccionadas)
            )
            
            puede_retroceder = (
                ruta.estado == 'COMPLETADA' or
                (ruta.estado == 'EN_PROGRESO' and ruta.indice_etapa_actual > 0)
            )
            
            # Construir respuesta
            response_data = {
                'ruta_clinica': {
                    'id': str(ruta.id),
                    'estado': ruta.estado,
                    'estado_display': ruta.get_estado_display(),
                    'etapa_actual': ruta.etapa_actual,
                    'etapa_actual_display': ruta.get_etapa_actual_display() if ruta.etapa_actual else None,
                    'indice_etapa_actual': ruta.indice_etapa_actual,
                    'esta_pausado': ruta.esta_pausado,
                    'motivo_pausa': ruta.motivo_pausa if ruta.esta_pausado else None,
                    'puede_avanzar': puede_avanzar,
                    'puede_retroceder': puede_retroceder,
                    'etapas_seleccionadas': ruta.etapas_seleccionadas,
                    'etapas_completadas': ruta.etapas_completadas,
                },
                'paciente': {
                    'id': str(ruta.paciente.id),
                    'identificador_hash': ruta.paciente.identificador_hash,
                    'nombre': ruta.paciente.metadatos_adicionales.get('nombre', 'N/A') 
                             if isinstance(ruta.paciente.metadatos_adicionales, dict) 
                             else f'Paciente {ruta.paciente.identificador_hash[:8]}',
                    'edad': ruta.paciente.edad,
                    'estado_actual': ruta.paciente.get_estado_actual_display(),
                    'etapa_actual': ruta.paciente.get_etapa_actual_display() if ruta.paciente.etapa_actual else None,
                },
                'timeline': timeline_data,
                'etapas_totales': len(ruta.etapas_seleccionadas) if ruta.etapas_seleccionadas else 0,
                'etapas_completadas': etapas_completadas,
                'progreso_general': ruta.porcentaje_completado,
                'tiempo_transcurrido_minutos': tiempo_total_minutos,
                'retrasos': ruta.detectar_retrasos(),
                'alertas': self._generar_alertas(ruta, retrasos, tiempo_total_minutos),
            }
            
            return Response(response_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return Response(
                {
                    'error': 'Error al obtener el timeline',
                    'detalle': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generar_alertas(self, ruta, retrasos, tiempo_total_minutos):
        """Genera alertas basadas en el estado de la ruta"""
        alertas = []
        
        if ruta.esta_pausado:
            alertas.append({
                'tipo': 'warning',
                'mensaje': f'Ruta pausada: {ruta.motivo_pausa or "Sin motivo especificado"}',
                'prioridad': 'alta'
            })
        
        # Verificar sincronización
        if ruta.etapa_actual != ruta.paciente.etapa_actual:
            alertas.append({
                'tipo': 'danger',
                'mensaje': 'Desincronización detectada entre ruta y paciente',
                'prioridad': 'critica'
            })
        
        if retrasos:
            for retraso in retrasos[:3]:  # Limitar a 3 alertas de retraso
                alertas.append({
                    'tipo': 'warning',
                    'mensaje': f'Retraso en {retraso.get("etapa_label", "etapa")}',
                    'prioridad': 'media'
                })
        
        if ruta.estado == 'EN_PROGRESO' and ruta.porcentaje_completado < 30 and tiempo_total_minutos > 120:
            alertas.append({
                'tipo': 'info',
                'mensaje': 'Progreso más lento de lo esperado',
                'prioridad': 'baja'
            })
        
        return alertas
    
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """Retorna el historial completo de cambios"""
        ruta = self.get_object()
        
        return Response({
            'ruta_id': str(ruta.id),
            'paciente': {
                'id': str(ruta.paciente.id),
                'nombre': ruta.paciente.metadatos_adicionales.get('nombre', 'N/A') 
                         if isinstance(ruta.paciente.metadatos_adicionales, dict) 
                         else f'Paciente {ruta.paciente.identificador_hash[:8]}',
            },
            'historial': ruta.historial_cambios,
            'total_cambios': len(ruta.historial_cambios)
        })
    
    @action(detail=True, methods=['get'])
    def validar_estado(self, request, pk=None):
        """
        Valida el estado actual de la ruta y su sincronización
        """
        ruta = self.get_object()
        
        # Validaciones
        sincronizado = ruta.etapa_actual == ruta.paciente.etapa_actual
        
        etapas = ruta.etapas_seleccionadas if ruta.etapas_seleccionadas else []
        
        # Validar consistencia de índice
        indice_valido = True
        if ruta.etapa_actual:
            if ruta.etapa_actual in etapas:
                indice_esperado = etapas.index(ruta.etapa_actual)
                indice_valido = (ruta.indice_etapa_actual == indice_esperado)
        
        # Validar completadas
        completadas_validas = all(
            etapa in etapas for etapa in ruta.etapas_completadas
        )
        
        return Response({
            'ruta_id': str(ruta.id),
            'estado': ruta.estado,
            'etapa_actual': ruta.etapa_actual,
            'indice_etapa_actual': ruta.indice_etapa_actual,
            'validaciones': {
                'sincronizado_con_paciente': sincronizado,
                'indice_consistente': indice_valido,
                'completadas_validas': completadas_validas,
                'puede_avanzar': ruta.estado == 'EN_PROGRESO' and ruta.indice_etapa_actual < len(etapas),
                'puede_retroceder': ruta.estado == 'COMPLETADA' or (ruta.estado == 'EN_PROGRESO' and ruta.indice_etapa_actual > 0),
            },
            'detalles': {
                'etapa_paciente': ruta.paciente.etapa_actual,
                'etapa_paciente_display': ruta.paciente.get_etapa_actual_display() if ruta.paciente.etapa_actual else None,
                'etapas_seleccionadas': etapas,
                'etapas_completadas': ruta.etapas_completadas,
                'porcentaje': ruta.porcentaje_completado,
            }
        })
    
    # Métodos existentes se mantienen...
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de rutas clínicas"""
        queryset = self.get_queryset()
        
        total = queryset.count()
        iniciadas = queryset.filter(estado='INICIADA').count()
        en_progreso = queryset.filter(estado='EN_PROGRESO').count()
        pausadas = queryset.filter(esta_pausado=True).count()
        completadas = queryset.filter(estado='COMPLETADA').count()
        canceladas = queryset.filter(estado='CANCELADA').count()
        
        progreso_promedio = queryset.aggregate(promedio=Avg('porcentaje_completado'))['promedio'] or 0
        
        return Response({
            'total': total,
            'por_estado': {
                'iniciadas': iniciadas,
                'en_progreso': en_progreso,
                'pausadas': pausadas,
                'completadas': completadas,
                'canceladas': canceladas,
            },
            'progreso_promedio': round(progreso_promedio, 2),
            'tasa_completitud': round((completadas / total * 100) if total > 0 else 0, 2),
        })