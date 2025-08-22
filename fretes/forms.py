from django import forms
from django.forms import ModelForm
from .models import Carrier, Pedido, PedidoVolume

class CalcularFreteForm(forms.Form):
    numero_pedido = forms.CharField(label="Pedido")
    carrier = forms.ModelChoiceField(queryset=Carrier.objects.all(), required=False)
    numero_nota = forms.CharField(required=False, label="Numero nota")
    valor_nota = forms.DecimalField(required=False, min_value=0, decimal_places=2, max_digits=12, label="Valor nota")
    kg_nota = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, label="Kg nota")

    def clean(self):
        data = super().clean()
        numero_pedido = data.get("numero_pedido")
        try:
            pedido = Pedido.objects.get(numero_pedido=numero_pedido)
        except Pedido.DoesNotExist:
            raise forms.ValidationError("Pedido não encontrado. Cadastre o pedido ou verifique o número.")
        carrier = data.get("carrier") or (pedido.carrier if pedido else None)
        if not carrier:
            raise forms.ValidationError("Selecione uma transportadora ou vincule uma ao pedido.")
        data["pedido"] = pedido
        data["carrier"] = carrier
        return data

class PedidoForm(ModelForm):
    class Meta:
        model = Pedido
        fields = ["numero_pedido", "picking", "carrier"]

class PedidoVolumeForm(ModelForm):
    class Meta:
        model = PedidoVolume
        fields = ["largura_cm", "altura_cm", "comprimento_cm", "quantidade"]
