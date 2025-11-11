from django.db.models import Avg, Count, Q, F, Sum
from django.utils import timezone
from datetime import timedelta
from atenciones.models import Atencion, Medico
from boxes.models import Box, OcupacionManual
from pacientes.models import Paciente
from users.models import User
from rutas_clinicas.models import RutaClinica

class NexaThinkAnalyzer:
    # Analizador mejorado con insights completos del sistema
    
    def __init__(self):
        self.insights = []
        self.ahora = timezone.now()
        self.hoy = self.ahora.date()
        
    def generar_insights(self):
        # Genera todos los insights disponibles
        self.insights = []
        
        # ========== ANÁLISIS ==========
        self._analizar_medicos()
        self._analizar_boxes()
        self._analizar_desercion()
        self._analizar_tiempos_espera()
        self._analizar_rutas_clinicas()
        self._analizar_horarios_pico()
        self._analizar_atrasos_reportados()  
        self._analizar_cronometros_atenciones() 
        self._analizar_ocupaciones_manuales()  
        self._analizar_etapas_clinicas()  
        self._analizar_sincronizacion_paciente_ruta()  
        self._analizar_especialidades_demanda()  
        self._analizar_pacientes_criticos()  
        self._analizar_eficiencia_boxes_por_especialidad()  
        self._analizar_patrones_cancelacion()  
        self._analizar_tendencias_semanales()  
        
        # Ordenar por prioridad
        self.insights.sort(key=lambda x: self._get_prioridad_valor(x['priority']), reverse=True)
        
        return self.insights
    
    def _get_prioridad_valor(self, priority):
        prioridades = {'crítica': 4, 'alta': 3, 'media': 2, 'baja': 1}
        return prioridades.get(priority, 0)
    
    # ========== ANÁLISIS MEDICOS ==========
    
    def _analizar_medicos(self):
        """Analiza el desempeño de los médicos con más métricas"""
        from users.models import User
        
        hace_30_dias = self.ahora - timedelta(days=30)
        medicos = User.objects.filter(rol='MEDICO', is_active=True)
        
        for medico in medicos:
            atenciones = Atencion.objects.filter(
                medico=medico,
                fecha_hora_inicio__gte=hace_30_dias,
                estado='COMPLETADA',
                duracion_real__isnull=False
            )
            
            if atenciones.exists():
                tiempo_promedio = atenciones.aggregate(promedio=Avg('duracion_real'))['promedio']
                nombre_completo = medico.get_full_name() or medico.username
                
                # Analizar no presentados
                no_presentados = Atencion.objects.filter(
                    medico=medico,
                    fecha_hora_inicio__gte=hace_30_dias,
                    estado='NO_PRESENTADO'
                ).count()
                
                if no_presentados > 5:
                    self.insights.append({
                        'type': 'warning',
                        'icon': 'AlertCircle',
                        'message': f'{nombre_completo} tiene {no_presentados} pacientes no presentados en el último mes',
                        'recommendation': 'Revisar sistema de confirmación de citas y recordatorios',
                        'priority': 'alta',
                        'data': {
                            'medico_id': str(medico.id),
                            'no_presentados': no_presentados
                        }
                    })
                
                # Tiempo de atención
                if tiempo_promedio > 30:
                    self.insights.append({
                        'type': 'warning',
                        'icon': 'Clock',
                        'message': f'{nombre_completo} está tardando más de lo normal ({tiempo_promedio:.0f} min promedio)',
                        'recommendation': 'Considerar revisión de carga de trabajo o capacitación',
                        'priority': 'alta',
                        'data': {
                            'medico_id': str(medico.id),
                            'tiempo_promedio': round(tiempo_promedio, 1)
                        }
                    })
                elif tiempo_promedio < 15:
                    self.insights.append({
                        'type': 'success',
                        'icon': 'CheckCircle',
                        'message': f'{nombre_completo} mantiene tiempos óptimos ({tiempo_promedio:.0f} min)',
                        'recommendation': 'Considerar como referencia de buenas prácticas',
                        'priority': 'baja',
                        'data': {
                            'medico_id': str(medico.id),
                            'tiempo_promedio': round(tiempo_promedio, 1)
                        }
                    })
    
    
    def _analizar_atrasos_reportados(self):
        """Analiza atenciones con atraso reportado (sistema de 5 minutos)"""
        # Atenciones con atraso reportado activas
        atenciones_con_atraso = Atencion.objects.filter(
            atraso_reportado=True,
            estado__in=['PROGRAMADA', 'EN_ESPERA', 'EN_CURSO']
        )
        
        criticas = []
        for atencion in atenciones_con_atraso:
            if atencion.verificar_tiempo_atraso():
                criticas.append(atencion)
        
        if criticas:
            self.insights.append({
                'type': 'alert',
                'icon': 'AlertCircle',
                'message': f'⚠️ {len(criticas)} pacientes excedieron tiempo de espera (5 min)',
                'recommendation': 'Marcar como NO_PRESENTADO o contactar urgentemente',
                'priority': 'crítica',
                'data': {
                    'atenciones': [str(a.id) for a in criticas[:5]]
                }
            })
        
        # Total de atrasos del día
        atrasos_hoy = Atencion.objects.filter(
            atraso_reportado=True,
            fecha_reporte_atraso__date=self.hoy
        ).count()
        
        if atrasos_hoy > 10:
            self.insights.append({
                'type': 'warning',
                'icon': 'TrendingUp',
                'message': f'Alto número de atrasos reportados hoy: {atrasos_hoy}',
                'recommendation': 'Revisar sistema de confirmación de citas y puntualidad',
                'priority': 'alta',
                'data': {'atrasos_hoy': atrasos_hoy}
            })
    
    def _analizar_cronometros_atenciones(self):
        """Analiza atenciones con cronómetro activo"""
        atenciones_en_curso = Atencion.objects.filter(
            estado='EN_CURSO',
            inicio_cronometro__isnull=False
        )
        
        excedidas = []
        proximas_exceder = []
        
        for atencion in atenciones_en_curso:
            tiempo_transcurrido = (self.ahora - atencion.inicio_cronometro).total_seconds() / 60
            
            if tiempo_transcurrido > atencion.duracion_planificada:
                excedidas.append({
                    'atencion_id': str(atencion.id),
                    'box': atencion.box.numero,
                    'exceso': int(tiempo_transcurrido - atencion.duracion_planificada)
                })
            elif tiempo_transcurrido > (atencion.duracion_planificada * 0.8):
                proximas_exceder.append({
                    'atencion_id': str(atencion.id),
                    'box': atencion.box.numero,
                    'tiempo_restante': int(atencion.duracion_planificada - tiempo_transcurrido)
                })
        
        if excedidas:
            self.insights.append({
                'type': 'alert',
                'icon': 'Clock',
                'message': f'🕐 {len(excedidas)} atenciones excediendo tiempo planificado',
                'recommendation': f'Box {excedidas[0]["box"]} excedido por {excedidas[0]["exceso"]} min. Considerar finalizar.',
                'priority': 'crítica',
                'data': {'excedidas': excedidas}
            })
        
        if proximas_exceder:
            self.insights.append({
                'type': 'warning',
                'icon': 'Activity',
                'message': f'{len(proximas_exceder)} atenciones próximas a exceder tiempo',
                'recommendation': 'Preparar conclusión o notificar posible extensión',
                'priority': 'media',
                'data': {'proximas': proximas_exceder}
            })
    
    def _analizar_ocupaciones_manuales(self):
        """Analiza ocupaciones manuales de boxes"""
        from boxes.models import OcupacionManual
        
        ocupaciones_activas = OcupacionManual.objects.filter(
            activa=True
        )
        
        expiradas = []
        proximas_expirar = []
        
        for ocupacion in ocupaciones_activas:
            if ocupacion.debe_finalizar():
                expiradas.append({
                    'box': ocupacion.box.numero,
                    'duracion': ocupacion.duracion_minutos,
                    'motivo': ocupacion.motivo
                })
            else:
                tiempo_restante = (ocupacion.fecha_fin_programada - self.ahora).total_seconds() / 60
                if tiempo_restante <= 5:
                    proximas_expirar.append({
                        'box': ocupacion.box.numero,
                        'minutos_restantes': int(tiempo_restante)
                    })
        
        if expiradas:
            self.insights.append({
                'type': 'alert',
                'icon': 'Activity',
                'message': f'📦 {len(expiradas)} boxes con ocupación manual expirada',
                'recommendation': f'Liberar Box {expiradas[0]["box"]} - {expiradas[0]["motivo"]}',
                'priority': 'alta',
                'data': {'expiradas': expiradas}
            })
    
    def _analizar_etapas_clinicas(self):
        """Analiza el flujo de etapas clínicas"""
        # Rutas con retrasos en etapas específicas
        rutas_activas = RutaClinica.objects.filter(estado='EN_PROGRESO')
        
        etapas_retrasadas = {}
        for ruta in rutas_activas:
            retrasos = ruta.detectar_retrasos()
            for retraso in retrasos:
                etapa = retraso['etapa_label']
                if etapa not in etapas_retrasadas:
                    etapas_retrasadas[etapa] = 0
                etapas_retrasadas[etapa] += 1
        
        if etapas_retrasadas:
            etapa_critica = max(etapas_retrasadas.items(), key=lambda x: x[1])
            self.insights.append({
                'type': 'warning',
                'icon': 'AlertCircle',
                'message': f'📋 Cuello de botella en "{etapa_critica[0]}" ({etapa_critica[1]} retrasos)',
                'recommendation': 'Asignar más recursos o revisar proceso en esta etapa',
                'priority': 'alta',
                'data': {'etapas_retrasadas': etapas_retrasadas}
            })
        
        # Rutas pausadas por mucho tiempo
        rutas_pausadas_largo = RutaClinica.objects.filter(
            estado='PAUSADA',
            fecha_actualizacion__lt=self.ahora - timedelta(days=3)
        ).count()
        
        if rutas_pausadas_largo > 0:
            self.insights.append({
                'type': 'warning',
                'icon': 'TrendingUp',
                'message': f'{rutas_pausadas_largo} rutas pausadas por más de 3 días',
                'recommendation': 'Contactar pacientes para reanudar o cancelar definitivamente',
                'priority': 'media',
                'data': {'rutas_pausadas': rutas_pausadas_largo}
            })
    
    def _analizar_sincronizacion_paciente_ruta(self):
        """Verifica sincronización entre pacientes y rutas clínicas"""
        # Buscar desincronizaciones
        pacientes_desincronizados = 0
        
        rutas_activas = RutaClinica.objects.filter(
            estado__in=['EN_PROGRESO', 'INICIADA']
        ).select_related('paciente')
        
        for ruta in rutas_activas:
            if ruta.etapa_actual != ruta.paciente.etapa_actual:
                pacientes_desincronizados += 1
        
        if pacientes_desincronizados > 0:
            self.insights.append({
                'type': 'alert',
                'icon': 'AlertCircle',
                'message': f'⚠️ {pacientes_desincronizados} pacientes con etapa desincronizada',
                'recommendation': 'Ejecutar sincronización manual o revisar proceso de actualización',
                'priority': 'crítica',
                'data': {'desincronizados': pacientes_desincronizados}
            })
    
    def _analizar_especialidades_demanda(self):
        """Analiza demanda por especialidad médica"""
        from collections import defaultdict
        
        # Atenciones por especialidad en últimos 7 días
        hace_7_dias = self.ahora - timedelta(days=7)
        
        demanda = defaultdict(int)
        medicos_por_especialidad = defaultdict(int)
        
        medicos = User.objects.filter(rol='MEDICO', is_active=True)
        for medico in medicos:
            if medico.especialidad:
                medicos_por_especialidad[medico.get_especialidad_display()] += 1
                
                atenciones = Atencion.objects.filter(
                    medico=medico,
                    fecha_hora_inicio__gte=hace_7_dias
                ).count()
                
                demanda[medico.get_especialidad_display()] += atenciones
        
        # Encontrar especialidades sobrecargadas
        for especialidad, total_atenciones in demanda.items():
            num_medicos = medicos_por_especialidad[especialidad]
            if num_medicos > 0:
                promedio_por_medico = total_atenciones / num_medicos
                
                if promedio_por_medico > 50:  # Más de 50 atenciones por médico en 7 días
                    self.insights.append({
                        'type': 'warning',
                        'icon': 'TrendingUp',
                        'message': f'Alta demanda en {especialidad}: {promedio_por_medico:.0f} atenciones/médico',
                        'recommendation': 'Considerar contratar más médicos o redistribuir carga',
                        'priority': 'alta',
                        'data': {
                            'especialidad': especialidad,
                            'atenciones_promedio': promedio_por_medico,
                            'medicos': num_medicos
                        }
                    })
    
    def _analizar_pacientes_criticos(self):
        """Analiza pacientes con urgencia crítica"""
        pacientes_criticos = Paciente.objects.filter(
            nivel_urgencia='CRITICA',
            activo=True,
            estado_actual='EN_ESPERA'
        ).count()
        
        if pacientes_criticos > 0:
            self.insights.append({
                'type': 'alert',
                'icon': 'AlertCircle',
                'message': f'🚨 {pacientes_criticos} pacientes críticos en espera',
                'recommendation': 'Priorizar atención inmediata o activar protocolo de emergencia',
                'priority': 'crítica',
                'data': {'pacientes_criticos': pacientes_criticos}
            })
        
        # Pacientes críticos sin ruta clínica
        criticos_sin_ruta = Paciente.objects.filter(
            nivel_urgencia='CRITICA',
            activo=True
        ).exclude(
            rutas_clinicas__estado__in=['INICIADA', 'EN_PROGRESO']
        ).count()
        
        if criticos_sin_ruta > 0:
            self.insights.append({
                'type': 'warning',
                'icon': 'AlertCircle',
                'message': f'{criticos_sin_ruta} pacientes críticos sin ruta clínica activa',
                'recommendation': 'Iniciar ruta clínica urgente para estos pacientes',
                'priority': 'alta',
                'data': {'criticos_sin_ruta': criticos_sin_ruta}
            })
    
    def _analizar_eficiencia_boxes_por_especialidad(self):
        """Analiza eficiencia de boxes por especialidad"""
        boxes = Box.objects.filter(activo=True)
        
        for box in boxes:
            if box.especialidad != 'MULTIUSO':
                # Calcular uso en últimas 24 horas
                ayer = self.ahora - timedelta(days=1)
                atenciones_box = Atencion.objects.filter(
                    box=box,
                    fecha_hora_inicio__gte=ayer
                ).count()
                
                porcentaje_ocupacion = box.calcular_tiempo_ocupacion_hoy()
                
                if porcentaje_ocupacion < 20 and atenciones_box < 3:
                    self.insights.append({
                        'type': 'info',
                        'icon': 'Activity',
                        'message': f'Box {box.numero} ({box.get_especialidad_display()}) subutilizado',
                        'recommendation': 'Considerar reasignar a MULTIUSO temporalmente',
                        'priority': 'media',
                        'data': {
                            'box': box.numero,
                            'ocupacion': porcentaje_ocupacion,
                            'atenciones': atenciones_box
                        }
                    })
    
    def _analizar_patrones_cancelacion(self):
        """Analiza patrones de cancelación"""
        hace_30_dias = self.ahora - timedelta(days=30)
        
        # Atenciones canceladas
        cancelaciones = Atencion.objects.filter(
            estado='CANCELADA',
            fecha_actualizacion__gte=hace_30_dias
        ).count()
        
        # Rutas canceladas
        rutas_canceladas = RutaClinica.objects.filter(
            estado='CANCELADA',
            fecha_actualizacion__gte=hace_30_dias
        ).count()
        
        total_atenciones = Atencion.objects.filter(
            fecha_hora_inicio__gte=hace_30_dias
        ).count()
        
        if total_atenciones > 0:
            tasa_cancelacion = (cancelaciones / total_atenciones) * 100
            
            if tasa_cancelacion > 15:
                self.insights.append({
                    'type': 'warning',
                    'icon': 'TrendingUp',
                    'message': f'Alta tasa de cancelación: {tasa_cancelacion:.1f}%',
                    'recommendation': 'Investigar causas y mejorar confirmación de citas',
                    'priority': 'alta',
                    'data': {
                        'cancelaciones': cancelaciones,
                        'rutas_canceladas': rutas_canceladas,
                        'tasa': tasa_cancelacion
                    }
                })
    
    def _analizar_tendencias_semanales(self):
        """Analiza tendencias y patrones semanales"""
        # Día de la semana con más atenciones
        from django.db.models import Count
        from django.db.models.functions import ExtractWeekDay
        
        hace_30_dias = self.ahora - timedelta(days=30)
        
        atenciones_por_dia = Atencion.objects.filter(
            fecha_hora_inicio__gte=hace_30_dias
        ).annotate(
            dia_semana=ExtractWeekDay('fecha_hora_inicio')
        ).values('dia_semana').annotate(
            total=Count('id')
        ).order_by('-total')
        
        if atenciones_por_dia:
            dias_nombres = {
                1: 'Domingo', 2: 'Lunes', 3: 'Martes', 
                4: 'Miércoles', 5: 'Jueves', 6: 'Viernes', 7: 'Sábado'
            }
            
            dia_mas_ocupado = atenciones_por_dia[0]
            dia_menos_ocupado = atenciones_por_dia.last()
            
            if dia_mas_ocupado['total'] > dia_menos_ocupado['total'] * 2:
                self.insights.append({
                    'type': 'info',
                    'icon': 'TrendingUp',
                    'message': f'Desbalance semanal: {dias_nombres[dia_mas_ocupado["dia_semana"]]} con {dia_mas_ocupado["total"]} atenciones',
                    'recommendation': f'Redistribuir citas hacia {dias_nombres[dia_menos_ocupado["dia_semana"]]}',
                    'priority': 'media',
                    'data': {
                        'dia_ocupado': dias_nombres[dia_mas_ocupado["dia_semana"]],
                        'dia_libre': dias_nombres[dia_menos_ocupado["dia_semana"]]
                    }
                })
    
    # Mantener los métodos existentes mejorados...
    def _analizar_boxes(self):
        """Analiza el uso de boxes con más detalle"""
        boxes = Box.objects.filter(activo=True)
        
        boxes_criticos = []
        for box in boxes:
            porcentaje_ocupacion = box.calcular_tiempo_ocupacion_hoy()
            
            # Verificar si hay ocupación manual activa
            tiene_ocupacion_manual = OcupacionManual.objects.filter(
                box=box,
                activa=True
            ).exists()
            
            if porcentaje_ocupacion < 30 and not tiene_ocupacion_manual:
                boxes_criticos.append(box)
            elif porcentaje_ocupacion > 85:
                self.insights.append({
                    'type': 'warning',
                    'icon': 'AlertCircle',
                    'message': f'Box {box.numero} con alta ocupación ({porcentaje_ocupacion:.0f}%)',
                    'recommendation': 'Redistribuir carga o habilitar box adicional',
                    'priority': 'alta',
                    'data': {
                        'box_id': str(box.id),
                        'box_numero': box.numero,
                        'ocupacion': round(porcentaje_ocupacion, 1)
                    }
                })
        
        if len(boxes_criticos) >= 3:
            self.insights.append({
                'type': 'info',
                'icon': 'Activity',
                'message': f'{len(boxes_criticos)} boxes subutilizados (menos del 30% de ocupación)',
                'recommendation': 'Optimizar asignación de recursos o programar mantenimientos',
                'priority': 'media',
                'data': {
                    'boxes': [b.numero for b in boxes_criticos[:5]]
                }
            })
    
    def _analizar_desercion(self):
        """Analiza deserción con más contexto"""
        hace_30_dias = self.ahora - timedelta(days=30)
        
        # Deserción de rutas
        rutas_iniciadas = RutaClinica.objects.filter(
            fecha_inicio__gte=hace_30_dias
        ).count()
        
        if rutas_iniciadas > 0:
            rutas_incompletas = RutaClinica.objects.filter(
                fecha_inicio__gte=hace_30_dias,
                estado__in=['CANCELADA', 'PAUSADA']
            ).count()
            
            tasa_desercion = (rutas_incompletas / rutas_iniciadas) * 100
            
            if tasa_desercion > 20:
                self.insights.append({
                    'type': 'alert',
                    'icon': 'AlertCircle',
                    'message': f'Alta tasa de deserción: {tasa_desercion:.0f}%',
                    'recommendation': 'Implementar sistema de seguimiento y recordatorios automatizados',
                    'priority': 'crítica',
                    'data': {
                        'tasa_desercion': round(tasa_desercion, 1),
                        'rutas_incompletas': rutas_incompletas,
                        'rutas_totales': rutas_iniciadas
                    }
                })
        
        # No presentados
        no_presentados_hoy = Atencion.objects.filter(
            estado='NO_PRESENTADO',
            fecha_actualizacion__date=self.hoy
        ).count()
        
        if no_presentados_hoy > 5:
            self.insights.append({
                'type': 'warning',
                'icon': 'AlertCircle',
                'message': f'{no_presentados_hoy} pacientes no se presentaron hoy',
                'recommendation': 'Revisar sistema de confirmación de citas',
                'priority': 'alta',
                'data': {'no_presentados': no_presentados_hoy}
            })
    
    def _analizar_tiempos_espera(self):
        """Analiza tiempos de espera con más detalle"""
        pacientes_en_espera = Paciente.objects.filter(
            estado_actual='EN_ESPERA',
            activo=True
        )
        
        total_espera = pacientes_en_espera.count()
        
        if total_espera > 10:
            # Analizar por urgencia
            criticos_esperando = pacientes_en_espera.filter(nivel_urgencia='CRITICA').count()
            alta_esperando = pacientes_en_espera.filter(nivel_urgencia='ALTA').count()
            
            if criticos_esperando > 0:
                self.insights.append({
                    'type': 'alert',
                    'icon': 'AlertCircle',
                    'message': f'🚨 {criticos_esperando} pacientes CRÍTICOS en espera',
                    'recommendation': 'ATENCIÓN INMEDIATA REQUERIDA',
                    'priority': 'crítica',
                    'data': {
                        'criticos': criticos_esperando,
                        'total_espera': total_espera
                    }
                })
            elif alta_esperando > 3:
                self.insights.append({
                    'type': 'warning',
                    'icon': 'Clock',
                    'message': f'{alta_esperando} pacientes de alta prioridad esperando',
                    'recommendation': 'Priorizar estos pacientes en las próximas atenciones',
                    'priority': 'alta',
                    'data': {
                        'alta_prioridad': alta_esperando,
                        'total_espera': total_espera
                    }
                })
            else:
                self.insights.append({
                    'type': 'warning',
                    'icon': 'Clock',
                    'message': f'{total_espera} pacientes en espera',
                    'recommendation': 'Considerar apertura de boxes adicionales',
                    'priority': 'media',
                    'data': {'pacientes_espera': total_espera}
                })
    
    def _analizar_rutas_clinicas(self):
        """Analiza rutas clínicas con retrasos específicos por etapa"""
        rutas_con_retraso = []
        etapas_problematicas = {}
        
        rutas_activas = RutaClinica.objects.filter(estado='EN_PROGRESO')
        
        for ruta in rutas_activas:
            retrasos = ruta.detectar_retrasos()
            if retrasos:
                rutas_con_retraso.append(ruta)
                for retraso in retrasos:
                    etapa = retraso['etapa_label']
                    if etapa not in etapas_problematicas:
                        etapas_problematicas[etapa] = {
                            'count': 0,
                            'retraso_promedio': 0,
                            'retrasos': []
                        }
                    etapas_problematicas[etapa]['count'] += 1
                    etapas_problematicas[etapa]['retrasos'].append(retraso['retraso_minutos'])
        
        # Calcular promedios
        for etapa, data in etapas_problematicas.items():
            if data['retrasos']:
                data['retraso_promedio'] = sum(data['retrasos']) / len(data['retrasos'])
        
        if etapas_problematicas:
            # Encontrar la etapa más problemática
            etapa_critica = max(etapas_problematicas.items(), 
                              key=lambda x: x[1]['count'])
            
            self.insights.append({
                'type': 'warning',
                'icon': 'AlertCircle',
                'message': f'Etapa "{etapa_critica[0]}" con {etapa_critica[1]["count"]} retrasos',
                'recommendation': f'Revisar proceso y recursos en esta etapa. Retraso promedio: {etapa_critica[1]["retraso_promedio"]:.0f} min',
                'priority': 'alta',
                'data': {
                    'rutas_con_retraso': len(rutas_con_retraso),
                    'etapas_problematicas': etapas_problematicas
                }
            })
    
    def _analizar_horarios_pico(self):
        """Analiza horarios pico con predicción"""
        hace_7_dias = self.ahora - timedelta(days=7)
        
        atenciones = Atencion.objects.filter(
            fecha_hora_inicio__gte=hace_7_dias
        )
        
        horas_conteo = {}
        for atencion in atenciones:
            hora = atencion.fecha_hora_inicio.hour
            horas_conteo[hora] = horas_conteo.get(hora, 0) + 1
        
        if horas_conteo:
            horas_ordenadas = sorted(horas_conteo.items(), key=lambda x: x[1], reverse=True)
            horas_pico = horas_ordenadas[:3]
            
            # Verificar si estamos cerca de una hora pico
            hora_actual = self.ahora.hour
            proxima_hora_pico = None
            
            for hora, conteo in horas_pico:
                if hora > hora_actual and hora - hora_actual <= 2:
                    proxima_hora_pico = hora
                    break
            
            if proxima_hora_pico:
                self.insights.append({
                    'type': 'info',
                    'icon': 'TrendingUp',
                    'message': f'⏰ Hora pico aproximándose a las {proxima_hora_pico:02d}:00',
                    'recommendation': 'Preparar personal adicional y verificar disponibilidad de boxes',
                    'priority': 'media',
                    'data': {
                        'hora_pico': proxima_hora_pico,
                        'atenciones_esperadas': horas_conteo.get(proxima_hora_pico, 0) // 7
                    }
                })
            
            # Horarios generales
            horas_str = ", ".join([f"{h:02d}:00" for h, _ in horas_pico[:2]])
            self.insights.append({
                'type': 'info',
                'icon': 'TrendingUp',
                'message': f'Horarios pico detectados: {horas_str}',
                'recommendation': 'Mantener máxima capacidad en estos horarios',
                'priority': 'baja',
                'data': {
                    'horas_pico': [h for h, _ in horas_pico],
                    'promedio_atenciones': sum(c for _, c in horas_pico[:2]) / (2 * 7)
                }
            })