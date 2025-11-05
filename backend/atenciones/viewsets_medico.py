# backend/atenciones/viewsets_medico.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Atencion
from .serializers import AtencionSerializer


class MedicoAtencionesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para que los médicos gestionen sus propias atenciones.
    Solo muestra las atenciones asignadas al médico autenticado.
    
    Endpoints disponibles:
    - GET /api/medico/atenciones/ - Lista atenciones del médico
    - GET /api/medico/atenciones/{id}/ - Detalle de una atención
    - GET /api/medico/atenciones/hoy/ - Atenciones de hoy
    - GET /api/medico/atenciones/proximas/ - Próximas atenciones
    - GET /api/medico/atenciones/actual/ - Atención en curso o próxima
    - POST /api/medico/atenciones/{id}/iniciar/ - Iniciar atención
    - POST /api/medico/atenciones/{id}/finalizar/ - Finalizar atención
    - POST /api/medico/atenciones/{id}/no_se_presento/ - Marcar no presentado
    """
    
    serializer_class = AtencionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Retorna solo las atenciones del médico autenticado.
        """
        user = self.request.user
        
        # Verificar que el usuario tenga rol MEDICO
        if user.rol != 'MEDICO':
            return Atencion.objects.none()
        
        return Atencion.objects.filter(
            medico=user
        ).select_related('paciente', 'box').order_by('fecha_hora_inicio')
    
    def list(self, request, *args, **kwargs):
        """
        Lista atenciones con filtros opcionales.
        """
        queryset = self.get_queryset()
        
        # Filtros opcionales
        estado = request.query_params.get('estado', None)
        fecha = request.query_params.get('fecha', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if fecha:
            queryset = queryset.filter(fecha_hora_inicio__date=fecha)
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'count': queryset.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def hoy(self, request):
        """
        Retorna las atenciones del médico para el día actual.
        ✅ CORREGIDO: Usa timezone.localtime para manejar correctamente la zona horaria
        """
        from django.utils import timezone
        
        # Obtener la fecha actual en la zona horaria local configurada
        ahora_local = timezone.localtime(timezone.now())
        hoy = ahora_local.date()
        
        print(f"\n🔍 DEBUG HOY:")
        print(f"   Ahora UTC: {timezone.now()}")
        print(f"   Ahora Local: {ahora_local}")
        print(f"   Fecha HOY: {hoy}")
        print(f"   Usuario: {request.user.username}")
        
        # Filtrar atenciones del día
        atenciones = self.get_queryset().filter(
            fecha_hora_inicio__date=hoy
        ).order_by('fecha_hora_inicio')
        
        print(f"   Atenciones encontradas: {atenciones.count()}")
        for a in atenciones:
            print(f"      - {a.id}: {timezone.localtime(a.fecha_hora_inicio)} | {a.paciente.identificador_hash[:8]}")
        
        serializer = self.get_serializer(atenciones, many=True)
        
        # Calcular estadísticas del día
        total = atenciones.count()
        completadas = atenciones.filter(estado='COMPLETADA').count()
        en_curso = atenciones.filter(estado='EN_CURSO').count()
        pendientes = atenciones.filter(estado__in=['PROGRAMADA', 'EN_ESPERA']).count()
        
        return Response({
            'fecha': hoy,
            'total': total,
            'completadas': completadas,
            'en_curso': en_curso,
            'pendientes': pendientes,
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def proximas(self, request):
        """
        Retorna las próximas atenciones del médico.
        
        GET /api/medico/atenciones/proximas/
        Query params:
        - limite: Número máximo de atenciones a retornar (default: 5)
        """
        limite = int(request.query_params.get('limite', 5))
        ahora = timezone.now()
        
        atenciones = self.get_queryset().filter(
            fecha_hora_inicio__gte=ahora,
            estado__in=['PROGRAMADA', 'EN_ESPERA']
        ).order_by('fecha_hora_inicio')[:limite]
        
        serializer = self.get_serializer(atenciones, many=True)
        
        return Response({
            'count': atenciones.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def actual(self, request):
        """
        Retorna la atención actual (en curso) o la próxima atención.
        Esta es la vista principal para el cronómetro del médico.
        
        GET /api/medico/atenciones/actual/
        """
        ahora = timezone.now()
        
        # Primero buscar si hay una atención en curso
        atencion_en_curso = self.get_queryset().filter(
            estado='EN_CURSO'
        ).first()
        
        if atencion_en_curso:
            serializer = self.get_serializer(atencion_en_curso)
            return Response({
                'tipo': 'en_curso',
                'atencion': serializer.data,
                'mensaje': 'Tienes una atención en curso'
            })
        
        # Si no hay atención en curso, buscar la próxima
        proxima_atencion = self.get_queryset().filter(
            fecha_hora_inicio__gte=ahora,
            estado__in=['PROGRAMADA', 'EN_ESPERA']
        ).order_by('fecha_hora_inicio').first()
        
        if proxima_atencion:
            # Calcular tiempo hasta el inicio
            tiempo_hasta_inicio = proxima_atencion.fecha_hora_inicio - ahora
            minutos_hasta_inicio = int(tiempo_hasta_inicio.total_seconds() / 60)
            
            # Determinar si puede iniciar (está dentro de los 15 minutos antes)
            puede_iniciar = minutos_hasta_inicio <= 15
            
            serializer = self.get_serializer(proxima_atencion)
            return Response({
                'tipo': 'proxima',
                'atencion': serializer.data,
                'minutos_hasta_inicio': minutos_hasta_inicio,
                'puede_iniciar': puede_iniciar,
                'mensaje': f'Tu próxima atención es en {minutos_hasta_inicio} minutos'
            })
        
        # No hay atenciones
        return Response({
            'tipo': 'ninguna',
            'atencion': None,
            'mensaje': 'No tienes atenciones programadas'
        })
    
    @action(detail=True, methods=['post'])
    def iniciar(self, request, pk=None):
        """
        Inicia el cronómetro de una atención.
        
        POST /api/medico/atenciones/{id}/iniciar/
        """
        atencion = self.get_object()
        
        # Verificar que puede iniciar
        if not atencion.puede_iniciar():
            return Response({
                'success': False,
                'error': f'No se puede iniciar esta atención. Estado actual: {atencion.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que no tenga otra atención en curso
        otra_en_curso = self.get_queryset().filter(estado='EN_CURSO').exists()
        if otra_en_curso:
            return Response({
                'success': False,
                'error': 'Ya tienes una atención en curso. Debes finalizarla primero.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Iniciar cronómetro (usa la función existente que NO modificamos)
        if atencion.iniciar_cronometro():
            serializer = self.get_serializer(atencion)
            return Response({
                'success': True,
                'mensaje': 'Atención iniciada correctamente',
                'atencion': serializer.data,
                'box_ocupado': atencion.box.estado == 'OCUPADO'
            })
        
        return Response({
            'success': False,
            'error': 'No se pudo iniciar la atención'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """
        Finaliza el cronómetro de una atención.
        
        POST /api/medico/atenciones/{id}/finalizar/
        Body (opcional):
        {
            "observaciones": "Observaciones finales de la atención"
        }
        """
        atencion = self.get_object()
        
        # Verificar que puede finalizar
        if not atencion.puede_finalizar():
            return Response({
                'success': False,
                'error': f'No se puede finalizar esta atención. Estado actual: {atencion.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Agregar observaciones si se proporcionaron
        observaciones = request.data.get('observaciones', '')
        if observaciones:
            atencion.observaciones += f"\n\nObservaciones finales: {observaciones}"
            atencion.save()
        
        # Finalizar cronómetro (usa la función existente que NO modificamos)
        if atencion.finalizar_cronometro():
            serializer = self.get_serializer(atencion)
            return Response({
                'success': True,
                'mensaje': 'Atención finalizada correctamente',
                'atencion': serializer.data,
                'duracion_real': atencion.duracion_real,
                'box_liberado': atencion.box.estado == 'DISPONIBLE'
            })
        
        return Response({
            'success': False,
            'error': 'No se pudo finalizar la atención'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def no_se_presento(self, request, pk=None):
        """
        Marca que el paciente no se presentó a la atención.
        
        POST /api/medico/atenciones/{id}/no_se_presento/
        Body (opcional):
        {
            "observaciones": "Motivo o detalles adicionales"
        }
        """
        atencion = self.get_object()
        
        # Verificar que la atención no esté completada
        if atencion.estado in ['COMPLETADA', 'CANCELADA', 'NO_PRESENTADO']:
            return Response({
                'success': False,
                'error': f'Esta atención ya está en estado: {atencion.get_estado_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Agregar observaciones
        observaciones = request.data.get('observaciones', 'Paciente no se presentó')
        atencion.observaciones += f"\n\n{observaciones}"
        
        # Marcar como no presentado (usa la nueva función)
        if atencion.marcar_no_presentado():
            serializer = self.get_serializer(atencion)
            return Response({
                'success': True,
                'mensaje': 'Paciente marcado como no presentado',
                'atencion': serializer.data,
                'box_liberado': atencion.box.estado == 'DISPONIBLE'
            })
        
        return Response({
            'success': False,
            'error': 'No se pudo marcar como no presentado'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Estadísticas de las atenciones del médico.
        
        GET /api/medico/atenciones/estadisticas/
        Query params:
        - periodo: Número de días a considerar (default: 30)
        """
        periodo = int(request.query_params.get('periodo', 30))
        fecha_desde = timezone.now() - timezone.timedelta(days=periodo)
        
        atenciones = self.get_queryset().filter(fecha_hora_inicio__gte=fecha_desde)
        
        # Estadísticas por estado
        total = atenciones.count()
        completadas = atenciones.filter(estado='COMPLETADA').count()
        canceladas = atenciones.filter(estado='CANCELADA').count()
        no_presentados = atenciones.filter(estado='NO_PRESENTADO').count()
        
        # Tiempo promedio
        atenciones_completadas = atenciones.filter(
            estado='COMPLETADA',
            duracion_real__isnull=False
        )
        
        tiempo_promedio = 0
        if atenciones_completadas.exists():
            from django.db.models import Avg
            tiempo_promedio = atenciones_completadas.aggregate(
                promedio=Avg('duracion_real')
            )['promedio'] or 0
        
        return Response({
            'periodo_dias': periodo,
            'total_atenciones': total,
            'completadas': completadas,
            'canceladas': canceladas,
            'no_presentados': no_presentados,
            'tiempo_promedio_minutos': round(tiempo_promedio, 1),
            'tasa_completado': round((completadas / total * 100) if total > 0 else 0, 1),
        })