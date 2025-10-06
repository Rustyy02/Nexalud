from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Paciente
from .serializers import (
    PacienteSerializer,
    PacienteListSerializer,
    PacienteCreateUpdateSerializer,
    PacienteEstadoSerializer
)


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pacientes.
    
    Endpoints disponibles:
    - GET /api/pacientes/ - Lista todos los pacientes
    - POST /api/pacientes/ - Crea un nuevo paciente
    - GET /api/pacientes/{id}/ - Detalle de un paciente
    - PUT /api/pacientes/{id}/ - Actualiza un paciente completo
    - PATCH /api/pacientes/{id}/ - Actualiza parcialmente un paciente
    - DELETE /api/pacientes/{id}/ - Elimina un paciente
    
    Acciones personalizadas:
    - POST /api/pacientes/{id}/cambiar_estado/ - Cambia el estado del paciente
    - GET /api/pacientes/activos/ - Lista solo pacientes activos
    - GET /api/pacientes/en_espera/ - Lista pacientes en espera
    - GET /api/pacientes/estadisticas/ - Estadísticas generales
    """
    queryset = Paciente.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción.
        """
        if self.action == 'list':
            return PacienteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PacienteCreateUpdateSerializer
        elif self.action == 'cambiar_estado':
            return PacienteEstadoSerializer
        return PacienteSerializer
    
    def get_queryset(self):
        """
        Filtra el queryset basado en parámetros de query.
        """
        queryset = Paciente.objects.all()
        
        # Filtros opcionales via query params
        estado = self.request.query_params.get('estado', None)
        urgencia = self.request.query_params.get('urgencia', None)
        activo = self.request.query_params.get('activo', None)
        buscar = self.request.query_params.get('q', None)
        
        if estado:
            queryset = queryset.filter(estado_actual=estado)
        
        if urgencia:
            queryset = queryset.filter(nivel_urgencia=urgencia)
        
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(activo=activo_bool)
        
        if buscar:
            queryset = queryset.filter(
                Q(identificador_hash__icontains=buscar)
            )
        
        return queryset.select_related().order_by('-fecha_ingreso')
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Endpoint personalizado para cambiar el estado de un paciente.
        
        POST /api/pacientes/{id}/cambiar_estado/
        Body: {"estado_actual": "EN_CONSULTA"}
        """
        paciente = self.get_object()
        serializer = PacienteEstadoSerializer(data=request.data)
        
        if serializer.is_valid():
            nuevo_estado = serializer.validated_data['estado_actual']
            if paciente.actualizar_estado(nuevo_estado):
                return Response({
                    'success': True,
                    'mensaje': f'Estado actualizado a {paciente.get_estado_actual_display()}',
                    'estado_actual': paciente.estado_actual
                })
            else:
                return Response({
                    'success': False,
                    'mensaje': 'No se pudo actualizar el estado'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        Lista solo pacientes activos.
        
        GET /api/pacientes/activos/
        """
        pacientes = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(pacientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_espera(self, request):
        """
        Lista pacientes que están en espera.
        
        GET /api/pacientes/en_espera/
        """
        pacientes = self.get_queryset().filter(
            estado_actual='EN_ESPERA',
            activo=True
        )
        serializer = self.get_serializer(pacientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas generales de pacientes.
        
        GET /api/pacientes/estadisticas/
        """
        queryset = self.get_queryset()
        
        # Contar por estado
        estados = {}
        for estado_key, estado_label in Paciente.ESTADO_CHOICES:
            count = queryset.filter(estado_actual=estado_key).count()
            estados[estado_key] = {
                'label': estado_label,
                'count': count
            }
        
        # Contar por urgencia
        urgencias = {}
        for urgencia_key, urgencia_label in Paciente.URGENCIA_CHOICES:
            count = queryset.filter(nivel_urgencia=urgencia_key).count()
            urgencias[urgencia_key] = {
                'label': urgencia_label,
                'count': count
            }
        
        return Response({
            'total': queryset.count(),
            'activos': queryset.filter(activo=True).count(),
            'inactivos': queryset.filter(activo=False).count(),
            'por_estado': estados,
            'por_urgencia': urgencias,
        })
    
    @action(detail=True, methods=['get'])
    def rutas_clinicas(self, request, pk=None):
        """
        Obtiene las rutas clínicas del paciente.
        
        GET /api/pacientes/{id}/rutas_clinicas/
        """
        paciente = self.get_object()
        rutas = paciente.rutas_clinicas.all()
        
        # Importación lazy para evitar circular imports
        from rutas_clinicas.serializers import RutaClinicaListSerializer
        serializer = RutaClinicaListSerializer(rutas, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def atenciones(self, request, pk=None):
        """
        Obtiene las atenciones del paciente.
        
        GET /api/pacientes/{id}/atenciones/
        """
        paciente = self.get_object()
        atenciones = paciente.atenciones.all()
        
        # Importación lazy para evitar circular imports
        from atenciones.serializers import AtencionListSerializer
        serializer = AtencionListSerializer(atenciones, many=True)
        
        return Response(serializer.data)