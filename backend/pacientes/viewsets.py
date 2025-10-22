# backend/pacientes/viewsets.py - ACTUALIZADO COMPLETO
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
    PacienteDatosMedicosSerializer,
    PacienteDatosContactoSerializer,
    PacienteSeguroMedicoSerializer,
    PacienteResumenSerializer
)


class PacienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestionar pacientes con toda su información.
    
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
    - GET /api/pacientes/{id}/datos_medicos/ - Información médica completa
    - GET /api/pacientes/{id}/datos_contacto/ - Información de contacto
    - GET /api/pacientes/{id}/seguro_medico/ - Información del seguro
    - GET /api/pacientes/{id}/calcular_imc/ - Calcula el IMC
    - GET /api/pacientes/con_alergias/ - Pacientes con alergias
    - GET /api/pacientes/por_tipo_sangre/ - Agrupa por tipo de sangre
    - GET /api/pacientes/por_seguro/ - Agrupa por seguro médico
    - GET /api/pacientes/por_region/ - Agrupa por región
    - POST /api/pacientes/validar_rut/ - Valida un RUT chileno
    - POST /api/pacientes/buscar_por_rut/ - Busca paciente por RUT
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
        elif self.action == 'datos_contacto':
            return PacienteDatosContactoSerializer
        elif self.action == 'seguro_medico':
            return PacienteSeguroMedicoSerializer
        elif self.action in ['activos', 'en_espera', 'con_alergias']:
            return PacienteResumenSerializer
        return PacienteSerializer
    
    def get_queryset(self):
        """Filtra el queryset basado en parámetros de query"""
        queryset = Paciente.objects.all()
        
        # Filtros básicos
        estado = self.request.query_params.get('estado')
        urgencia = self.request.query_params.get('urgencia')
        activo = self.request.query_params.get('activo')
        buscar = self.request.query_params.get('q')
        
        # Nuevos filtros
        tipo_sangre = self.request.query_params.get('tipo_sangre')
        tiene_alergias = self.request.query_params.get('tiene_alergias')
        genero = self.request.query_params.get('genero')
        seguro = self.request.query_params.get('seguro')
        region = self.request.query_params.get('region')
        rut = self.request.query_params.get('rut')
        
        if estado:
            queryset = queryset.filter(estado_actual=estado)
        
        if urgencia:
            queryset = queryset.filter(nivel_urgencia=urgencia)
        
        if activo is not None:
            activo_bool = activo.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(activo=activo_bool)
        
        if buscar:
            queryset = queryset.filter(
                Q(rut__icontains=buscar) |
                Q(nombre__icontains=buscar) |
                Q(apellido_paterno__icontains=buscar) |
                Q(apellido_materno__icontains=buscar) |
                Q(correo__icontains=buscar) |
                Q(identificador_hash__icontains=buscar)
            )
        
        # Nuevos filtros
        if tipo_sangre:
            queryset = queryset.filter(tipo_sangre=tipo_sangre)
        
        if tiene_alergias is not None:
            if tiene_alergias.lower() in ['true', '1', 'yes']:
                queryset = queryset.exclude(alergias='')
        
        if genero:
            queryset = queryset.filter(genero=genero)
        
        if seguro:
            queryset = queryset.filter(seguro_medico=seguro)
        
        if region:
            queryset = queryset.filter(direccion_region=region)
        
        if rut:
            # Limpiar RUT para búsqueda
            rut_limpio = rut.replace('.', '').replace('-', '')
            queryset = queryset.filter(rut__icontains=rut_limpio)
        
        return queryset.order_by('-fecha_ingreso', '-fecha_actualizacion')
    
    # ============================================
    # ENDPOINTS BÁSICOS MEJORADOS
    # ============================================
    
    def create(self, request, *args, **kwargs):
        """
        Crea un nuevo paciente con validación completa del RUT.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con serializer completo
        instance = serializer.instance
        output_serializer = PacienteSerializer(instance)
        
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    # ============================================
    # ENDPOINTS DE INFORMACIÓN ESPECÍFICA
    # ============================================
    
    @action(detail=True, methods=['get'])
    def datos_medicos(self, request, pk=None):
        """
        Obtiene información médica completa del paciente.
        
        GET /api/pacientes/{id}/datos_medicos/
        """
        paciente = self.get_object()
        info_medica = paciente.obtener_informacion_completa()
        
        return Response({
            'paciente_id': str(paciente.id),
            'rut': paciente.rut,
            'nombre_completo': paciente.nombre_completo,
            'informacion_medica': {
                'tipo_sangre': info_medica['tipo_sangre'],
                'peso': info_medica['peso'],
                'altura': info_medica['altura'],
                'imc': info_medica['imc'],
                'categoria_imc': info_medica['categoria_imc'],
                'alergias': info_medica['alergias'],
                'condiciones_preexistentes': info_medica['condiciones_preexistentes'],
                'medicamentos': info_medica['medicamentos'],
            },
            'alertas': {
                'tiene_alergias': paciente.tiene_alergias(),
                'tiene_condiciones': paciente.tiene_condiciones_preexistentes(),
            }
        })
    
    @action(detail=True, methods=['get'])
    def datos_contacto(self, request, pk=None):
        """
        Obtiene información de contacto y dirección completa.
        
        GET /api/pacientes/{id}/datos_contacto/
        """
        paciente = self.get_object()
        serializer = PacienteDatosContactoSerializer(paciente)
        
        return Response({
            'paciente_id': str(paciente.id),
            'rut': paciente.rut,
            'nombre_completo': paciente.nombre_completo,
            'contacto': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def seguro_medico(self, request, pk=None):
        """
        Obtiene información del seguro médico.
        
        GET /api/pacientes/{id}/seguro_medico/
        """
        paciente = self.get_object()
        serializer = PacienteSeguroMedicoSerializer(paciente)
        
        return Response({
            'paciente_id': str(paciente.id),
            'rut': paciente.rut,
            'nombre_completo': paciente.nombre_completo,
            'seguro': serializer.data
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
            'rut': paciente.rut,
            'nombre': paciente.nombre_completo,
            'peso': float(paciente.peso),
            'altura': paciente.altura,
            'imc': imc,
            'categoria_imc': categoria,
            'recomendacion': self._get_recomendacion_imc(categoria)
        })
    
    # ============================================
    # ENDPOINTS DE AGRUPACIÓN Y ESTADÍSTICAS
    # ============================================
    
    @action(detail=False, methods=['get'])
    def por_seguro(self, request):
        """
        Agrupa pacientes por tipo de seguro médico.
        
        GET /api/pacientes/por_seguro/
        """
        queryset = self.get_queryset()
        
        resultado = {}
        for seguro_key, seguro_label in Paciente.SEGURO_MEDICO_CHOICES:
            pacientes = queryset.filter(seguro_medico=seguro_key)
            resultado[seguro_key] = {
                'label': seguro_label,
                'count': pacientes.count(),
                'porcentaje': round(
                    (pacientes.count() / queryset.count() * 100) if queryset.count() > 0 else 0,
                    2
                )
            }
        
        return Response(resultado)
    
    @action(detail=False, methods=['get'])
    def por_region(self, request):
        """
        Agrupa pacientes por región.
        
        GET /api/pacientes/por_region/
        """
        queryset = self.get_queryset()
        
        resultado = {}
        for region_key, region_label in Paciente.REGION_CHOICES:
            pacientes = queryset.filter(direccion_region=region_key)
            resultado[region_key] = {
                'label': region_label,
                'count': pacientes.count(),
                'porcentaje': round(
                    (pacientes.count() / queryset.count() * 100) if queryset.count() > 0 else 0,
                    2
                )
            }
        
        return Response(resultado)
    
    @action(detail=False, methods=['get'])
    def estadisticas_completas(self, request):
        """
        Estadísticas completas y detalladas.
        
        GET /api/pacientes/estadisticas_completas/
        """
        queryset = self.get_queryset()
        
        # Estadísticas por seguro
        por_seguro = {}
        for seguro_key, seguro_label in Paciente.SEGURO_MEDICO_CHOICES:
            count = queryset.filter(seguro_medico=seguro_key).count()
            por_seguro[seguro_key] = {
                'label': seguro_label,
                'count': count
            }
        
        # Estadísticas por región
        por_region = {}
        for region_key, region_label in Paciente.REGION_CHOICES:
            count = queryset.filter(direccion_region=region_key).count()
            por_region[region_key] = {
                'label': region_label,
                'count': count
            }
        
        # Datos médicos completos
        con_alergias = queryset.exclude(alergias='').count()
        con_condiciones = queryset.exclude(condiciones_preexistentes='').count()
        con_peso_altura = queryset.exclude(peso__isnull=True).exclude(altura__isnull=True).count()
        
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
        
        # Estadísticas por género
        por_genero = {}
        for genero_key, genero_label in Paciente.GENERO_CHOICES:
            count = queryset.filter(genero=genero_key).count()
            por_genero[genero_key] = {
                'label': genero_label,
                'count': count
            }
        
        # Estadísticas por tipo de sangre
        por_tipo_sangre = {}
        for tipo_key, tipo_label in Paciente.TIPO_SANGRE_CHOICES:
            count = queryset.filter(tipo_sangre=tipo_key).count()
            por_tipo_sangre[tipo_key] = {
                'label': tipo_label,
                'count': count
            }
        
        # Estadísticas por estado
        por_estado = {}
        for estado_key, estado_label in Paciente.ESTADO_CHOICES:
            count = queryset.filter(estado_actual=estado_key).count()
            por_estado[estado_key] = {
                'label': estado_label,
                'count': count
            }
        
        # Estadísticas por urgencia
        por_urgencia = {}
        for urgencia_key, urgencia_label in Paciente.URGENCIA_CHOICES:
            count = queryset.filter(nivel_urgencia=urgencia_key).count()
            por_urgencia[urgencia_key] = {
                'label': urgencia_label,
                'count': count
            }
        
        return Response({
            'total_pacientes': queryset.count(),
            'activos': queryset.filter(activo=True).count(),
            'inactivos': queryset.filter(activo=False).count(),
            'por_estado': por_estado,
            'por_urgencia': por_urgencia,
            'por_seguro': por_seguro,
            'por_region': por_region,
            'por_genero': por_genero,
            'por_tipo_sangre': por_tipo_sangre,
            'datos_medicos': {
                'con_alergias': con_alergias,
                'con_condiciones_preexistentes': con_condiciones,
                'con_peso_y_altura': con_peso_altura,
                'porcentaje_datos_completos': round(
                    (con_peso_altura / queryset.count() * 100) if queryset.count() > 0 else 0,
                    2
                )
            },
            'imc': {
                'promedio': round(imc_promedio, 2) if imc_promedio else None,
                'total_calculable': len(pacientes_con_imc),
                'por_categoria': categorias_imc
            }
        })
    
    # ============================================
    # ENDPOINTS DE VALIDACIÓN Y BÚSQUEDA
    # ============================================
    
    @action(detail=False, methods=['post'])
    def validar_rut(self, request):
        """
        Valida un RUT chileno.
        
        POST /api/pacientes/validar_rut/
        Body: {"rut": "12.345.678-9"}
        """
        rut = request.data.get('rut', '')
        
        if not rut:
            return Response({
                'valido': False,
                'mensaje': 'Debe proporcionar un RUT.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Formatear si viene sin formato
        if not ('.' in rut and '-' in rut):
            rut = Paciente.formatear_rut(rut)
        
        es_valido = Paciente.validar_rut(rut)
        
        # Verificar si existe
        existe = Paciente.objects.filter(rut=rut).exists()
        
        return Response({
            'rut': rut,
            'valido': es_valido,
            'existe': existe,
            'mensaje': 'RUT válido' if es_valido else 'RUT inválido - verifique el dígito verificador'
        })
    
    @action(detail=False, methods=['post'])
    def buscar_por_rut(self, request):
        """
        Busca un paciente por RUT.
        
        POST /api/pacientes/buscar_por_rut/
        Body: {"rut": "12.345.678-9"}
        """
        rut = request.data.get('rut', '')
        
        if not rut:
            return Response({
                'error': 'Debe proporcionar un RUT.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Formatear si viene sin formato
        if not ('.' in rut and '-' in rut):
            rut = Paciente.formatear_rut(rut)
        
        try:
            paciente = Paciente.objects.get(rut=rut)
            serializer = PacienteSerializer(paciente)
            return Response({
                'encontrado': True,
                'paciente': serializer.data
            })
        except Paciente.DoesNotExist:
            return Response({
                'encontrado': False,
                'mensaje': f'No se encontró ningún paciente con el RUT {rut}'
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
    
    # ============================================
    # ENDPOINTS ORIGINALES MANTENIDOS
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
    def con_alergias(self, request):
        """Lista pacientes que tienen alergias registradas"""
        pacientes = self.get_queryset().exclude(alergias='')
        serializer = self.get_serializer(pacientes, many=True)
        
        return Response({
            'count': pacientes.count(),
            'pacientes': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo_sangre(self, request):
        """Agrupa pacientes por tipo de sangre"""
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