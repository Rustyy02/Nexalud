from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import RutaClinica, EtapaRuta
from .serializers import (
    RutaClinicaSerializer,
    RutaClinicaListSerializer,
    RutaClinicaCreateSerializer,
    EtapaRutaSerializer,
    EtapaRutaListSerializer,
    TimelineSerializer
)


class RutaClinicaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar rutas clínicas.
    
    Este es el core del sistema de timeline.
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
        return RutaClinicaSerializer
    
    def get_queryset(self):
        queryset = RutaClinica.objects.select_related('paciente').prefetch_related('etapas')
        
        # Filtros
        estado = self.request.query_params.get('estado', None)
        paciente_id = self.request.query_params.get('paciente', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        return queryset.order_by('-fecha_inicio')
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        Endpoint especializado para obtener el timeline completo del paciente.
        
        GET /api/rutas-clinicas/{id}/timeline/
        
        Retorna toda la información necesaria para renderizar el timeline horizontal.
        """
        ruta = self.get_object()
        etapas = ruta.etapas.all().order_by('orden')
        
        data = {
            'paciente': {
                'id': str(ruta.paciente.id),
                'identificador_hash': ruta.paciente.identificador_hash,
                'edad': ruta.paciente.edad,
                'estado_actual': ruta.paciente.estado_actual,
                'nivel_urgencia': ruta.paciente.nivel_urgencia,
            },
            'ruta_clinica': {
                'id': str(ruta.id),
                'estado': ruta.estado,
                'porcentaje_completado': ruta.porcentaje_completado,
                'fecha_inicio': ruta.fecha_inicio,
                'fecha_estimada_fin': ruta.fecha_estimada_fin,
            },
            'etapas': EtapaRutaListSerializer(etapas, many=True).data,
            'progreso_general': ruta.porcentaje_completado,
            'etapas_completadas': etapas.filter(estado='COMPLETADA').count(),
            'etapas_totales': etapas.count(),
            'tiempo_transcurrido_minutos': int(ruta.obtener_tiempo_total_real().total_seconds() / 60),
            'estado_actual': ruta.estado,
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def recalcular_progreso(self, request, pk=None):
        """
        Recalcula el progreso de la ruta.
        
        POST /api/rutas-clinicas/{id}/recalcular_progreso/
        """
        ruta = self.get_object()
        progreso = ruta.calcular_progreso()
        
        return Response({
            'success': True,
            'porcentaje_completado': progreso,
            'mensaje': 'Progreso recalculado exitosamente'
        })
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """
        Pausa la ruta clínica completa.
        
        POST /api/rutas-clinicas/{id}/pausar/
        Body: {"motivo": "Razón de la pausa"}
        """
        ruta = self.get_object()
        motivo = request.data.get('motivo', 'Sin motivo especificado')
        
        ruta.pausar_ruta(motivo)
        
        return Response({
            'success': True,
            'estado': ruta.estado,
            'mensaje': 'Ruta pausada exitosamente'
        })
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """
        Reanuda una ruta pausada.
        
        POST /api/rutas-clinicas/{id}/reanudar/
        """
        ruta = self.get_object()
        
        if ruta.estado != 'PAUSADA':
            return Response({
                'success': False,
                'mensaje': 'La ruta no está pausada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        ruta.reanudar_ruta()
        
        return Response({
            'success': True,
            'estado': ruta.estado,
            'mensaje': 'Ruta reanudada exitosamente'
        })
    
    @action(detail=True, methods=['get'])
    def retrasos(self, request, pk=None):
        """
        Obtiene las etapas con retraso.
        
        GET /api/rutas-clinicas/{id}/retrasos/
        """
        ruta = self.get_object()
        etapas_retrasadas = ruta.detectar_retrasos()
        
        serializer = EtapaRutaListSerializer(etapas_retrasadas, many=True)
        
        return Response({
            'total_retrasos': len(etapas_retrasadas),
            'etapas': serializer.data
        })


class EtapaRutaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar etapas individuales de las rutas clínicas.
    
    Este ViewSet maneja las acciones sobre los nodos del timeline.
    """
    queryset = EtapaRuta.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EtapaRutaListSerializer
        return EtapaRutaSerializer
    
    def get_queryset(self):
        queryset = EtapaRuta.objects.select_related('ruta_clinica', 'ruta_clinica__paciente')
        
        # Filtros
        ruta_id = self.request.query_params.get('ruta', None)
        estado = self.request.query_params.get('estado', None)
        es_estatico = self.request.query_params.get('estatico', None)
        
        if ruta_id:
            queryset = queryset.filter(ruta_clinica_id=ruta_id)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if es_estatico is not None:
            estatico_bool = es_estatico.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(es_estatico=estatico_bool)
        
        return queryset.order_by('ruta_clinica', 'orden')
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """
        Inicia la etapa (para el timeline).
        
        POST /api/etapas/{id}/iniciar/
        """
        etapa = self.get_object()
        
        if etapa.iniciar_etapa():
            return Response({
                'success': True,
                'mensaje': f'Etapa "{etapa.nombre}" iniciada',
                'estado': etapa.estado,
                'fecha_inicio': etapa.fecha_inicio
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo iniciar la etapa. Verifica su estado actual.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        Finaliza la etapa (para el timeline).
        
        POST /api/etapas/{id}/finalizar/
        """
        etapa = self.get_object()
        
        if etapa.finalizar_etapa():
            # Recalcular progreso de la ruta
            etapa.ruta_clinica.calcular_progreso()
            
            return Response({
                'success': True,
                'mensaje': f'Etapa "{etapa.nombre}" finalizada',
                'estado': etapa.estado,
                'duracion_real': etapa.duracion_real,
                'fecha_fin': etapa.fecha_fin,
                'progreso_ruta': etapa.ruta_clinica.porcentaje_completado
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo finalizar la etapa. Verifica su estado actual.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """
        Pausa la etapa (nodo estático).
        
        POST /api/etapas/{id}/pausar/
        Body: {"motivo": "Esperando resultados de laboratorio externo"}
        """
        etapa = self.get_object()
        motivo = request.data.get('motivo', 'Sin motivo especificado')
        
        if etapa.pausar_etapa(motivo):
            return Response({
                'success': True,
                'mensaje': f'Etapa "{etapa.nombre}" pausada',
                'estado': etapa.estado,
                'es_estatico': etapa.es_estatico,
                'motivo_pausa': etapa.motivo_pausa
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo pausar la etapa. Verifica su estado actual.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """
        Reanuda una etapa pausada.
        
        POST /api/etapas/{id}/reanudar/
        """
        etapa = self.get_object()
        
        if etapa.reanudar_etapa():
            return Response({
                'success': True,
                'mensaje': f'Etapa "{etapa.nombre}" reanudada',
                'estado': etapa.estado,
                'es_estatico': etapa.es_estatico
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo reanudar la etapa. Verifica su estado actual.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def progreso(self, request, pk=None):
        """
        Info de cada etapa en detalle, para el tooltip.
        
        GET /api/etapas/{id}/progreso/
        """
        etapa = self.get_object()
        
        return Response({
            'id': str(etapa.id),
            'nombre': etapa.nombre,
            'orden': etapa.orden,
            'estado': etapa.estado,
            'porcentaje_avance': etapa.obtener_porcentaje_avance(),
            'tiempo_transcurrido_minutos': self._get_tiempo_minutos(etapa.calcular_tiempo_transcurrido()),
            'duracion_estimada': etapa.duracion_estimada,
            'duracion_real': etapa.duracion_real,
            'tiene_retraso': etapa.detectar_retraso(),
            'es_estatico': etapa.es_estatico,
            'motivo_pausa': etapa.motivo_pausa if etapa.es_estatico else None
        })
    
    def _get_tiempo_minutos(self, timedelta_obj):
        """Convertir el timedelta a minutos para mostrar en la respuesta"""
        if timedelta_obj:
            return int(timedelta_obj.total_seconds() / 60)
        return None