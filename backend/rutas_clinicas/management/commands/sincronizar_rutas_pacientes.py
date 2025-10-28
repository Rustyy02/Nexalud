# backend/rutas_clinicas/management/commands/sincronizar_rutas_pacientes.py
"""
Comando para sincronizar rutas clínicas con pacientes.

Uso:
    python manage.py sincronizar_rutas_pacientes
    python manage.py sincronizar_rutas_pacientes --dry-run
    python manage.py sincronizar_rutas_pacientes --force
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from rutas_clinicas.models import RutaClinica


class Command(BaseCommand):
    help = 'Sincroniza las etapas de las rutas clínicas con sus pacientes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se sincronizaría sin hacer cambios',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sincroniza todas las rutas, incluso las ya sincronizadas',
        )
        parser.add_argument(
            '--estado',
            type=str,
            choices=['INICIADA', 'EN_PROGRESO', 'PAUSADA', 'COMPLETADA', 'CANCELADA'],
            help='Sincronizar solo rutas en este estado',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        estado = options.get('estado')
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('SINCRONIZACIÓN DE RUTAS CLÍNICAS CON PACIENTES'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN: No se realizarán cambios'))
            self.stdout.write('')
        
        # Obtener rutas activas
        queryset = RutaClinica.objects.select_related('paciente')
        
        if estado:
            queryset = queryset.filter(estado=estado)
            self.stdout.write(f"📊 Filtrando por estado: {estado}")
        else:
            # Por defecto, solo rutas activas
            queryset = queryset.filter(estado__in=['INICIADA', 'EN_PROGRESO'])
            self.stdout.write("📊 Sincronizando rutas activas (INICIADA, EN_PROGRESO)")
        
        self.stdout.write('')
        
        total_rutas = queryset.count()
        self.stdout.write(f"📋 Total de rutas a revisar: {total_rutas}")
        self.stdout.write('')
        
        if total_rutas == 0:
            self.stdout.write(self.style.WARNING('⚠️  No hay rutas para sincronizar'))
            return
        
        # Contadores
        sincronizadas = 0
        ya_sincronizadas = 0
        sin_etapa = 0
        errores = 0
        
        # Procesar cada ruta
        for i, ruta in enumerate(queryset, 1):
            try:
                # Información de la ruta
                etapa_ruta = ruta.etapa_actual
                etapa_paciente = ruta.paciente.etapa_actual
                
                self.stdout.write(
                    f"[{i}/{total_rutas}] Ruta {str(ruta.id)[:8]}... | "
                    f"Paciente: {ruta.paciente.identificador_hash[:12]}..."
                )
                
                # Caso 1: Sin etapa actual
                if not etapa_ruta:
                    if etapa_paciente:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠️  Ruta sin etapa, pero paciente tiene: {ruta.paciente.get_etapa_actual_display()}"
                            )
                        )
                        if not dry_run:
                            ruta.paciente.limpiar_etapa()
                            self.stdout.write(self.style.SUCCESS("  ✓ Etapa del paciente limpiada"))
                            sincronizadas += 1
                        else:
                            self.stdout.write("  🔍 Se limpiaría la etapa del paciente")
                            sincronizadas += 1
                    else:
                        self.stdout.write("  ✓ Sin etapa en ambos (OK)")
                        ya_sincronizadas += 1
                    sin_etapa += 1
                    continue
                
                # Caso 2: Ya sincronizada
                if etapa_ruta == etapa_paciente and not force:
                    self.stdout.write(
                        f"  ✓ Ya sincronizada: {ruta.get_etapa_actual_display()}"
                    )
                    ya_sincronizadas += 1
                    continue
                
                # Caso 3: Necesita sincronización
                if etapa_ruta != etapa_paciente or force:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  🔄 Desincronizada:"
                        )
                    )
                    self.stdout.write(
                        f"     Ruta: {ruta.get_etapa_actual_display()}"
                    )
                    self.stdout.write(
                        f"     Paciente: {ruta.paciente.get_etapa_actual_display() if etapa_paciente else 'Sin etapa'}"
                    )
                    
                    if not dry_run:
                        ruta.paciente.actualizar_etapa(etapa_ruta)
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"  ✓ Sincronizada → {ruta.get_etapa_actual_display()}"
                            )
                        )
                        sincronizadas += 1
                    else:
                        self.stdout.write(
                            f"  🔍 Se sincronizaría → {ruta.get_etapa_actual_display()}"
                        )
                        sincronizadas += 1
                
                self.stdout.write('')
                
            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ Error al sincronizar ruta {ruta.id}: {str(e)}"
                    )
                )
                self.stdout.write('')
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN: Ningún cambio fue realizado'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Sincronización completada'))
        
        self.stdout.write('')
        self.stdout.write(f"📊 Total procesadas: {total_rutas}")
        self.stdout.write(f"✓ Sincronizadas: {sincronizadas}")
        self.stdout.write(f"✓ Ya sincronizadas: {ya_sincronizadas}")
        self.stdout.write(f"— Sin etapa: {sin_etapa}")
        self.stdout.write(f"❌ Errores: {errores}")
        self.stdout.write('')
        self.stdout.write(f"🕐 Ejecutado: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Sugerencias
        if sincronizadas > 0 and dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('💡 Para aplicar los cambios, ejecuta:'))
            self.stdout.write('   python manage.py sincronizar_rutas_pacientes')
        
        if errores > 0:
            self.stdout.write('')
            self.stdout.write(
                self.style.ERROR(
                    f'⚠️  Se encontraron {errores} errores. Revisa los logs para más detalles.'
                )
            )
