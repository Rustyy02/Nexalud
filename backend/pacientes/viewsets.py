# backend/pacientes/viewsets.py - ACTUALIZADO CON NUEVOS ENDPOINTS
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count
from .models import Paciente
from .serializers import (
    PacienteSerializer,
    PacienteListSerializer,
    PacienteCreateUpdateSerializer,
    PacienteEstadoSerializer,
    PacienteIMCSerializer,
    PacienteDatosMedicosSerializer
)


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pacientes con funcionalidades médicas ampliadas.
    
    Endpoints disponibles:
    - GET /api/pacientes/ - Lista todos los pacientes
    - POST /api/pacientes/ - Crea un nuevo paciente
    - GET /api/pacientes/{id}/ - Detalle de un paciente
    - PUT /api/pacientes/{id}/ - Actualiza un paciente completo
    - PATCH /api/pacientes/{id}/ - Actualiza parcialmente un paciente
    - DELETE /api/pacientes/{id}/ - Elimina un paciente
    
    Acciones personalizadas:
    - POST /api/pacientes/{id}/cambiar_estado/ - Cambia el estado
    - GET /api/pacientes/activos/ - Lista pacientes activos
    - GET /api/pacientes/en_espera/ - Lista pacientes en espera
    - GET /api/pacientes/estadisticas/ - Estadísticas generales
    - GET /api/pacientes/{id}/rutas_clinicas/ - Rutas clínicas
    - GET /api/pacientes/{id}/atenciones/ - Atenciones
    
    NUEVOS ENDPOINTS:
    - GET /api/pacientes/{id}/datos_medicos/ - Información médica completa
    - GET /api/pacientes/{id}/calcular_imc/ - Calcula el IMC
    - GET /api/pacientes/con_alergias/ - Pacientes con alergias
    - GET /api/pacientes/por_tipo_sangre/ - Agrupa por tipo de sangre
    - GET /api/pacientes/estadisticas_medicas/ - Estadísticas médicas
    """
    queryset = Paciente.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return PacienteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PacienteCreateUpdateSerializer
        elif self.action == 'cambiar_estado':
            return PacienteEstadoSerializer
        elif self.action == 'calcular_imc':
            return PacienteIMCSerializer
        elif self.action == 'datos_medicos':
            return PacienteDatosMedicosSerializer
        return PacienteSerializer
    
    def get_queryset(self):
        """Filtra el queryset basado en parámetros de query"""
        queryset = Paciente.objects.all()
        
        # Filtros básicos
        estado = self.request.query_params.get('estado', None)
        urgencia = self.request.query_params.get('urgencia', None)
        activo = self.request.query_params.get('activo', None)
        buscar = self.request.query_params.get('q', None)
        
        # NUEVOS FILTROS
        tipo_sangre = self.request.query_params.get('tipo_sangre', None)
        tiene_alergias = self.request.query_params.get('tiene_alergias', None)
        genero = self.request.query_params.get('genero', None)
        
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
        
        # NUEVOS FILTROS
        if tipo_sangre:
            queryset = queryset.filter(tipo_sangre=tipo_sangre)
        
        if tiene_alergias is not None:
            if tiene_alergias.lower() in ['true', '1', 'yes']:
                queryset = queryset.exclude(alergias='')
        
        if genero:
            queryset = queryset.filter(genero=genero)
        
        return queryset.order_by('-fecha_ingreso')
    
    # ============================================
    # ENDPOINTS BÁSICOS (ya existían)
    # ============================================
    
    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """Cambia el estado de un paciente"""
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
        """Lista pacientes activos"""
        pacientes = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(pacientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_espera(self, request):
        """Lista pacientes en espera"""
        pacientes = self.get_queryset().filter(
            estado_actual='EN_ESPERA',
            activo=True
        )
        serializer = self.get_serializer(pacientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas generales de pacientes"""
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
        """Obtiene las rutas clínicas del paciente"""
        paciente = self.get_object()
        rutas = paciente.rutas_clinicas.all()
        
        from rutas_clinicas.serializers import RutaClinicaListSerializer
        serializer = RutaClinicaListSerializer(rutas, many=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def atenciones(self, request, pk=None):
        """Obtiene las atenciones del paciente"""
        paciente = self.get_object()
        atenciones = paciente.atenciones.all()
        
        from atenciones.serializers import AtencionListSerializer
        serializer = AtencionListSerializer(atenciones, many=True)
        
        return Response(serializer.data)
    
    # ============================================
    # NUEVOS ENDPOINTS - INFORMACIÓN MÉDICA
    # ============================================
    
    @action(detail=True, methods=['get'])
    def datos_medicos(self, request, pk=None):
        """
        Obtiene información médica completa del paciente.
        
        GET /api/pacientes/{id}/datos_medicos/
        """
        paciente = self.get_object()
        info_medica = paciente.obtener_informacion_medica_completa()
        
        return Response({
            'paciente_id': str(paciente.id),
            'informacion_medica': info_medica,
            'alertas': {
                'tiene_alergias': paciente.tiene_alergias(),
                'tiene_condiciones': paciente.tiene_condiciones_preexistentes(),
            }
        })
    
    @action(detail=True, methods=['get'])
    def calcular_imc(self, request, pk=None):
        """
        Calcula el IMC del paciente.
        
        GET /api/pacientes/{id}/calcular_imc/
        """
        paciente = self.get_object()
        imc = paciente.calcular_imc()
        categoria = paciente.obtener_categoria_imc()
        
        if not imc:
            return Response({
                'error': 'No se puede calcular el IMC. Faltan datos de peso o altura.',
                'peso': float(paciente.peso) if paciente.peso else None,
                'altura': paciente.altura
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'paciente_id': str(paciente.id),
            'nombre': paciente.obtener_nombre_display(),
            'peso': float(paciente.peso),
            'altura': paciente.altura,
            'imc': imc,
            'categoria_imc': categoria,
            'recomendacion': self._get_recomendacion_imc(categoria)
        })
    
    @action(detail=False, methods=['get'])
    def con_alergias(self, request):
        """
        Lista pacientes que tienen alergias registradas.
        
        GET /api/pacientes/con_alergias/
        """
        pacientes = self.get_queryset().exclude(alergias='')
        serializer = self.get_serializer(pacientes, many=True)
        
        return Response({
            'count': pacientes.count(),
            'pacientes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo_sangre(self, request):
        """
        Agrupa pacientes por tipo de sangre.
        
        GET /api/pacientes/por_tipo_sangre/
        """
        queryset = self.get_queryset()
        
        resultado = {}
        for tipo_key, tipo_label in Paciente.TIPO_SANGRE_CHOICES:
            pacientes = queryset.filter(tipo_sangre=tipo_key)
            resultado[tipo_key] = {
                'label': tipo_label,
                'count': pacientes.count(),
                'porcentaje': round(
                    (pacientes.count() / queryset.count() * 100) if queryset.count() > 0 else 0,
                    2
                )
            }
        
        return Response(resultado)
    
    @action(detail=False, methods=['get'])
    def estadisticas_medicas(self, request):
        """
        Estadísticas médicas avanzadas de los pacientes.
        
        GET /api/pacientes/estadisticas_medicas/
        """
        queryset = self.get_queryset()
        
        # Contar por tipo de sangre
        por_tipo_sangre = {}
        for tipo_key, tipo_label in Paciente.TIPO_SANGRE_CHOICES:
            count = queryset.filter(tipo_sangre=tipo_key).count()
            por_tipo_sangre[tipo_key] = {
                'label': tipo_label,
                'count': count
            }
        
        # Pacientes con datos médicos completos
        con_peso = queryset.exclude(peso__isnull=True).count()
        con_altura = queryset.exclude(altura__isnull=True).count()
        con_alergias = queryset.exclude(alergias='').count()
        con_condiciones = queryset.exclude(condiciones_preexistentes='').count()
        con_medicamentos = queryset.exclude(medicamentos_actuales='').count()
        
        # Calcular promedios de IMC por categoría
        pacientes_con_imc = []
        categorias_imc = {
            'Bajo peso': 0,
            'Peso normal': 0,
            'Sobrepeso': 0,
            'Obesidad': 0
        }
        
        for paciente in queryset:
            imc = paciente.calcular_imc()
            if imc:
                pacientes_con_imc.append(imc)
                categoria = paciente.obtener_categoria_imc()
                if categoria in categorias_imc:
                    categorias_imc[categoria] += 1
        
        imc_promedio = sum(pacientes_con_imc) / len(pacientes_con_imc) if pacientes_con_imc else None
        
        # Distribución por género
        por_genero = {}
        for genero_key, genero_label in Paciente.GENERO_CHOICES:
            count = queryset.filter(genero=genero_key).count()
            por_genero[genero_key] = {
                'label': genero_label,
                'count': count
            }
        
        return Response({
            'total_pacientes': queryset.count(),
            'por_tipo_sangre': por_tipo_sangre,
            'por_genero': por_genero,
            'datos_completos': {
                'con_peso': con_peso,
                'con_altura': con_altura,
                'con_alergias': con_alergias,
                'con_condiciones_preexistentes': con_condiciones,
                'con_medicamentos': con_medicamentos,
                'porcentaje_datos_completos': round(
                    (min(con_peso, con_altura) / queryset.count() * 100) if queryset.count() > 0 else 0,
                    2
                )
            },
            'imc': {
                'promedio': round(imc_promedio, 2) if imc_promedio else None,
                'total_calculable': len(pacientes_con_imc),
                'por_categoria': categorias_imc
            }
        })
    
    @action(detail=False, methods=['get'])
    def pacientes_criticos(self, request):
        """
        Lista pacientes con nivel de urgencia CRÍTICA o ALTA.
        
        GET /api/pacientes/pacientes_criticos/
        """
        pacientes = self.get_queryset().filter(
            nivel_urgencia__in=['CRITICA', 'ALTA'],
            activo=True
        ).order_by('-nivel_urgencia', '-fecha_ingreso')
        
        serializer = self.get_serializer(pacientes, many=True)
        
        return Response({
            'count': pacientes.count(),
            'criticos': pacientes.filter(nivel_urgencia='CRITICA').count(),
            'altos': pacientes.filter(nivel_urgencia='ALTA').count(),
            'pacientes': serializer.data
        })
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    def _get_recomendacion_imc(self, categoria):
        """Retorna recomendaciones según la categoría del IMC"""
        recomendaciones = {
            'Bajo peso': 'Se recomienda evaluación nutricional y aumento controlado de peso.',
            'Peso normal': 'El peso está en rango saludable. Mantener hábitos saludables.',
            'Sobrepeso': 'Se recomienda evaluación nutricional y plan de ejercicio.',
            'Obesidad': 'Se recomienda evaluación médica completa y plan de reducción de peso supervisado.',
            'No disponible': 'No se puede calcular. Registre peso y altura del paciente.'
        }
        return recomendaciones.get(categoria, 'No disponible')