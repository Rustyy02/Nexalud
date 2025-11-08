# Agregar estos endpoints a tu archivo views.py existente

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Atencion
from .serializers import AtencionSerializer

# Agregar este método a tu ViewSet de Atencion existente

@action(detail=True, methods=['post'], url_path='reportar-atraso')
def reportar_atraso(self, request, pk=None):
    """
    Reporta un atraso del paciente.
    Inicia un timer de 5 minutos.
    Si no llega en 5 minutos, se marca automáticamente como NO_PRESENTADO.
    """
    atencion = self.get_object()
    
    # Validar que la atención esté EN_CURSO
    if atencion.estado != 'EN_CURSO':
        return Response(
            {'error': 'Solo se puede reportar atraso cuando la atención está EN_CURSO'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que no se haya reportado ya
    if atencion.atraso_reportado:
        return Response(
            {'error': 'El atraso ya fue reportado anteriormente'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    motivo = request.data.get('motivo', '')
    
    if atencion.reportar_atraso(motivo):
        serializer = AtencionSerializer(atencion)
        return Response({
            'message': 'Atraso reportado. El paciente tiene 5 minutos para llegar.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(
        {'error': 'No se pudo reportar el atraso'},
        status=status.HTTP_400_BAD_REQUEST
    )


@action(detail=True, methods=['post'], url_path='verificar-atraso')
def verificar_atraso(self, request, pk=None):
    """
    Verifica si han pasado 5 minutos desde el reporte de atraso.
    Si es así, marca automáticamente como NO_PRESENTADO.
    """
    atencion = self.get_object()
    
    if not atencion.atraso_reportado:
        return Response(
            {'message': 'No hay atraso reportado'},
            status=status.HTTP_200_OK
        )
    
    if atencion.verificar_tiempo_atraso():
        # Han pasado 5 minutos, marcar como NO_PRESENTADO
        if atencion.marcar_no_presentado():
            serializer = AtencionSerializer(atencion)
            return Response({
                'message': 'Atención marcada como NO_PRESENTADO',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
    
    serializer = AtencionSerializer(atencion)
    return Response({
        'message': 'Aún dentro del tiempo de espera',
        'data': serializer.data
    }, status=status.HTTP_200_OK)


@action(detail=True, methods=['post'], url_path='iniciar-consulta')
def iniciar_consulta(self, request, pk=None):
    """
    El paciente llegó después de reportar atraso.
    Cancela el timer de atraso y permite continuar la consulta normalmente.
    """
    atencion = self.get_object()
    
    if atencion.estado != 'EN_CURSO':
        return Response(
            {'error': 'La atención no está EN_CURSO'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not atencion.atraso_reportado:
        return Response(
            {'error': 'No hay atraso reportado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar que no hayan pasado 5 minutos
    if atencion.verificar_tiempo_atraso():
        return Response(
            {'error': 'El tiempo de espera ha expirado. La atención debe marcarse como NO_PRESENTADO'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Limpiar el reporte de atraso
    atencion.atraso_reportado = False
    atencion.fecha_reporte_atraso = None
    atencion.motivo_atraso = "Paciente llegó con retraso pero dentro del tiempo de tolerancia"
    atencion.save()
    
    serializer = AtencionSerializer(atencion)
    return Response({
        'message': 'Consulta iniciada correctamente',
        'data': serializer.data
    }, status=status.HTTP_200_OK)