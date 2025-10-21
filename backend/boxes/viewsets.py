from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count
from django.utils import timezone
from .models import Box
from .serializers import (
    BoxSerializer,
    BoxListSerializer,
    BoxCreateUpdateSerializer,
    BoxEstadisticasSerializer,
    BoxOcupacionSerializer
)

class BoxViewSet(viewsets.ModelViewSet):
    queryset = Box.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        # MODIFICAR ESTA PARTE
        if self.action == 'list':
            return BoxSerializer # CAMBIADO
        elif self.action in ['create', 'update', 'partial_update']:
            return BoxCreateUpdateSerializer
        elif self.action in ['ocupar', 'liberar']:
            return BoxOcupacionSerializer
        elif self.action == 'estadisticas':
            return BoxEstadisticasSerializer
        return BoxSerializer
class BoxViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar boxes de atención.
    
    Endpoints disponibles:
    - GET /api/boxes/ - Lista todos los boxes
    - POST /api/boxes/ - Crea un nuevo box
    - GET /api/boxes/{id}/ - Detalle de un box
    - PUT /api/boxes/{id}/ - Actualiza un box completo
    - PATCH /api/boxes/{id}/ - Actualiza parcialmente un box
    - DELETE /api/boxes/{id}/ - Elimina un box
    
    Acciones personalizadas:
    - POST /api/boxes/{id}/ocupar/ - Marca box como ocupado
    - POST /api/boxes/{id}/liberar/ - Libera el box
    - GET /api/boxes/disponibles/ - Lista boxes disponibles
    - GET /api/boxes/ocupados/ - Lista boxes ocupados
    - GET /api/boxes/estadisticas/ - Estadísticas generales
    - GET /api/boxes/por_especialidad/ - Agrupa por especialidad
    - POST /api/boxes/{id}/mantenimiento/ - Marca en mantenimiento
    - POST /api/boxes/reset_ocupacion/ - Resetea contadores diarios
    """
    queryset = Box.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return BoxListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BoxCreateUpdateSerializer
        elif self.action in ['ocupar', 'liberar']:
            return BoxOcupacionSerializer
        elif self.action == 'estadisticas':
            return BoxEstadisticasSerializer
        return BoxSerializer
    
    def get_queryset(self):
        """Filtra el queryset basado en parámetros de query"""
        queryset = Box.objects.all()
        
        # Filtros opcionales via query params
        estado = self.request.query_params.get('estado', None)
        especialidad = self.request.query_params.get('especialidad', None)
        disponible = self.request.query_params.get('disponible', None)
        activo = self.request.query_params.get('activo', None)
        buscar = self.request.query_params.get('q', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if especialidad:
            queryset = queryset.filter(especialidad=especialidad)
        
        if disponible is not None:
            if disponible.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(estado='DISPONIBLE', activo=True)
            else:
                queryset = queryset.exclude(estado='DISPONIBLE')
        
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(activo=activo_bool)
        
        if buscar:
            queryset = queryset.filter(
                Q(numero__icontains=buscar) |
                Q(nombre__icontains=buscar)
            )
        
        return queryset.order_by('numero')
    
    @action(detail=True, methods=['post'])
    def ocupar(self, request, pk=None):
        """
        Marca el box como ocupado.
        
        POST /api/boxes/{id}/ocupar/
        Body (opcional): {"timestamp": "2025-01-01T10:00:00Z"}
        """
        box = self.get_object()
        serializer = BoxOcupacionSerializer(data=request.data)
        
        if serializer.is_valid():
            timestamp = serializer.validated_data.get('timestamp', None)
            
            if box.ocupar(timestamp):
                return Response({
                    'success': True,
                    'mensaje': f'Box {box.numero} ocupado exitosamente',
                    'estado': box.estado,
                    'ultima_ocupacion': box.ultima_ocupacion
                })
            
            return Response({
                'success': False,
                'mensaje': 'El box no está disponible para ser ocupado',
                'estado_actual': box.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def liberar(self, request, pk=None):
        """
        Libera el box.
        
        POST /api/boxes/{id}/liberar/
        Body (opcional): {"timestamp": "2025-01-01T10:30:00Z"}
        """
        box = self.get_object()
        serializer = BoxOcupacionSerializer(data=request.data)
        
        if serializer.is_valid():
            timestamp = serializer.validated_data.get('timestamp', None)
            
            if box.liberar(timestamp):
                return Response({
                    'success': True,
                    'mensaje': f'Box {box.numero} liberado exitosamente',
                    'estado': box.estado,
                    'ultima_liberacion': box.ultima_liberacion,
                    'tiempo_ocupado_total': str(box.tiempo_ocupado_hoy)
                })
            
            return Response({
                'success': False,
                'mensaje': 'El box no está ocupado',
                'estado_actual': box.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """
        Lista boxes disponibles.
        
        GET /api/boxes/disponibles/
        Query params opcionales: ?especialidad=CARDIOLOGIA
        """
        especialidad = request.query_params.get('especialidad', None)
        boxes = self.get_queryset().filter(estado='DISPONIBLE', activo=True)
        
        if especialidad:
            boxes = boxes.filter(
                Q(especialidad=especialidad) | Q(especialidad='MULTIUSO')
            )
        
        serializer = self.get_serializer(boxes, many=True)
        return Response({
            'count': boxes.count(),
            'boxes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def ocupados(self, request):
        """
        Lista boxes ocupados.
        
        GET /api/boxes/ocupados/
        """
        boxes = self.get_queryset().filter(estado='OCUPADO')
        serializer = self.get_serializer(boxes, many=True)
        return Response({
            'count': boxes.count(),
            'boxes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de boxes.
        
        GET /api/boxes/estadisticas/
        """
        queryset = self.get_queryset()
        
        # Estadísticas por estado
        total = queryset.count()
        disponibles = queryset.filter(estado='DISPONIBLE', activo=True).count()
        ocupados = queryset.filter(estado='OCUPADO').count()
        mantenimiento = queryset.filter(estado='MANTENIMIENTO').count()
        fuera_servicio = queryset.filter(estado='FUERA_SERVICIO').count()
        
        # Estadísticas por especialidad
        por_especialidad = {}
        for especialidad_key, especialidad_label in Box.ESPECIALIDAD_CHOICES:
            count = queryset.filter(especialidad=especialidad_key).count()
            disponibles_esp = queryset.filter(
                especialidad=especialidad_key,
                estado='DISPONIBLE',
                activo=True
            ).count()
            
            por_especialidad[especialidad_key] = {
                'label': especialidad_label,
                'total': count,
                'disponibles': disponibles_esp,
                'tasa_disponibilidad': round((disponibles_esp / count * 100) if count > 0 else 0, 2)
            }
        
        # Tasa de ocupación promedio
        boxes_activos = queryset.filter(activo=True)
        tasa_ocupacion_promedio = 0
        if boxes_activos.exists():
            tasas = [box.calcular_tiempo_ocupacion_hoy() for box in boxes_activos]
            tasa_ocupacion_promedio = sum(tasas) / len(tasas) if tasas else 0
        
        return Response({
            'total': total,
            'disponibles': disponibles,
            'ocupados': ocupados,
            'mantenimiento': mantenimiento,
            'fuera_servicio': fuera_servicio,
            'por_especialidad': por_especialidad,
            'tasa_ocupacion_promedio': round(tasa_ocupacion_promedio, 2),
            'porcentaje_disponibilidad': round((disponibles / total * 100) if total > 0 else 0, 2),
            'porcentaje_ocupacion': round((ocupados / total * 100) if total > 0 else 0, 2),
        })
    
    @action(detail=False, methods=['get'])
    def por_especialidad(self, request):
        """
        Agrupa boxes por especialidad.
        
        GET /api/boxes/por_especialidad/
        """
        queryset = self.get_queryset()
        
        resultado = {}
        for especialidad_key, especialidad_label in Box.ESPECIALIDAD_CHOICES:
            boxes = queryset.filter(especialidad=especialidad_key)
            resultado[especialidad_key] = {
                'label': especialidad_label,
                'total': boxes.count(),
                'disponibles': boxes.filter(estado='DISPONIBLE', activo=True).count(),
                'ocupados': boxes.filter(estado='OCUPADO').count(),
                'boxes': BoxListSerializer(boxes, many=True).data
            }
        
        return Response(resultado)
    
    @action(detail=True, methods=['post'])
    def mantenimiento(self, request, pk=None):
        """
        Marca el box en mantenimiento.
        
        POST /api/boxes/{id}/mantenimiento/
        Body (opcional): {"motivo": "Reparación de equipamiento"}
        """
        box = self.get_object()
        motivo = request.data.get('motivo', 'Mantenimiento programado')
        
        box.estado = 'MANTENIMIENTO'
        box.save()
        
        return Response({
            'success': True,
            'mensaje': f'Box {box.numero} marcado en mantenimiento',
            'estado': box.estado,
            'motivo': motivo
        })
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa un box desactivado.
        
        POST /api/boxes/{id}/activar/
        """
        box = self.get_object()
        box.activo = True
        box.estado = 'DISPONIBLE'
        box.save()
        
        return Response({
            'success': True,
            'mensaje': f'Box {box.numero} activado',
            'activo': box.activo,
            'estado': box.estado
        })
    
    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        Desactiva un box.
        
        POST /api/boxes/{id}/desactivar/
        """
        box = self.get_object()
        box.activo = False
        box.estado = 'FUERA_SERVICIO'
        box.save()
        
        return Response({
            'success': True,
            'mensaje': f'Box {box.numero} desactivado',
            'activo': box.activo,
            'estado': box.estado
        })
    
    @action(detail=False, methods=['post'])
    def reset_ocupacion(self, request):
        """
        Resetea los contadores de ocupación diaria de todos los boxes.
        Típicamente ejecutado a medianoche mediante tarea programada.
        
        POST /api/boxes/reset_ocupacion/
        """
        boxes = self.get_queryset()
        count = 0
        
        for box in boxes:
            box.reset_tiempo_ocupado_diario()
            count += 1
        
        return Response({
            'success': True,
            'mensaje': f'Contadores de ocupación reseteados para {count} boxes',
            'boxes_afectados': count
        })
    
    @action(detail=True, methods=['get'])
    def historial_ocupacion(self, request, pk=None):
        """
        Obtiene el historial de ocupación del box.
        
        GET /api/boxes/{id}/historial_ocupacion/
        """
        box = self.get_object()
        
        return Response({
            'box': BoxListSerializer(box).data,
            'tiempo_ocupado_hoy': str(box.tiempo_ocupado_hoy),
            'porcentaje_ocupacion': box.calcular_tiempo_ocupacion_hoy(),
            'ultima_ocupacion': box.ultima_ocupacion,
            'ultima_liberacion': box.ultima_liberacion,
            'ocupacion_actual': box.obtener_ocupacion_actual()
        })
        
        # backend/boxes/viewsets.py - AGREGAR AL FINAL DE LA CLASE BoxViewSet

    @action(detail=False, methods=['get'])
    def sincronizar_estados(self, request):
        """
        Sincroniza los estados de los boxes con las atenciones programadas.
        Marca como ocupados los boxes que tienen atenciones en curso.
        
        GET /api/boxes/sincronizar_estados/
        """
        from django.utils import timezone
        from atenciones.models import Atencion
        
        ahora = timezone.now()
        boxes_actualizados = 0
        
        # Obtener todas las atenciones que deberían estar en curso
        atenciones_activas = Atencion.objects.filter(
            estado__in=['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO'],
            fecha_hora_inicio__lte=ahora,
        ).select_related('box')
        
        boxes_ocupados = set()
        
        for atencion in atenciones_activas:
            tiempo_transcurrido = (ahora - atencion.fecha_hora_inicio).total_seconds() / 60
            
            # Si la atención está dentro de su tiempo planificado
            if tiempo_transcurrido <= atencion.duracion_planificada + 15:
                boxes_ocupados.add(atencion.box.id)
                
                # Marcar box como ocupado si no lo está
                if atencion.box.estado != 'OCUPADO':
                    atencion.box.estado = 'OCUPADO'
                    atencion.box.ultima_ocupacion = atencion.fecha_hora_inicio
                    atencion.box.save()
                    boxes_actualizados += 1
                
                # Si la atención está programada, iniciarla automáticamente
                if atencion.estado == 'PROGRAMADA':
                    atencion.iniciar_cronometro()
        
        # Liberar boxes que no tienen atenciones activas
        boxes_a_liberar = self.get_queryset().filter(
            estado='OCUPADO'
        ).exclude(id__in=boxes_ocupados)
        
        for box in boxes_a_liberar:
            box.liberar()
            boxes_actualizados += 1
        
        return Response({
            'success': True,
            'boxes_actualizados': boxes_actualizados,
            'boxes_ocupados': len(boxes_ocupados),
            'timestamp': ahora
        })

