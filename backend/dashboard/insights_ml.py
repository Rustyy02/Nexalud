# backend/dashboard/insights_ml.py
"""
Esta es la base para generar insights de los datos del dashboard, aún no es machine learning automatizado, pero es un buen punto para partir.
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from atenciones.models import Atencion, Medico
from boxes.models import Box
from pacientes.models import Paciente
from users.models import User
from rutas_clinicas.models import RutaClinica


class NexaThinkAnalyzer:
    """Analizador de insights basado en datos históricos y en tiempo real"""
    
    def __init__(self):
        self.insights = []
        self.ahora = timezone.now()
        self.hoy = self.ahora.date()
        
    def generar_insights(self):
        """Genera todos los insights disponibles"""
        self.insights = []
        
        # Análisis de médicos
        self._analizar_medicos()
        
        # Análisis de boxes
        self._analizar_boxes()
        
        # Análisis de deserción
        self._analizar_desercion()
        
        # Análisis de tiempos de espera
        self._analizar_tiempos_espera()
        
        # Análisis de rutas clínicas
        self._analizar_rutas_clinicas()
        
        # Análisis de horarios pico
        self._analizar_horarios_pico()
        
        # Ordenar por prioridad
        self.insights.sort(key=lambda x: self._get_prioridad_valor(x['priority']), reverse=True)
        
        return self.insights
    
    def _get_prioridad_valor(self, priority):
        """Convierte prioridad a valor numérico para ordenar"""
        prioridades = {'crítica': 4, 'alta': 3, 'media': 2, 'baja': 1}
        return prioridades.get(priority, 0)
    
    def _analizar_medicos(self):
        """Analiza el desempeño de los médicos"""
        # ✅ CORREGIDO: Usar User con rol MEDICO
        from users.models import User
        
        # Tiempo promedio por médico (últimos 30 días)
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
                tiempo_promedio = atenciones.aggregate(
                    promedio=Avg('duracion_real')
                )['promedio']
                
                nombre_completo = medico.get_full_name() or medico.username
                
                # Baseline: 20 minutos es lo esperado
                if tiempo_promedio > 30:
                    self.insights.append({
                        'type': 'warning',
                        'icon': 'Clock',
                        'message': f'{nombre_completo} está tardando más de lo normal en sus atenciones ({tiempo_promedio:.0f} min promedio)',
                        'recommendation': 'Considerar revisión de carga de trabajo o capacitación en eficiencia',
                        'priority': 'alta',
                        'data': {
                            'medico_id': str(medico.id),
                            'medico_nombre': nombre_completo,
                            'tiempo_promedio': round(tiempo_promedio, 1),
                            'atenciones_analizadas': atenciones.count()
                        }
                    })
                elif tiempo_promedio < 15:
                    self.insights.append({
                        'type': 'success',
                        'icon': 'CheckCircle',
                        'message': f'{nombre_completo} mantiene tiempos óptimos de atención ({tiempo_promedio:.0f} min)',
                        'recommendation': 'Considerar como referencia de buenas prácticas',
                        'priority': 'baja',
                        'data': {
                            'medico_id': str(medico.id),
                            'medico_nombre': nombre_completo,
                            'tiempo_promedio': round(tiempo_promedio, 1)
                        }
                    })
    
    def _analizar_boxes(self):
        """Analiza el uso de boxes"""
        boxes = Box.objects.filter(activo=True)
        
        for box in boxes:
            # Calcular ocupación del día
            porcentaje_ocupacion = box.calcular_tiempo_ocupacion_hoy()
            
            if porcentaje_ocupacion < 30:
                self.insights.append({
                    'type': 'info',
                    'icon': 'Activity',
                    'message': f'El {box.numero} está siendo ocupado en menor tiempo del día ({porcentaje_ocupacion:.0f}% de ocupación)',
                    'recommendation': 'Optimizar asignación de recursos o considerar mantenimiento programado',
                    'priority': 'media',
                    'data': {
                        'box_id': str(box.id),
                        'box_numero': box.numero,
                        'ocupacion': round(porcentaje_ocupacion, 1)
                    }
                })
            elif porcentaje_ocupacion > 85:
                self.insights.append({
                    'type': 'warning',
                    'icon': 'AlertCircle',
                    'message': f'El {box.numero} tiene alta ocupación ({porcentaje_ocupacion:.0f}%)',
                    'recommendation': 'Considerar redistribución de carga o habilitar box adicional',
                    'priority': 'alta',
                    'data': {
                        'box_id': str(box.id),
                        'box_numero': box.numero,
                        'ocupacion': round(porcentaje_ocupacion, 1)
                    }
                })
    
    def _analizar_desercion(self):
        """Analiza tasa de deserción de pacientes"""
        # Pacientes que iniciaron pero no completaron ruta
        hace_30_dias = self.ahora - timedelta(days=30)
        
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
                    'message': f'Existe mucha gente desertando o no completando su proceso clínico ({tasa_desercion:.0f}%)',
                    'recommendation': 'Implementar sistema de recordatorios y mejorar experiencia del paciente',
                    'priority': 'crítica',
                    'data': {
                        'tasa_desercion': round(tasa_desercion, 1),
                        'rutas_incompletas': rutas_incompletas,
                        'rutas_totales': rutas_iniciadas
                    }
                })
    
    def _analizar_tiempos_espera(self):
        """Analiza tiempos de espera"""
        pacientes_en_espera = Paciente.objects.filter(
            estado_actual='EN_ESPERA',
            activo=True
        )
        
        if pacientes_en_espera.count() > 10:
            self.insights.append({
                'type': 'warning',
                'icon': 'Clock',
                'message': f'Hay {pacientes_en_espera.count()} pacientes en espera',
                'recommendation': 'Considerar apertura de boxes adicionales o redistribución de personal',
                'priority': 'alta',
                'data': {
                    'pacientes_espera': pacientes_en_espera.count()
                }
            })
    
    def _analizar_rutas_clinicas(self):
        """Analiza el estado de las rutas clínicas"""
        rutas_con_retraso = []
        
        rutas_activas = RutaClinica.objects.filter(
            estado='EN_PROGRESO'
        )
        
        for ruta in rutas_activas:
            retrasos = ruta.detectar_retrasos()
            if retrasos:
                rutas_con_retraso.append(ruta)
        
        if len(rutas_con_retraso) > 0:
            self.insights.append({
                'type': 'warning',
                'icon': 'AlertCircle',
                'message': f'{len(rutas_con_retraso)} ruta(s) clínica(s) con retrasos detectados',
                'recommendation': 'Revisar causas de retraso y ajustar tiempos estimados',
                'priority': 'alta',
                'data': {
                    'rutas_con_retraso': len(rutas_con_retraso)
                }
            })
    
    def _analizar_horarios_pico(self):
        """Detecta horarios pico de demanda"""
        # Analizar atenciones de los últimos 7 días por hora
        hace_7_dias = self.ahora - timedelta(days=7)
        
        atenciones = Atencion.objects.filter(
            fecha_hora_inicio__gte=hace_7_dias
        )
        
        # Agrupar por hora
        horas_conteo = {}
        for atencion in atenciones:
            hora = atencion.fecha_hora_inicio.hour
            horas_conteo[hora] = horas_conteo.get(hora, 0) + 1
        
        if horas_conteo:
            # Encontrar las 2 horas con más demanda
            horas_ordenadas = sorted(horas_conteo.items(), key=lambda x: x[1], reverse=True)
            horas_pico = horas_ordenadas[:2]
            
            horas_str = ", ".join([f"{h:02d}:00-{h+1:02d}:00" for h, _ in horas_pico])
            
            self.insights.append({
                'type': 'info',
                'icon': 'TrendingUp',
                'message': f'Se detectan picos de demanda en horarios {horas_str}',
                'recommendation': 'Incrementar personal durante estas horas para mejorar tiempos de atención',
                'priority': 'media',
                'data': {
                    'horas_pico': [h for h, _ in horas_pico],
                    'atenciones_promedio': sum(c for _, c in horas_pico) / len(horas_pico)
                }
            })