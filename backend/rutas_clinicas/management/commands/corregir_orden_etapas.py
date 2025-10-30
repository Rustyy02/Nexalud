# backend/rutas_clinicas/management/commands/corregir_orden_etapas.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from rutas_clinicas.models import RutaClinica


class Command(BaseCommand):
    help = 'Corrige el orden de etapas en rutas clínicas existentes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se corregiría sin hacer cambios',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('CORRECCIÓN DE ORDEN DE ETAPAS'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN'))
            self.stdout.write('')
        
        # Obtener todas las rutas activas
        rutas = RutaClinica.objects.filter(
            estado__in=['INICIADA', 'EN_PROGRESO']
        )
        
        total = rutas.count()
        corregidas = 0
        
        orden_fijo = [key for key, _ in RutaClinica.ETAPAS_CHOICES]
        
        for i, ruta in enumerate(rutas, 1):
            self.stdout.write(f"\n[{i}/{total}] Ruta {str(ruta.id)[:8]}...")
            
            if not ruta.etapa_actual:
                self.stdout.write("  ⏭️  Sin etapa actual, saltando...")
                continue
            
            # Encontrar índice de la etapa actual en el orden fijo
            try:
                indice_actual = orden_fijo.index(ruta.etapa_actual)
            except ValueError:
                self.stdout.write(f"  ❌ Etapa no válida: {ruta.etapa_actual}")
                continue
            
            # Verificar si hay etapas anteriores no completadas
            etapas_previas_faltantes = []
            for j in range(indice_actual):
                etapa_previa = orden_fijo[j]
                if etapa_previa not in ruta.etapas_completadas:
                    etapas_previas_faltantes.append(etapa_previa)
            
            if not etapas_previas_faltantes:
                self.stdout.write("  ✓ Ruta correcta")
                continue
            
            # Mostrar corrección
            self.stdout.write(
                self.style.WARNING(
                    f"  🔧 Falta marcar como completadas: {len(etapas_previas_faltantes)} etapas"
                )
            )
            
            if not dry_run:
                ahora = timezone.now()
                for etapa_previa in etapas_previas_faltantes:
                    # Agregar a completadas
                    if etapa_previa not in ruta.etapas_completadas:
                        ruta.etapas_completadas.append(etapa_previa)
                    
                    # Registrar timestamp
                    ruta.timestamps_etapas[etapa_previa] = {
                        'fecha_inicio': ahora.isoformat(),
                        'fecha_fin': ahora.isoformat(),
                        'duracion_real': 0,
                        'duracion_estimada': ruta.DURACIONES_ESTIMADAS.get(etapa_previa, 30),
                        'observaciones': 'Auto-completada por corrección de orden',
                        'usuario_inicio': 'Sistema',
                        'auto_completada': True,
                    }
                    
                    label = dict(RutaClinica.ETAPAS_CHOICES).get(etapa_previa)
                    self.stdout.write(f"     ✓ {label}")
                
                ruta.calcular_progreso()
                ruta.save()
                corregidas += 1
            else:
                for etapa_previa in etapas_previas_faltantes:
                    label = dict(RutaClinica.ETAPAS_CHOICES).get(etapa_previa)
                    self.stdout.write(f"     🔍 Se completaría: {label}")
                corregidas += 1
        
        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('RESUMEN'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ Corrección completada'))
        
        self.stdout.write('')
        self.stdout.write(f"📊 Total procesadas: {total}")
        self.stdout.write(f"🔧 Rutas corregidas: {corregidas}")
        self.stdout.write(f"✓ Rutas correctas: {total - corregidas}")
        self.stdout.write('')