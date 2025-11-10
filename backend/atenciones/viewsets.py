from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count, F
from django.utils import timezone
from .models import Medico, Atencion
from .serializers import (
    MedicoSerializer,
    MedicoListSerializer,
    MedicoCreateUpdateSerializer,
    AtencionSerializer,
    AtencionListSerializer,
    AtencionCreateUpdateSerializer,
    AtencionCronometroSerializer,
    AtencionCancelarSerializer,
    AtencionReagendarSerializer,
    AtencionEstadisticasSerializer
)


class MedicoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar médicos y prestadores de salud.
    
    Endpoints disponibles:
    - GET /api/medicos/ - Lista todos los médicos
    - POST /api/medicos/ - Crea un nuevo médico
    - GET /api/medicos/{id}/ - Detalle de un médico
    - PUT /api/medicos/{id}/ - Actualiza un médico
    - PATCH /api/medicos/{id}/ - Actualiza parcialmente
    - DELETE /api/medicos/{id}/ - Elimina un médico
    
    Acciones personalizadas:
    - GET /api/medicos/{id}/atenciones_hoy/ - Atenciones del día
    - GET /api/medicos/{id}/agenda_semanal/ - Agenda de la semana
    - GET /api/medicos/{id}/metricas/ - Métricas de desempeño
    - GET /api/medicos/activos/ - Lista médicos activos
    - GET /api/medicos/por_especialidad/ - Agrupa por especialidad
    - GET /api/medicos/estadisticas/ - Estadísticas generales
    - POST /api/medicos/{id}/activar/ - Activa médico
    - POST /api/medicos/{id}/desactivar/ - Desactiva médico
    """
    queryset = Medico.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # Retorna el serializer apropiado según la acción
        if self.action == 'list':
            return MedicoListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return MedicoCreateUpdateSerializer
        return MedicoSerializer
    
    def get_queryset(self):
        # Filtra el queryset basado en parámetros de query
        queryset = Medico.objects.all()
        
        # Filtros
        activo = self.request.query_params.get('activo', None)
        especialidad = self.request.query_params.get('especialidad', None)
        buscar = self.request.query_params.get('q', None)
        
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(activo=activo_bool)
        
        if especialidad:
            queryset = queryset.filter(especialidad_principal=especialidad)
        
        if buscar:
            queryset = queryset.filter(
                Q(nombre__icontains=buscar) |
                Q(apellido__icontains=buscar) |
                Q(codigo_medico__icontains=buscar)
            )
        
        return queryset.order_by('apellido', 'nombre')
    
    @action(detail=True, methods=['get'])
    def atenciones_hoy(self, request, pk=None):
        
        # Obtiene las atenciones del médico para el día actual.
        # GET /api/medicos/{id}/atenciones_hoy/
        
        medico = self.get_object()
        atenciones = medico.obtener_atenciones_dia()
        
        serializer = AtencionListSerializer(atenciones, many=True)
        
        return Response({
            'medico': MedicoListSerializer(medico).data,
            'fecha': timezone.now().date(),
            'total_atenciones': atenciones.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def agenda_semanal(self, request, pk=None):
        
        # Obtiene la agenda del médico para la semana actual.
        # GET /api/medicos/{id}/agenda_semanal/
        
        medico = self.get_object()
        
        # Obtener inicio y fin de semana
        hoy = timezone.now().date()
        inicio_semana = hoy - timezone.timedelta(days=hoy.weekday())
        fin_semana = inicio_semana + timezone.timedelta(days=6)
        
        atenciones = medico.atenciones.filter(
            fecha_hora_inicio__date__gte=inicio_semana,
            fecha_hora_inicio__date__lte=fin_semana
        ).order_by('fecha_hora_inicio')
        
        serializer = AtencionListSerializer(atenciones, many=True)
        
        return Response({
            'medico': MedicoListSerializer(medico).data,
            'inicio_semana': inicio_semana,
            'fin_semana': fin_semana,
            'total_atenciones': atenciones.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def metricas(self, request, pk=None):
        
        # Obtiene métricas de desempeño del médico.
        # GET /api/medicos/{id}/metricas/
        
        medico = self.get_object()
        
        # Métricas básicas
        eficiencia = medico.obtener_eficiencia()
        tiempo_promedio = medico.calcular_tiempo_promedio_atencion()
        
        # Atenciones del mes
        inicio_mes = timezone.now().replace(day=1)
        atenciones_mes = medico.atenciones.filter(
            fecha_hora_inicio__gte=inicio_mes
        )
        
        return Response({
            'medico': MedicoListSerializer(medico).data,
            'tiempo_promedio_atencion': round(tiempo_promedio, 2),
            'eficiencia': eficiencia,
            'atenciones_mes': atenciones_mes.count(),
            'atenciones_completadas_mes': atenciones_mes.filter(estado='COMPLETADA').count(),
            'atenciones_canceladas_mes': atenciones_mes.filter(estado='CANCELADA').count(),
        })
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        
        # Lista médicos activos.
        # GET /api/medicos/activos/
        
        medicos = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(medicos, many=True)
        
        return Response({
            'count': medicos.count(),
            'medicos': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_especialidad(self, request):
        
        # Agrupa médicos por especialidad.
        # GET /api/medicos/por_especialidad/
        
        queryset = self.get_queryset()
        
        resultado = {}
        for especialidad_key, especialidad_label in Medico.ESPECIALIDAD_CHOICES:
            medicos = queryset.filter(especialidad_principal=especialidad_key)
            resultado[especialidad_key] = {
                'label': especialidad_label,
                'total': medicos.count(),
                'activos': medicos.filter(activo=True).count(),
                'medicos': MedicoListSerializer(medicos, many=True).data
            }
        
        return Response(resultado)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        
        # Estadísticas generales de médicos.
        # GET /api/medicos/estadisticas/
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        activos = queryset.filter(activo=True).count()
        
        # Por especialidad
        por_especialidad = {}
        for especialidad_key, especialidad_label in Medico.ESPECIALIDAD_CHOICES:
            count = queryset.filter(especialidad_principal=especialidad_key).count()
            por_especialidad[especialidad_key] = {
                'label': especialidad_label,
                'count': count
            }
        
        return Response({
            'total': total,
            'activos': activos,
            'inactivos': total - activos,
            'por_especialidad': por_especialidad,
        })
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        
        # Activa un médico.
        # POST /api/medicos/{id}/activar/
        
        medico = self.get_object()
        medico.activo = True
        medico.save()
        
        return Response({
            'success': True,
            'mensaje': f'Médico {medico.nombre_completo} activado',
            'activo': medico.activo
        })
    
    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        
        # Desactiva un médico.
        # POST /api/medicos/{id}/desactivar/
        
        medico = self.get_object()
        medico.activo = False
        medico.save()
        
        return Response({
            'success': True,
            'mensaje': f'Médico {medico.nombre_completo} desactivado',
            'activo': medico.activo
        })


class AtencionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar atenciones médicas con cronómetro.
    
    Endpoints disponibles:
    - GET /api/atenciones/ - Lista todas las atenciones
    - POST /api/atenciones/ - Crea una nueva atención
    - GET /api/atenciones/{id}/ - Detalle de una atención
    - PUT /api/atenciones/{id}/ - Actualiza una atención
    - PATCH /api/atenciones/{id}/ - Actualiza parcialmente
    - DELETE /api/atenciones/{id}/ - Elimina una atención
    
    Acciones personalizadas:
    - POST /api/atenciones/{id}/iniciar_cronometro/ - Inicia cronómetro
    - POST /api/atenciones/{id}/finalizar_cronometro/ - Finaliza cronómetro
    - POST /api/atenciones/{id}/cancelar/ - Cancela atención
    - POST /api/atenciones/{id}/reagendar/ - Reagenda atención
    - GET /api/atenciones/en_curso/ - Atenciones en curso
    - GET /api/atenciones/hoy/ - Atenciones del día
    - GET /api/atenciones/pendientes/ - Atenciones pendientes
    - GET /api/atenciones/retrasadas/ - Atenciones retrasadas
    - GET /api/atenciones/estadisticas/ - Estadísticas generales
    """
    queryset = Atencion.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # Retorna el serializer apropiado según la acción
        if self.action == 'list':
            return AtencionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AtencionCreateUpdateSerializer
        elif self.action in ['iniciar_cronometro', 'finalizar_cronometro']:
            return AtencionCronometroSerializer
        elif self.action == 'cancelar':
            return AtencionCancelarSerializer
        elif self.action == 'reagendar':
            return AtencionReagendarSerializer
        elif self.action == 'estadisticas':
            return AtencionEstadisticasSerializer
        return AtencionSerializer
    
    def get_queryset(self):
        # Filtra el queryset basado en parámetros de query
        queryset = Atencion.objects.select_related('paciente', 'medico', 'box')
        
        # Filtros
        estado = self.request.query_params.get('estado', None)
        medico_id = self.request.query_params.get('medico', None)
        box_id = self.request.query_params.get('box', None)
        paciente_id = self.request.query_params.get('paciente', None)
        tipo = self.request.query_params.get('tipo', None)
        fecha = self.request.query_params.get('fecha', None)
        fecha_desde = self.request.query_params.get('fecha_desde', None)
        fecha_hasta = self.request.query_params.get('fecha_hasta', None)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if medico_id:
            queryset = queryset.filter(medico_id=medico_id)
        
        if box_id:
            queryset = queryset.filter(box_id=box_id)
        
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        if tipo:
            queryset = queryset.filter(tipo_atencion=tipo)
        
        if fecha:
            queryset = queryset.filter(fecha_hora_inicio__date=fecha)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_hora_inicio__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_hora_inicio__lte=fecha_hasta)
        
        return queryset.order_by('-fecha_hora_inicio')
    
    @action(detail=True, methods=['post'])
    def iniciar_cronometro(self, request, pk=None):
        
        # Inicia el cronómetro de la atención.
        # POST /api/atenciones/{id}/iniciar_cronometro/
    
        atencion = self.get_object()
        
        if atencion.iniciar_cronometro():
            return Response({
                'success': True,
                'mensaje': 'Cronómetro iniciado correctamente',
                'inicio_cronometro': atencion.inicio_cronometro,
                'estado': atencion.estado,
                'box_ocupado': atencion.box.estado == 'OCUPADO'
            })
        
        return Response({
            'success': False,
            'mensaje': f'No se pudo iniciar el cronómetro. Estado actual: {atencion.get_estado_display()}',
            'estado_actual': atencion.estado
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def finalizar_cronometro(self, request, pk=None):
        
        # Finaliza el cronómetro de la atención.
        # POST /api/atenciones/{id}/finalizar_cronometro/
        
        atencion = self.get_object()
        
        if atencion.finalizar_cronometro():
            return Response({
                'success': True,
                'mensaje': 'Cronómetro finalizado correctamente',
                'fin_cronometro': atencion.fin_cronometro,
                'duracion_real': atencion.duracion_real,
                'estado': atencion.estado,
                'box_liberado': atencion.box.estado == 'DISPONIBLE',
                'diferencia_duracion': atencion.calcular_diferencia_duracion()
            })
        
        return Response({
            'success': False,
            'mensaje': f'No se pudo finalizar el cronómetro. Estado actual: {atencion.get_estado_display()}',
            'estado_actual': atencion.estado
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        
        # Cancela una atención.
        # POST /api/atenciones/{id}/cancelar/
    
        atencion = self.get_object()
        serializer = AtencionCancelarSerializer(data=request.data)
        
        if serializer.is_valid():
            motivo = serializer.validated_data.get('motivo', '')
            
            if atencion.cancelar_atencion(motivo):
                return Response({
                    'success': True,
                    'mensaje': 'Atención cancelada',
                    'estado': atencion.estado,
                    'motivo': motivo
                })
            
            return Response({
                'success': False,
                'mensaje': 'No se pudo cancelar la atención'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reagendar(self, request, pk=None):
        
        # Reagenda una atención.
        # POST /api/atenciones/{id}/reagendar/
    
        atencion = self.get_object()
        serializer = AtencionReagendarSerializer(data=request.data)
        
        if serializer.is_valid():
            nueva_fecha = serializer.validated_data['nueva_fecha']
            nuevo_box = serializer.validated_data.get('nuevo_box')
            
            if atencion.reagendar(nueva_fecha, nuevo_box):
                return Response({
                    'success': True,
                    'mensaje': 'Atención reagendada correctamente',
                    'nueva_fecha': atencion.fecha_hora_inicio,
                    'box': atencion.box.numero
                })
            
            return Response({
                'success': False,
                'mensaje': 'No se pudo reagendar la atención'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def en_curso(self, request):
        
        # Lista atenciones actualmente en curso.
        # GET /api/atenciones/en_curso/
        
        atenciones = self.get_queryset().filter(estado='EN_CURSO')
        serializer = self.get_serializer(atenciones, many=True)
        
        return Response({
            'count': atenciones.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def hoy(self, request):
        
        # Lista atenciones del día actual.
        # GET /api/atenciones/hoy/
        
        hoy = timezone.now().date()
        atenciones = self.get_queryset().filter(fecha_hora_inicio__date=hoy)
        serializer = self.get_serializer(atenciones, many=True)
        
        return Response({
            'fecha': hoy,
            'count': atenciones.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        
        # Lista atenciones pendientes (programadas o en espera).
        # GET /api/atenciones/pendientes/
        
        atenciones = self.get_queryset().filter(
            estado__in=['PROGRAMADA', 'EN_ESPERA']
        )
        serializer = self.get_serializer(atenciones, many=True)
        
        return Response({
            'count': atenciones.count(),
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def retrasadas(self, request):
        
        # Lista atenciones que están retrasadas.
        # GET /api/atenciones/retrasadas/
        
        atenciones_en_curso = self.get_queryset().filter(estado='EN_CURSO')
        atenciones_retrasadas = [
            atencion for atencion in atenciones_en_curso 
            if atencion.is_retrasada()
        ]
        
        serializer = self.get_serializer(atenciones_retrasadas, many=True)
        
        return Response({
            'count': len(atenciones_retrasadas),
            'atenciones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        
        # Estadísticas generales de atenciones.
        # GET /api/atenciones/estadisticas/
    
        queryset = self.get_queryset()
        
        # Por estado
        por_estado = {}
        for estado_key, estado_label in Atencion.ESTADO_CHOICES:
            count = queryset.filter(estado=estado_key).count()
            por_estado[estado_key] = {
                'label': estado_label,
                'count': count
            }
        
        # Por tipo
        por_tipo = {}
        for tipo_key, tipo_label in Atencion.TIPO_ATENCION_CHOICES:
            count = queryset.filter(tipo_atencion=tipo_key).count()
            por_tipo[tipo_key] = {
                'label': tipo_label,
                'count': count
            }
        
        # Promedios
        atenciones_completadas = queryset.filter(
            estado='COMPLETADA',
            duracion_real__isnull=False
        )
        
        promedio_duracion_real = 0
        if atenciones_completadas.exists():
            promedio_duracion_real = atenciones_completadas.aggregate(
                promedio=Avg('duracion_real')
            )['promedio'] or 0
        
        promedio_duracion_planificada = queryset.aggregate(
            promedio=Avg('duracion_planificada')
        )['promedio'] or 0
        
        # Tasa de cumplimiento
        total_completadas = atenciones_completadas.count()
        a_tiempo = atenciones_completadas.filter(
            duracion_real__lte=F('duracion_planificada')
        ).count()
        
        tasa_cumplimiento = (a_tiempo / total_completadas * 100) if total_completadas > 0 else 0
        
        # Atenciones retrasadas
        atenciones_en_curso = queryset.filter(estado='EN_CURSO')
        retrasadas = sum(1 for a in atenciones_en_curso if a.is_retrasada())
        
        return Response({
            'total': queryset.count(),
            'por_estado': por_estado,
            'por_tipo': por_tipo,
            'promedio_duracion_real': round(promedio_duracion_real, 2),
            'promedio_duracion_planificada': round(promedio_duracion_planificada, 2),
            'tasa_cumplimiento_horario': round(tasa_cumplimiento, 2),
            'atenciones_retrasadas': retrasadas,
        })
    
    @action(detail=True, methods=['get'])
    def metricas(self, request, pk=None):
        
        # Métricas detalladas de una atención específica.
        # GET /api/atenciones/{id}/metricas/
        
        atencion = self.get_object()
        
        return Response({
            'atencion_id': str(atencion.id),
            'metricas': atencion.generar_metricas(),
            'retraso_minutos': atencion.calcular_retraso(),
            'diferencia_duracion': atencion.calcular_diferencia_duracion(),
            'esta_retrasada': atencion.is_retrasada(),
            'tiempo_transcurrido': self._get_tiempo_transcurrido(atencion),
        })
    
    def _get_tiempo_transcurrido(self, atencion):
        # Helper para obtener tiempo transcurrido formateado
        tiempo = atencion.obtener_tiempo_transcurrido()
        if tiempo:
            minutos = int(tiempo.total_seconds() / 60)
            horas = minutos // 60
            mins = minutos % 60
            return {
                'minutos': minutos,
                'formateado': f"{horas}h {mins}m"
            }
        return None

    @action(detail=False, methods=['get'])
    def con_atraso_reportado(self, request):
        
        # Lista atenciones con atraso reportado por el médico.
        # Estas son las que aparecerán en EstadoBoxes.
        # GET /api/atenciones/con_atraso_reportado/
        
        from django.utils import timezone
        ahora = timezone.now()
        
        # Buscar atenciones con atraso reportado que NO estén finalizadas
        atenciones = self.get_queryset().filter(
            atraso_reportado=True,
            estado__in=['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO'],
            fecha_reporte_atraso__isnull=False
        ).select_related('paciente', 'medico', 'box')
        
        # Marcar como no presentado si han pasado más de 5 min desde el reporte de atraso
        atenciones_actualizadas = 0
        for atencion in atenciones:
            minutos_desde_reporte = (ahora - atencion.fecha_reporte_atraso).total_seconds() / 60
            
            if minutos_desde_reporte >= 5:
                # Marcar como no presentado automáticamente
                resultado = atencion.marcar_no_presentado()
                if resultado:
                    atencion.observaciones += "\n\n[AUTOMÁTICO] Marcado como no presentado después de 5 minutos de espera desde reporte de atraso."
                    atencion.save()
                    atenciones_actualizadas += 1
        
        # Recargar las atenciones después de la actualización automática
        atenciones = self.get_queryset().filter(
            atraso_reportado=True,
            estado__in=['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO'],
            fecha_reporte_atraso__isnull=False
        ).select_related('paciente', 'medico', 'box')
        
        serializer = self.get_serializer(atenciones, many=True)
        
        return Response({
            'count': atenciones.count(),
            'atenciones_marcadas_no_presentado': atenciones_actualizadas,
            'atenciones': serializer.data
        })
        
    @action(detail=True, methods=['post'], url_path='reportar-atraso')
    def reportar_atraso(self, request, pk=None):
        """
        Reporta un atraso del paciente.
        
        Disponible en:
        - Atenciones PROGRAMADAS/EN_ESPERA (paciente no llega a tiempo)
        - Atenciones EN_CURSO durante los primeros 5 minutos (paciente se ausenta)
        
        Inicia un timer de 5 minutos. Si el paciente no llega/regresa en ese tiempo,
        se marcará automáticamente como NO_PRESENTADO.
        """
        atencion = self.get_object()
        
        puede_reportar, mensaje_error = atencion.puede_reportar_atraso()
        
        if not puede_reportar:
            return Response(
                {'error': mensaje_error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        motivo = request.data.get('motivo', '')
        
        if atencion.reportar_atraso(motivo):
            serializer = AtencionSerializer(atencion)
            
            # Mensaje diferente según el estado
            if atencion.estado == 'EN_CURSO':
                mensaje = '⚠️ Atraso reportado - Paciente tiene 5 minutos para regresar'
            else:
                mensaje = '⚠️ Atraso reportado - Paciente tiene 5 minutos para llegar'
            
            return Response({
                'success': True,
                'message': mensaje,
                'atencion': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'No se pudo reportar el atraso'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'], url_path='verificar-atraso')
    def verificar_atraso(self, request, pk=None):
        
        # Verifica si han pasado 5 minutos desde el reporte de atraso.
        # Si es así, marca automáticamente como NO_PRESENTADO.
        
        atencion = self.get_object()
        
        if not atencion.atraso_reportado:
            return Response(
                {'success': True, 'message': 'No hay atraso reportado'},
                status=status.HTTP_200_OK
            )
        
        if atencion.verificar_tiempo_atraso():
            # Han pasado 5 minutos, marcar como NO_PRESENTADO
            if atencion.marcar_no_presentado():
                serializer = AtencionSerializer(atencion)
                return Response({
                    'success': True,
                    'message': 'Atención marcada como NO_PRESENTADO',
                    'atencion': serializer.data
                }, status=status.HTTP_200_OK)
        
        serializer = AtencionSerializer(atencion)
        return Response({
            'success': True,
            'message': 'Aún dentro del tiempo de espera',
            'atencion': serializer.data
        }, status=status.HTTP_200_OK)


    @action(detail=True, methods=['post'], url_path='iniciar-consulta')
    def iniciar_consulta(self, request, pk=None):
        
        # El paciente llegó después de reportar atraso.
        # Cancela el timer de atraso y permite continuar/iniciar la consulta.
        
        atencion = self.get_object()

        # 1. Verificar si hay un atraso reportado. Si no, no es el flujo correcto.
        if not atencion.atraso_reportado:
            return Response(
                {'error': 'No hay atraso reportado para esta atención.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Verificar si el tiempo de espera ha expirado (5 minutos)
        if atencion.verificar_tiempo_atraso():
            return Response(
                {'error': 'El tiempo de espera ha expirado. La atención ya debería estar marcada como NO_PRESENTADO.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar estado actual antes de limpiar el flag
        estado_previo = atencion.estado

        # 3. Limpiar el reporte de atraso (siempre)
        atencion.atraso_reportado = False
        atencion.fecha_reporte_atraso = None
        atencion.motivo_atraso = "Paciente llegó/regresó después de reportar atraso dentro del tiempo de tolerancia."
        atencion.save()
        
        mensaje = "Atención reanudada correctamente."

        # 4. Si la atención estaba PROGRAMADA o EN_ESPERA, la INICIAMOS AHORA
        if estado_previo in ['PROGRAMADA', 'EN_ESPERA']:
            if atencion.iniciar_cronometro():
                mensaje = "Consulta iniciada y atraso despejado correctamente."
            else:
                 # Esto solo debería ocurrir si ya existía otra en curso, etc.
                return Response(
                    {'error': 'No se pudo iniciar el cronómetro.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Si estaba EN_CURSO, solo se limpió el flag y el cronómetro sigue corriendo.
        
        serializer = AtencionSerializer(atencion)
        return Response({
            'success': True,
            'message': mensaje,
            'atencion': serializer.data
        }, status=status.HTTP_200_OK)
        
    def create(self, request, *args, **kwargs):
        """
        Crea una nueva atención y automáticamente crea ruta clínica si no existe.
        """
        from rutas_clinicas.models import RutaClinica
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verificar si el paciente tiene ruta antes de crear la atención
        paciente = serializer.validated_data['paciente']
        tiene_ruta_antes = RutaClinica.objects.filter(
            paciente=paciente,
            estado__in=['INICIADA', 'EN_PROGRESO', 'PAUSADA']
        ).exists()
        
        # Crear la atención
        self.perform_create(serializer)
        
        # Verificar si se creó ruta después
        tiene_ruta_despues = RutaClinica.objects.filter(
            paciente=paciente,
            estado__in=['INICIADA', 'EN_PROGRESO', 'PAUSADA']
        ).exists()
        
        # Log para debugging
        if not tiene_ruta_antes and tiene_ruta_despues:
            print(f"✅ Ruta clínica creada automáticamente para paciente {paciente.identificador_hash[:8]}")
        
        headers = self.get_success_headers(serializer.data)
        
        # Incluir información sobre la ruta en la respuesta
        response_data = serializer.data
        response_data['ruta_creada_automaticamente'] = (not tiene_ruta_antes and tiene_ruta_despues)
        
        return Response(
            response_data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )