from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count
from django.utils import timezone
from .models import Box, OcupacionManual
from datetime import timedelta
from .serializers import (
    BoxSerializer,
    BoxListSerializer,
    BoxCreateUpdateSerializer,
    BoxEstadisticasSerializer,
    BoxOcupacionSerializer
)

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
    - GET /api/boxes/sincronizar_estados/ - Sincroniza estados con atenciones
    - GET/POST /api/boxes/verificar_y_liberar/ - Verifica y libera boxes según atenciones
    - GET /api/boxes/estado_detallado/ - Estado detallado de boxes y atenciones
    - GET/POST /api/boxes/liberar_ocupaciones_manuales/ - Libera ocupaciones manuales expiradas
    """
    queryset = Box.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # Retorna el serializer apropiado según la acción
        if self.action == 'list':
            return BoxSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BoxCreateUpdateSerializer
        elif self.action in ['ocupar', 'liberar']:
            return BoxOcupacionSerializer
        elif self.action == 'estadisticas':
            return BoxEstadisticasSerializer
        return BoxSerializer
    
    def get_queryset(self):
        # Filtra el queryset basado en parámetros de query
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
        
        #Marca el box como ocupado manualmente.
        #POST /api/boxes/{id}/ocupar/
        
        box = self.get_object()
        
        # Obtener duración y motivo
        duracion_minutos = request.data.get('duracion_minutos', 30)
        motivo = request.data.get('motivo', 'Ocupación manual')
        
        # Validar duración - CONVERTIR A INT PRIMERO
        try:
            duracion_minutos = int(duracion_minutos)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'La duración debe ser un número válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        duraciones_validas = [15, 30, 45, 60, 75, 90, 105, 120]
        if duracion_minutos not in duraciones_validas:
            return Response({
                'success': False,
                'error': f'Duración no válida. Debe ser una de: {duraciones_validas}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el box esté disponible
        if box.estado != 'DISPONIBLE':
            return Response({
                'success': False,
                'mensaje': 'El box no está disponible para ser ocupado',
                'estado_actual': box.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ocupar el box
        ahora = timezone.now()
        if box.ocupar(ahora):
            # Crear registro de ocupación manual
            fecha_fin = ahora + timedelta(minutes=duracion_minutos)
            
            ocupacion = OcupacionManual.objects.create(
                box=box,
                duracion_minutos=duracion_minutos,
                fecha_inicio=ahora,
                fecha_fin_programada=fecha_fin,
                motivo=motivo,
                activa=True
            )
            
            return Response({
                'success': True,
                'mensaje': f'Box {box.numero} ocupado exitosamente',
                'ocupacion': {
                    'id': str(ocupacion.id),
                    'duracion_minutos': duracion_minutos,
                    'fecha_inicio': ocupacion.fecha_inicio,
                    'fecha_fin_programada': ocupacion.fecha_fin_programada,
                    'motivo': motivo,
                },
                'estado': box.estado,
                'ultima_ocupacion': box.ultima_ocupacion
            })
        
        return Response({
            'success': False,
            'mensaje': 'El box no está disponible para ser ocupado',
            'estado_actual': box.estado
        }, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=True, methods=['post'])
    def liberar(self, request, pk=None):
        
        #Libera el box SOLO si no tiene una ocupación manual activa.
        #POST /api/boxes/{id}/liberar/
        
        box = self.get_object()
        
        # Verificar si hay una ocupación manual activa
        ocupacion_activa = OcupacionManual.objects.filter(
            box=box,
            activa=True
        ).first()
        
        if ocupacion_activa:
            return Response({
                'success': False,
                'mensaje': f'El box tiene una ocupación manual activa hasta {ocupacion_activa.fecha_fin_programada}',
                'ocupacion': {
                    'duracion_minutos': ocupacion_activa.duracion_minutos,
                    'motivo': ocupacion_activa.motivo,
                    'fecha_fin_programada': ocupacion_activa.fecha_fin_programada,
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        #Lista todos los boxes disponibles.
        #GET /api/boxes/disponibles/
        
        boxes_disponibles = self.get_queryset().filter(
            estado='DISPONIBLE',
            activo=True
        )
        serializer = BoxListSerializer(boxes_disponibles, many=True)
        return Response({
            'count': boxes_disponibles.count(),
            'boxes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def ocupados(self, request):
        
        #Lista todos los boxes ocupados.
        #GET /api/boxes/ocupados/
        
        boxes_ocupados = self.get_queryset().filter(estado='OCUPADO')
        serializer = BoxListSerializer(boxes_ocupados, many=True)
        return Response({
            'count': boxes_ocupados.count(),
            'boxes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        
        #Retorna estadísticas generales de los boxes.
        #GET /api/boxes/estadisticas/

        queryset = self.get_queryset()
        
        total = queryset.count()
        disponibles = queryset.filter(estado='DISPONIBLE', activo=True).count()
        ocupados = queryset.filter(estado='OCUPADO').count()
        mantenimiento = queryset.filter(estado='MANTENIMIENTO').count()
        fuera_servicio = queryset.filter(estado='FUERA_SERVICIO').count()
        
        # Conteo por especialidad
        por_especialidad = {}
        for choice in Box.ESPECIALIDAD_CHOICES:
            codigo, nombre = choice
            count = queryset.filter(especialidad=codigo).count()
            if count > 0:
                por_especialidad[nombre] = count
        
        # Tasa de ocupación promedio
        boxes_activos = queryset.filter(activo=True)
        if boxes_activos.exists():
            tasa_ocupacion_promedio = sum(
                box.calcular_tiempo_ocupacion_hoy() for box in boxes_activos
            ) / boxes_activos.count()
        else:
            tasa_ocupacion_promedio = 0
        
        data = {
            'total': total,
            'disponibles': disponibles,
            'ocupados': ocupados,
            'mantenimiento': mantenimiento,
            'fuera_servicio': fuera_servicio,
            'por_especialidad': por_especialidad,
            'tasa_ocupacion_promedio': round(tasa_ocupacion_promedio, 2)
        }
        
        serializer = BoxEstadisticasSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def por_especialidad(self, request):
        
        # Agrupa los boxes por especialidad.
        # GET /api/boxes/por_especialidad/
        
        especialidad = request.query_params.get('especialidad', None)
        
        if especialidad:
            boxes = self.get_queryset().filter(especialidad=especialidad)
            serializer = BoxListSerializer(boxes, many=True)
            return Response({
                'especialidad': especialidad,
                'count': boxes.count(),
                'boxes': serializer.data
            })
        
        # Si no se especifica, retornar todas las especialidades
        result = {}
        for choice in Box.ESPECIALIDAD_CHOICES:
            codigo, nombre = choice
            boxes = self.get_queryset().filter(especialidad=codigo)
            if boxes.exists():
                result[nombre] = {
                    'codigo': codigo,
                    'count': boxes.count(),
                    'boxes': BoxListSerializer(boxes, many=True).data
                }
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def mantenimiento(self, request, pk=None):
        
        # Marca el box en mantenimiento.
        # POST /api/boxes/{id}/mantenimiento/
        
        box = self.get_object()
        box.estado = 'MANTENIMIENTO'
        box.save()
        
        return Response({
            'success': True,
            'mensaje': f'Box {box.numero} marcado en mantenimiento',
            'estado': box.estado
        })
    
    @action(detail=False, methods=['post'])
    def reset_ocupacion(self, request):
        
        # Resetea los contadores de ocupación diaria de todos los boxes.
        # Se ejecutaría típicamente a medianoche.
        # POST /api/boxes/reset_ocupacion/
        
        boxes = self.get_queryset()
        count = 0
        
        for box in boxes:
            box.reset_tiempo_ocupado_diario()
            count += 1
        
        return Response({
            'success': True,
            'mensaje': f'Contadores reseteados para {count} boxes',
            'boxes_actualizados': count
        })

    @action(detail=False, methods=['get'])
    def sincronizar_estados(self, request):
        
        # Sincroniza los estados de los boxes con las atenciones programadas.
        # RESPETA ocupaciones manuales activas y NO las libera.
        # También finaliza atenciones que han excedido su duración.
        # GET /api/boxes/sincronizar_estados/
        
        ahora = timezone.now()
        boxes_actualizados = 0
        atenciones_finalizadas = 0
        
        try:
            from atenciones.models import Atencion
            
            # Obtener todas las atenciones activas
            atenciones_activas = Atencion.objects.filter(
                estado__in=['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO'],
                fecha_hora_inicio__lte=ahora,
            ).select_related('box')
            
            boxes_ocupados_por_atencion = set()
            
            for atencion in atenciones_activas:
                # Calcular tiempo transcurrido desde el inicio programado
                tiempo_desde_inicio = (ahora - atencion.fecha_hora_inicio).total_seconds() / 60
                
                # Si la atención está en curso, usar el cronómetro
                if atencion.estado == 'EN_CURSO' and atencion.inicio_cronometro:
                    tiempo_transcurrido = (ahora - atencion.inicio_cronometro).total_seconds() / 60
                    
                    # Si ha excedido la duración planificada, finalizarla
                    if tiempo_transcurrido >= atencion.duracion_planificada:
                        resultado = atencion.finalizar_cronometro()
                        if resultado:
                            atenciones_finalizadas += 1
                            boxes_actualizados += 1
                        continue  # No mantener el box ocupado si finalizamos la atención
                
                # Si la atención está dentro de su tiempo planificado (con margen de 15 min)
                if tiempo_desde_inicio <= atencion.duracion_planificada + 15:
                    boxes_ocupados_por_atencion.add(atencion.box.id)
                    
                    # Marcar box como ocupado si no lo está
                    if atencion.box.estado != 'OCUPADO':
                        atencion.box.estado = 'OCUPADO'
                        atencion.box.ultima_ocupacion = atencion.fecha_hora_inicio
                        atencion.box.save()
                        boxes_actualizados += 1
                    
                    # Si la atención está programada, iniciarla automáticamente
                    if atencion.estado == 'PROGRAMADA':
                        atencion.iniciar_cronometro()
                else:
                    # La atención excedió el tiempo con margen, finalizarla si está en curso
                    if atencion.estado == 'EN_CURSO':
                        resultado = atencion.finalizar_cronometro()
                        if resultado:
                            atenciones_finalizadas += 1
                            boxes_actualizados += 1
            
            # Obtener boxes con ocupaciones manuales activas
            ocupaciones_manuales = OcupacionManual.objects.filter(
                activa=True,
                fecha_fin_programada__gt=ahora  # Que aún no hayan expirado
            ).select_related('box')
            
            boxes_con_ocupacion_manual = set(ocupacion.box.id for ocupacion in ocupaciones_manuales)
            
            # Liberar SOLO boxes que:
            # 1. NO tienen atenciones activas
            # 2. NO tienen ocupaciones manuales activas
            # 3. Están marcados como OCUPADO
            boxes_a_liberar = self.get_queryset().filter(
                estado='OCUPADO'
            ).exclude(
                id__in=boxes_ocupados_por_atencion
            ).exclude(
                id__in=boxes_con_ocupacion_manual
            )
            
            for box in boxes_a_liberar:
                box.liberar()
                boxes_actualizados += 1
        
        except Exception as e:
            # Si hay error con atenciones (módulo no existe, etc), solo procesar ocupaciones manuales
            print(f"Error al sincronizar con atenciones: {e}")
            
            # Solo asegurarse de respetar ocupaciones manuales
            ocupaciones_manuales = OcupacionManual.objects.filter(
                activa=True,
                fecha_fin_programada__gt=ahora
            ).select_related('box')
            
            boxes_con_ocupacion_manual = set(ocupacion.box.id for ocupacion in ocupaciones_manuales)
            
            # Solo liberar boxes que NO tienen ocupación manual
            boxes_a_liberar = self.get_queryset().filter(
                estado='OCUPADO'
            ).exclude(
                id__in=boxes_con_ocupacion_manual
            )
            
            for box in boxes_a_liberar:
                # Verificar doblemente que no tiene ocupación manual
                tiene_ocupacion = OcupacionManual.objects.filter(
                    box=box,
                    activa=True
                ).exists()
                
                if not tiene_ocupacion:
                    box.liberar()
                    boxes_actualizados += 1
        
        return Response({
            'success': True,
            'boxes_actualizados': boxes_actualizados,
            'atenciones_finalizadas': atenciones_finalizadas,
            'timestamp': ahora
        })

    @action(detail=False, methods=['get', 'post'])
    def verificar_y_liberar(self, request):
    
        # Verifica atenciones en curso y libera boxes si han excedido
        # su duración planificada.
        # GET /api/boxes/verificar_y_liberar/
        # POST /api/boxes/verificar_y_liberar/
        
        try:
            from atenciones.models import Atencion
            
            ahora = timezone.now()
            atenciones_en_curso = Atencion.objects.filter(
                estado='EN_CURSO',
                inicio_cronometro__isnull=False
            ).select_related('box')
            
            boxes_liberados = 0
            atenciones_finalizadas = []
            
            for atencion in atenciones_en_curso:
                tiempo_transcurrido = ahora - atencion.inicio_cronometro
                minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
                
                # Debug: mostrar info de la atención
                info_atencion = {
                    'atencion_id': str(atencion.id),
                    'box': atencion.box.numero,
                    'duracion_planificada': atencion.duracion_planificada,
                    'minutos_transcurridos': round(minutos_transcurridos, 1),
                    'debe_finalizar': minutos_transcurridos >= atencion.duracion_planificada,
                }
                
                # Liberar si ha excedido la duración planificada
                if minutos_transcurridos >= atencion.duracion_planificada:
                    # Finalizar la atención
                    resultado = atencion.finalizar_cronometro()
                    
                    if resultado:
                        boxes_liberados += 1
                        info_atencion['finalizada'] = True
                        info_atencion['box_estado_despues'] = atencion.box.estado
                    else:
                        info_atencion['finalizada'] = False
                        info_atencion['error'] = 'No se pudo finalizar'
                    
                    atenciones_finalizadas.append(info_atencion)
            
            return Response({
                'success': True,
                'timestamp': ahora,
                'atenciones_revisadas': atenciones_en_curso.count(),
                'boxes_liberados': boxes_liberados,
                'atenciones_finalizadas': atenciones_finalizadas,
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'mensaje': 'El módulo de atenciones no está disponible'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def estado_detallado(self, request):
        
        # Muestra el estado detallado de todos los boxes con sus atenciones.
        # GET /api/boxes/estado_detallado/
        
        boxes = self.get_queryset()
        ahora = timezone.now()
        resultado = []
        
        try:
            from atenciones.models import Atencion
            
            for box in boxes:
                # Buscar atención activa en este box
                atencion_activa = Atencion.objects.filter(
                    box=box,
                    estado='EN_CURSO'
                ).first()
                
                info_box = {
                    'id': str(box.id),
                    'numero': box.numero,
                    'estado': box.estado,
                    'estado_display': box.get_estado_display(),
                }
                
                if atencion_activa:
                    tiempo_transcurrido = ahora - atencion_activa.inicio_cronometro
                    minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
                    
                    info_box['atencion_activa'] = {
                        'id': str(atencion_activa.id),
                        'inicio': atencion_activa.inicio_cronometro,
                        'duracion_planificada': atencion_activa.duracion_planificada,
                        'minutos_transcurridos': round(minutos_transcurridos, 1),
                        'tiempo_restante': max(0, atencion_activa.duracion_planificada - minutos_transcurridos),
                        'debe_finalizar': minutos_transcurridos >= atencion_activa.duracion_planificada,
                    }
                else:
                    info_box['atencion_activa'] = None
                
                resultado.append(info_box)
        except:
            # Si no existe el módulo de atenciones, solo mostrar estado básico
            for box in boxes:
                resultado.append({
                    'id': str(box.id),
                    'numero': box.numero,
                    'estado': box.estado,
                    'estado_display': box.get_estado_display(),
                    'atencion_activa': None
                })
        
        return Response({
            'timestamp': ahora,
            'boxes': resultado
        })

    @action(detail=False, methods=['get', 'post'])
    def liberar_ocupaciones_manuales(self, request):
        
        # Libera boxes cuyas ocupaciones manuales han expirado.
        # GET/POST /api/boxes/liberar_ocupaciones_manuales/
        
        ahora = timezone.now()
        
        # Buscar ocupaciones manuales que deben finalizar
        ocupaciones_a_finalizar = OcupacionManual.objects.filter(
            activa=True,
            fecha_fin_programada__lte=ahora
        ).select_related('box')
        
        boxes_liberados = 0
        ocupaciones_finalizadas = []
        
        for ocupacion in ocupaciones_a_finalizar:
            if ocupacion.finalizar():
                boxes_liberados += 1
                ocupaciones_finalizadas.append({
                    'ocupacion_id': str(ocupacion.id),
                    'box': ocupacion.box.numero,
                    'duracion_minutos': ocupacion.duracion_minutos,
                    'motivo': ocupacion.motivo,
                })
        
        return Response({
            'success': True,
            'timestamp': ahora,
            'boxes_liberados': boxes_liberados,
            'ocupaciones_finalizadas': ocupaciones_finalizadas,
        })