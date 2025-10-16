# backend/rutas_clinicas/viewsets.py - VERSIÓN MEJORADA
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
    ViewSet mejorado para gestionar rutas clínicas.
    
    Nuevas características:
    - Sincronización automática con estado del paciente
    - Detección de retrasos
    - Historial de cambios completo
    - Observaciones por etapa
    - Validaciones de transición
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
        elif self.action in ['pausar', 'reanudar']:
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
            # Obtener rutas activas y filtrar las que tienen retrasos
            rutas_con_retraso = []
            for ruta in queryset.filter(estado='EN_PROGRESO'):
                if ruta.detectar_retrasos():
                    rutas_con_retraso.append(ruta.id)
            queryset = queryset.filter(id__in=rutas_con_retraso)
        
        return queryset.order_by('-fecha_inicio')
    
    # ============================================
    # ACCIONES PRINCIPALES
    # ============================================
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """Inicia la ruta clínica"""
        ruta = self.get_object()
        usuario = request.user
        
        if ruta.iniciar_ruta(usuario=usuario):
            return Response({
                'success': True,
                'mensaje': 'Ruta iniciada correctamente',
                'estado': ruta.estado,
                'etapa_actual': ruta.get_etapa_actual_display(),
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'porcentaje_completado': ruta.porcentaje_completado
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo iniciar la ruta. Verifique que tenga etapas seleccionadas.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def avanzar(self, request, pk=None):
        """
        Avanza a la siguiente etapa.
        Body opcional: {"observaciones": "texto"}
        """
        ruta = self.get_object()
        usuario = request.user
        observaciones = request.data.get('observaciones', '')
        
        if ruta.avanzar_etapa(observaciones=observaciones, usuario=usuario):
            return Response({
                'success': True,
                'mensaje': 'Etapa avanzada correctamente',
                'etapa_actual': ruta.get_etapa_actual_display() if ruta.etapa_actual else 'Completada',
                'porcentaje_completado': ruta.porcentaje_completado,
                'estado': ruta.estado,
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'completada': ruta.estado == 'COMPLETADA'
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo avanzar la etapa'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def retroceder(self, request, pk=None):
        """
        Retrocede a la etapa anterior.
        Body opcional: {"motivo": "texto"}
        """
        ruta = self.get_object()
        usuario = request.user
        motivo = request.data.get('motivo', '')
        
        if ruta.retroceder_etapa(motivo=motivo, usuario=usuario):
            return Response({
                'success': True,
                'mensaje': 'Se retrocedió a la etapa anterior',
                'etapa_actual': ruta.get_etapa_actual_display(),
                'porcentaje_completado': ruta.porcentaje_completado,
                'estado_paciente': ruta.paciente.get_estado_actual_display()
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se puede retroceder más. Ya está en la primera etapa.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """
        Pausa la ruta clínica.
        Body: {"motivo": "texto"}
        """
        ruta = self.get_object()
        usuario = request.user
        serializer = RutaAccionSerializer(data=request.data)
        
        if serializer.is_valid():
            motivo = serializer.validated_data.get('motivo', 'Sin motivo especificado')
            ruta.pausar_ruta(motivo=motivo, usuario=usuario)
            
            return Response({
                'success': True,
                'estado': ruta.estado,
                'mensaje': f'Ruta pausada: {motivo}',
                'esta_pausado': ruta.esta_pausado,
                'estado_paciente': ruta.paciente.get_estado_actual_display(),
                'etapa_actual': ruta.get_etapa_actual_display()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """Reanuda una ruta pausada"""
        ruta = self.get_object()
        usuario = request.user
        
        if ruta.reanudar_ruta(usuario=usuario):
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
            'mensaje': 'La ruta no está pausada o no se pudo reanudar.',
            'estado_actual': ruta.estado
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # INFORMACIÓN Y ANÁLISIS
    # ============================================
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        Endpoint principal para visualización del timeline.
        Retorna información completa incluyendo retrasos.
        """
        ruta = self.get_object()
        timeline_data = ruta.obtener_info_timeline()
        retrasos = ruta.detectar_retrasos()
        
        # Detectar alertas
        alertas = []
        
        if ruta.esta_pausado:
            alertas.append({
                'tipo': 'pausada',
                'mensaje': f'Ruta pausada: {ruta.motivo_pausa}',
                'severidad': 'warning'
            })
        
        if retrasos:
            for retraso in retrasos:
                alertas.append({
                    'tipo': 'retraso',
                    'mensaje': f'{retraso["etapa_label"]} retrasada {retraso["retraso_minutos"]} minutos',
                    'severidad': 'error',
                    'etapa': retraso['etapa']
                })
        
        if ruta.estado == 'COMPLETADA':
            alertas.append({
                'tipo': 'completada',
                'mensaje': 'Ruta completada exitosamente',
                'severidad': 'success'
            })
        
        data = {
            'paciente': ruta.paciente,
            'ruta_clinica': ruta,
            'timeline': timeline_data,
            'progreso_general': ruta.porcentaje_completado,
            'etapas_completadas': len(ruta.etapas_completadas),
            'etapas_totales': len(ruta.etapas_seleccionadas),
            'tiempo_transcurrido_minutos': int(ruta.obtener_tiempo_total_real().total_seconds() / 60),
            'estado_actual': ruta.estado,
            'esta_pausado': ruta.esta_pausado,
            'alertas': alertas,
            'retrasos': retrasos,
        }
        
        serializer = TimelineSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historial(self, request, pk=None):
        """Retorna el historial completo de cambios de la ruta"""
        ruta = self.get_object()
        
        return Response({
            'ruta_id': str(ruta.id),
            'paciente': {
                'id': str(ruta.paciente.id),
                'nombre': ruta.paciente.metadatos_adicionales.get('nombre', 'N/A'),
            },
            'historial': ruta.historial_cambios,
            'total_cambios': len(ruta.historial_cambios)
        })
    
    @action(detail=True, methods=['get'])
    def retrasos(self, request, pk=None):
        """Detecta y retorna las etapas con retraso"""
        ruta = self.get_object()
        retrasos = ruta.detectar_retrasos()
        
        return Response({
            'tiene_retrasos': len(retrasos) > 0,
            'cantidad_retrasos': len(retrasos),
            'retrasos': retrasos,
            'etapa_actual': ruta.get_etapa_actual_display(),
            'estado': ruta.estado
        })
    
    @action(detail=True, methods=['post'])
    def agregar_observacion(self, request, pk=None):
        """
        Agrega observaciones a la etapa actual.
        Body: {"observaciones": "texto"}
        """
        ruta = self.get_object()
        observaciones = request.data.get('observaciones', '')
        
        if not observaciones:
            return Response({
                'success': False,
                'mensaje': 'Las observaciones no pueden estar vacías'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if ruta.etapa_actual and ruta.etapa_actual in ruta.timestamps_etapas:
            ruta.timestamps_etapas[ruta.etapa_actual]['observaciones'] = observaciones
            ruta.save()
            
            return Response({
                'success': True,
                'mensaje': 'Observaciones agregadas correctamente',
                'etapa': ruta.get_etapa_actual_display(),
                'observaciones': observaciones
            })
        
        return Response({
            'success': False,
            'mensaje': 'No hay etapa actual para agregar observaciones'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # ============================================
    # ENDPOINTS GENERALES
    # ============================================
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Lista rutas clínicas activas"""
        rutas = self.get_queryset().filter(estado__in=['INICIADA', 'EN_PROGRESO'])
        serializer = self.get_serializer(rutas, many=True)
        
        return Response({
            'count': rutas.count(),
            'rutas': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def con_retrasos(self, request):
        """Lista rutas que tienen etapas retrasadas"""
        rutas_activas = self.get_queryset().filter(estado='EN_PROGRESO')
        
        rutas_con_retraso = []
        for ruta in rutas_activas:
            retrasos = ruta.detectar_retrasos()
            if retrasos:
                serialized = RutaClinicaListSerializer(ruta).data
                serialized['retrasos'] = retrasos
                rutas_con_retraso.append(serialized)
        
        return Response({
            'count': len(rutas_con_retraso),
            'rutas': rutas_con_retraso
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales mejoradas"""
        queryset = self.get_queryset()
        
        # Estadísticas básicas
        total = queryset.count()
        iniciadas = queryset.filter(estado='INICIADA').count()
        en_progreso = queryset.filter(estado='EN_PROGRESO').count()
        pausadas = queryset.filter(esta_pausado=True).count()
        completadas = queryset.filter(estado='COMPLETADA').count()
        
        # Detectar rutas con retraso
        rutas_activas = queryset.filter(estado='EN_PROGRESO')
        con_retraso = sum(1 for ruta in rutas_activas if ruta.detectar_retrasos())
        
        # Promedio de progreso
        progreso_promedio = queryset.aggregate(promedio=Avg('porcentaje_completado'))['promedio'] or 0
        
        # Tiempo promedio de completitud
        rutas_completadas = queryset.filter(estado='COMPLETADA', fecha_fin_real__isnull=False)
        tiempo_promedio = 0
        if rutas_completadas.exists():
            tiempos = []
            for ruta in rutas_completadas:
                tiempo = ruta.obtener_tiempo_total_real()
                tiempos.append(tiempo.total_seconds() / 60)
            tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
        
        # Estadísticas por etapa actual
        por_etapa = {}
        for etapa_key, etapa_label in RutaClinica.ETAPAS_CHOICES:
            count = queryset.filter(etapa_actual=etapa_key).count()
            por_etapa[etapa_key] = {
                'label': etapa_label,
                'count': count
            }
        
        return Response({
            'total': total,
            'por_estado': {
                'iniciadas': iniciadas,
                'en_progreso': en_progreso,
                'pausadas': pausadas,
                'completadas': completadas,
            },
            'por_etapa_actual': por_etapa,
            'progreso_promedio': round(progreso_promedio, 2),
            'tiempo_promedio_completitud_minutos': round(tiempo_promedio, 2),
            'tasa_completitud': round((completadas / total * 100) if total > 0 else 0, 2),
            'rutas_con_retraso': con_retraso,
            'tasa_retraso': round((con_retraso / en_progreso * 100) if en_progreso > 0 else 0, 2),
        })
    
    @action(detail=False, methods=['get'])
    def etapas_disponibles(self, request):
        """Lista etapas disponibles con duraciones estimadas"""
        etapas = [
            {
                'key': key,
                'label': label,
                'duracion_estimada': RutaClinica.DURACIONES_ESTIMADAS.get(key, 30),
                'estado_paciente': RutaClinica.ETAPA_A_ESTADO_PACIENTE.get(key, 'EN_CONSULTA')
            }
            for key, label in RutaClinica.ETAPAS_CHOICES
        ]
        
        return Response({
            'etapas': etapas,
            'total': len(etapas)
        })
