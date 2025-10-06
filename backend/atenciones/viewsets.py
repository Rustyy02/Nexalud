# atenciones/viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Medico, Atencion
from .serializers import (
    MedicoSerializer,
    AtencionSerializer,
    AtencionListSerializer
)


class MedicoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar médicos"""
    queryset = Medico.objects.all()
    serializer_class = MedicoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Medico.objects.all()
        
        activo = self.request.query_params.get('activo', None)
        especialidad = self.request.query_params.get('especialidad', None)
        
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1']
            queryset = queryset.filter(activo=activo_bool)
        
        if especialidad:
            queryset = queryset.filter(especialidad_principal=especialidad)
        
        return queryset.order_by('apellido', 'nombre')
    
    @action(detail=True, methods=['get'])
    def atenciones_hoy(self, request, pk=None):
        """Obtiene atenciones del médico para hoy"""
        medico = self.get_object()
        atenciones = medico.obtener_atenciones_dia()
        
        from .serializers import AtencionListSerializer
        serializer = AtencionListSerializer(atenciones, many=True)
        
        return Response(serializer.data)


class AtencionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar atenciones (con cronómetro)"""
    queryset = Atencion.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AtencionListSerializer
        return AtencionSerializer
    
    def get_queryset(self):
        queryset = Atencion.objects.select_related('paciente', 'medico', 'box')
        
        # Filtros
        estado = self.request.query_params.get('estado', None)
        medico_id = self.request.query_params.get('medico', None)
        box_id = self.request.query_params.get('box', None)
        fecha = self.request.query_params.get('fecha', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if medico_id:
            queryset = queryset.filter(medico_id=medico_id)
        
        if box_id:
            queryset = queryset.filter(box_id=box_id)
        
        if fecha:
            queryset = queryset.filter(fecha_hora_inicio__date=fecha)
        
        return queryset.order_by('-fecha_hora_inicio')
    
    @action(detail=True, methods=['post'])
    def iniciar_cronometro(self, request, pk=None):
        """Inicia el cronómetro de la atención"""
        atencion = self.get_object()
        
        if atencion.iniciar_cronometro():
            return Response({
                'success': True,
                'mensaje': 'Cronómetro iniciado',
                'inicio_cronometro': atencion.inicio_cronometro,
                'estado': atencion.estado
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo iniciar el cronómetro'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def finalizar_cronometro(self, request, pk=None):
        """Finaliza el cronómetro de la atención"""
        atencion = self.get_object()
        
        if atencion.finalizar_cronometro():
            return Response({
                'success': True,
                'mensaje': 'Cronómetro finalizado',
                'fin_cronometro': atencion.fin_cronometro,
                'duracion_real': atencion.duracion_real,
                'estado': atencion.estado
            })
        
        return Response({
            'success': False,
            'mensaje': 'No se pudo finalizar el cronómetro'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def en_curso(self, request):
        """Lista atenciones actualmente en curso"""
        atenciones = self.get_queryset().filter(estado='EN_CURSO')
        serializer = self.get_serializer(atenciones, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hoy(self, request):
        """Lista atenciones del día actual"""
        hoy = timezone.now().date()
        atenciones = self.get_queryset().filter(fecha_hora_inicio__date=hoy)
        serializer = self.get_serializer(atenciones, many=True)
        return Response(serializer.data)