from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Box
from .serializers import BoxSerializer, BoxListSerializer

class BoxViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar boxes"""
    queryset = Box.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BoxListSerializer
        return BoxSerializer
    
    def get_queryset(self):
        queryset = Box.objects.all()
        
        # Filtros
        estado = self.request.query_params.get('estado', None)
        especialidad = self.request.query_params.get('especialidad', None)
        disponible = self.request.query_params.get('disponible', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if especialidad:
            queryset = queryset.filter(especialidad=especialidad)
        
        if disponible is not None:
            if disponible.lower() in ['true', '1']:
                queryset = queryset.filter(estado='DISPONIBLE', activo=True)
        
        return queryset.order_by('numero')
    
    @action(detail=True, methods=['post'])
    def ocupar(self, request, pk=None):
        """Marca el box como ocupado"""
        box = self.get_object()
        
        if box.ocupar():
            return Response({
                'success': True,
                'mensaje': f'Box {box.numero} ocupado',
                'estado': box.estado
            })
        
        return Response({
            'success': False,
            'mensaje': 'El box no está disponible'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def liberar(self, request, pk=None):
        """Libera el box"""
        box = self.get_object()
        
        if box.liberar():
            return Response({
                'success': True,
                'mensaje': f'Box {box.numero} liberado',
                'estado': box.estado
            })
        
        return Response({
            'success': False,
            'mensaje': 'El box no está ocupado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def disponibles(self, request):
        """Lista boxes disponibles"""
        boxes = self.get_queryset().filter(estado='DISPONIBLE', activo=True)
        serializer = self.get_serializer(boxes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de boxes"""
        queryset = self.get_queryset()
        
        return Response({
            'total': queryset.count(),
            'disponibles': queryset.filter(estado='DISPONIBLE', activo=True).count(),
            'ocupados': queryset.filter(estado='OCUPADO').count(),
            'mantenimiento': queryset.filter(estado='MANTENIMIENTO').count(),
            'fuera_servicio': queryset.filter(estado='FUERA_SERVICIO').count(),
        })
