# backend/rutas_clinicas/viewsets.py
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
    ViewSet para gestionar rutas clínicas simplificadas.
    
    Las etapas son campos dentro del modelo, no una clase separada.
    
    Endpoints disponibles:
    - GET /api/rutas-clinicas/ - Lista todas las rutas
    - POST /api/rutas-clinicas/ - Crea una nueva ruta
    - GET /api/rutas-clinicas/{id}/ - Detalle de una ruta
    - PUT /api/rutas-clinicas/{id}/ - Actualiza una ruta
    - PATCH /api/rutas-clinicas/{id}/ - Actualiza parcialmente
    - DELETE /api/rutas-clinicas/{id}/ - Elimina una ruta
    
    Acciones personalizadas:
    - POST /api/rutas-clinicas/{id}/iniciar/ - Inicia la ruta
    - POST /api/rutas-clinicas/{id}/avanzar/ - Avanza a siguiente etapa
    - POST /api/rutas-clinicas/{id}/retroceder/ - Retrocede una etapa
    - POST /api/rutas-clinicas/{id}/pausar/ - Pausa la ruta
    - POST /api/rutas-clinicas/{id}/reanudar/ - Reanuda la ruta
    - POST /api/rutas-clinicas/{id}/completar/ - Completa la ruta
    - GET /api/rutas-clinicas/{id}/timeline/ - Timeline completo
    - GET /api/rutas-clinicas/activas/ - Lista rutas activas
    - GET /api/rutas-clinicas/estadisticas/ - Estadísticas
    - GET /api/rutas-clinicas/etapas-disponibles/ - Lista de etapas disponibles
    """
    queryset = RutaClinica.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
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
        """Filtra el queryset basado en parámetros de query"""
        queryset = RutaClinica.objects.select_related('paciente')
        
        # Filtros opcionales
        estado = self.request.query_params.get('estado', None)
        paciente_id = self.request.query_params.get('paciente', None)
        etapa_actual = self.request.query_params.get('etapa', None)
        pausado = self.request.query_params.get('pausado', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if etapa_actual:
            queryset = queryset.filter(etapa_actual=etapa_actual)
        
        if pausado is not None:
            pausado_bool = pausado.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(esta_pausado=pausado_bool)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_inicio__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_inicio__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_inicio')
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """
        Inicia la ruta clínica (comienza la primera etapa).
        
        POST /api/rutas-clinicas/{id}/iniciar/
        """
        ruta = self.get_object()
        
        if ruta.iniciar_ruta():
            return Response({
                'success': True,
                'mensaje': 'Ruta iniciada correctamente',
                'estado': ruta.estado,
                'etapa_actual': ruta.get_etapa_actual_display(),
                'porcentaje_completado': ruta.porcentaje_completado
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo iniciar la ruta. Verifique que tenga etapas seleccionadas.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def avanzar(self, request, pk=None):
        """
        Avanza a la siguiente etapa del proceso.
        
        POST /api/rutas-clinicas/{id}/avanzar/
        """
        ruta = self.get_object()
        
        if ruta.avanzar_etapa():
            return Response({
                'success': True,
                'mensaje': 'Etapa avanzada correctamente',
                'etapa_actual': ruta.get_etapa_actual_display() if ruta.etapa_actual else 'Completada',
                'porcentaje_completado': ruta.porcentaje_completado,
                'estado': ruta.estado,
                'completada': ruta.estado == 'COMPLETADA'
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo avanzar la etapa'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def retroceder(self, request, pk=None):
        """
        Retrocede a la etapa anterior (por si hay error).
        
        POST /api/rutas-clinicas/{id}/retroceder/
        """
        ruta = self.get_object()
        
        if ruta.retroceder_etapa():
            return Response({
                'success': True,
                'mensaje': 'Se retrocedió a la etapa anterior',
                'etapa_actual': ruta.get_etapa_actual_display(),
                'porcentaje_completado': ruta.porcentaje_completado
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se puede retroceder más. Ya está en la primera etapa.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def pausar(self, request, pk=None):
        """
        Pausa la ruta clínica completa.
        
        POST /api/rutas-clinicas/{id}/pausar/
        Body: {"motivo": "Razón de la pausa"}
        """
        ruta = self.get_object()
        serializer = RutaAccionSerializer(data=request.data)
        
        if serializer.is_valid():
            motivo = serializer.validated_data.get('motivo', 'Sin motivo especificado')
            ruta.pausar_ruta(motivo)
            
            return Response({
                'success': True,
                'estado': ruta.estado,
                'mensaje': f'Ruta pausada exitosamente por: {motivo}', # Mensaje corregido
                'esta_pausado': ruta.esta_pausado,
                'etapa_actual': ruta.get_etapa_actual_display()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) # Retorna los errores de validación del serializer
    
    @action(detail=True, methods=['post'])
    def reanudar(self, request, pk=None):
        """
        Reanuda una ruta pausada.
        
        POST /api/rutas-clinicas/{id}/reanudar/
        """
        ruta = self.get_object()
        
        if ruta.reanudar_ruta():
            return Response({
                'success': True,
                'estado': ruta.estado,
                'mensaje': 'Ruta reanudada exitosamente',
                'esta_pausado': ruta.esta_pausado,
                'etapa_actual': ruta.get_etapa_actual_display()
            })
        
        return Response({
            'success': False,
            'mensaje': 'La ruta no está pausada o no se pudo reanudar.',
            'estado_actual': ruta.estado
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def completar(self, request, pk=None):
        """
        Marca la ruta como completada manualmente.
        
        POST /api/rutas-clinicas/{id}/completar/
        """
        ruta = self.get_object()
        
        ruta.estado = 'COMPLETADA'
        ruta.fecha_fin_real = timezone.now()
        ruta.porcentaje_completado = 100.0
        ruta.etapa_actual = None
        ruta.save()
        
        return Response({
            'success': True,
            'mensaje': 'Ruta marcada como completada',
            'estado': ruta.estado,
            'fecha_fin_real': ruta.fecha_fin_real,
            'tiempo_total': int(ruta.obtener_tiempo_total_real().total_seconds() / 60)
        })
    
    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        Endpoint para obtener el timeline completo del paciente.
        
        GET /api/rutas-clinicas/{id}/timeline/
        
        Retorna toda la información necesaria para renderizar el timeline horizontal.
        """
        ruta = self.get_object()
        timeline_data = ruta.obtener_info_timeline()
        
        # Detectar alertas
        alertas = []
        
        if ruta.esta_pausado:
            alertas.append({
                'tipo': 'pausada',
                'mensaje': f'Ruta pausada: {ruta.motivo_pausa}',
                'severidad': 'warning'
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
        }
        
        serializer = TimelineSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Lista rutas clínicas activas (iniciadas o en progreso).
        
        GET /api/rutas-clinicas/activas/
        """
        rutas = self.get_queryset().filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        )
        
        serializer = self.get_serializer(rutas, many=True)
        return Response({
            'count': rutas.count(),
            'rutas': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def pausadas(self, request):
        """
        Lista rutas clínicas pausadas.
        
        GET /api/rutas-clinicas/pausadas/
        """
        rutas = self.get_queryset().filter(esta_pausado=True)
        
        serializer = self.get_serializer(rutas, many=True)
        return Response({
            'count': rutas.count(),
            'rutas': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de rutas clínicas.
        
        GET /api/rutas-clinicas/estadisticas/
        """
        queryset = self.get_queryset()
        
        # Estadísticas por estado
        total = queryset.count()
        iniciadas = queryset.filter(estado='INICIADA').count()
        en_progreso = queryset.filter(estado='EN_PROGRESO').count()
        pausadas = queryset.filter(esta_pausado=True).count()
        completadas = queryset.filter(estado='COMPLETADA').count()
        canceladas = queryset.filter(estado='CANCELADA').count()
        
        # Promedio de progreso
        progreso_promedio = queryset.aggregate(
            promedio=Avg('porcentaje_completado')
        )['promedio'] or 0
        
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
                'canceladas': canceladas,
            },
            'por_etapa_actual': por_etapa,
            'progreso_promedio': round(progreso_promedio, 2),
            'tiempo_promedio_completitud_minutos': round(tiempo_promedio, 2),
            'tasa_completitud': round((completadas / total * 100) if total > 0 else 0, 2),
        })
    
    @action(detail=False, methods=['get'])
    def etapas_disponibles(self, request):
        """
        Lista todas las etapas disponibles para selección.
        
        GET /api/rutas-clinicas/etapas-disponibles/
        """
        etapas = [
            {'key': key, 'label': label}
            for key, label in RutaClinica.ETAPAS_CHOICES
        ]
        
        return Response({
            'etapas': etapas,
            'total': len(etapas)
        })
    
    @action(detail=True, methods=['post'])
    def recalcular_progreso(self, request, pk=None):
        """
        Recalcula manualmente el progreso de la ruta.
        
        POST /api/rutas-clinicas/{id}/recalcular_progreso/
        """
        ruta = self.get_object()
        progreso = ruta.calcular_progreso()
        
        return Response({
            'success': True,
            'porcentaje_completado': progreso,
            'mensaje': 'Progreso recalculado exitosamente',
            'estado': ruta.estado
        })
    
    @action(detail=True, methods=['get'])
    def info_etapa_actual(self, request, pk=None):
        """
        Obtiene información detallada de la etapa actual.
        
        GET /api/rutas-clinicas/{id}/info_etapa_actual/
        """
        ruta = self.get_object()
        
        if not ruta.etapa_actual:
            return Response({
                'etapa_actual': None,
                'mensaje': 'No hay etapa actual'
            })
        
        timestamps = ruta.timestamps_etapas.get(ruta.etapa_actual, {})
        
        return Response({
            'etapa_key': ruta.etapa_actual,
            'etapa_label': ruta.get_etapa_actual_display(),
            'orden': ruta.indice_etapa_actual + 1,
            'fecha_inicio': timestamps.get('fecha_inicio'),
            'fecha_fin': timestamps.get('fecha_fin'),
            'estado': 'EN_PROCESO',
            'es_actual': True
        })