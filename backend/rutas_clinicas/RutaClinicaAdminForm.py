from django import forms
from .models import RutaClinica


class RutaClinicaAdminForm(forms.ModelForm):
    # Form personalizado para el admin de RutaClinica
    
    etapas_seleccionadas = forms.MultipleChoiceField(
        choices=RutaClinica.ETAPAS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Seleccione las etapas del proceso clínico en orden"
    )
    
    class Meta:
        model = RutaClinica
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si ya tiene etapas seleccionadas, mostrarlas
        if self.instance.pk and self.instance.etapas_seleccionadas:
            self.initial['etapas_seleccionadas'] = self.instance.etapas_seleccionadas
    
    def clean_etapas_seleccionadas(self):
        # Convierte las etapas seleccionadas a lista
        etapas = self.cleaned_data.get('etapas_seleccionadas', [])
        return list(etapas) if etapas else []