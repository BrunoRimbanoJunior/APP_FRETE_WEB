
from django import forms
from django.forms import ModelForm
from .models import Carrier, Pedido, PedidoVolume, Produto, Cliente, Garantia, FreteCalculado

class CalcularFreteForm(forms.Form):
    # Suporta multiplos pedidos separados por virgula
    numero_pedido = forms.CharField(label="Pedidos")
    carrier = forms.ModelChoiceField(queryset=Carrier.objects.all(), required=False)
    numero_nota = forms.CharField(required=False, label="Numero nota")
    valor_nota = forms.DecimalField(required=False, min_value=0, decimal_places=2, max_digits=12, label="Valor nota")
    kg_nota = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, label="Kg nota")
    # Novo: tipo de frete e autorizacao condicional
    tipo_frete = forms.ChoiceField(
        choices=FreteCalculado.TIPOS_FRETE,
        required=False,
        label="Tipo de frete",
    )
    autorizado_por = forms.CharField(required=False, label="Autorizado por")

    def clean(self):
        data = super().clean()
        pedidos_raw = (data.get("numero_pedido") or "").strip()
        if not pedidos_raw:
            raise forms.ValidationError("Informe ao menos um numero de pedido (separe por virgula).")

        numeros = [p.strip() for p in pedidos_raw.replace(";", ",").split(",") if p.strip()]
        if not numeros:
            raise forms.ValidationError("Informe ao menos um numero de pedido valido.")

        pedidos = list(Pedido.objects.filter(numero_pedido__in=numeros).prefetch_related("volumes"))
        encontrados = {p.numero_pedido for p in pedidos}
        faltando = [n for n in numeros if n not in encontrados]
        if faltando:
            raise forms.ValidationError(f"Pedidos nao encontrados: {', '.join(faltando)}. Cadastre-os antes de calcular.")

        # Determina carrier
        carrier = data.get("carrier")
        if not carrier:
            carriers = {p.carrier_id for p in pedidos if p.carrier_id}
            if len(carriers) == 1:
                # Usa a do unico carrier presente
                carrier = pedidos[0].carrier
            else:
                raise forms.ValidationError("Selecione uma transportadora.")

        # Validacao para tipo de frete quando valor_nota < 4000
        valor_nota = data.get("valor_nota")
        tipo = (data.get("tipo_frete") or "").strip()
        if valor_nota is not None:
            try:
                below = float(valor_nota) < 4000
            except Exception:
                below = False
            if below:
                if not tipo:
                    self.add_error("tipo_frete", "Selecione o tipo de frete.")
                if tipo == FreteCalculado.TIPO_PAGO and not (data.get("autorizado_por") or "").strip():
                    self.add_error("autorizado_por", "Obrigatorio quando frete pago com valor da nota < 4.000,00.")

        data["pedidos"] = pedidos
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


class ProdutoForm(ModelForm):
    class Meta:
        model = Produto
        fields = [
            "codigo", "rtg", "descricao", "enderecos", "peso_bruto_kg", "peso_liquido_kg",
            "largura_cm", "altura_cm", "comprimento_cm"
        ]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control"}),
            "rtg": forms.TextInput(attrs={"class": "form-control"}),
            "descricao": forms.TextInput(attrs={"class": "form-control"}),
            "enderecos": forms.TextInput(attrs={"class": "form-control", "placeholder": "Endereco 1, Endereco 2"}),
            "peso_bruto_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "peso_liquido_kg": forms.NumberInput(attrs={"class": "form-control", "step": "0.001"}),
            "largura_cm": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "altura_cm": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "comprimento_cm": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class ClienteForm(ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome", "cnpj", "endereco", "cidade", "estado", "email", "telefone"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "cnpj": forms.TextInput(attrs={"class": "form-control"}),
            "endereco": forms.TextInput(attrs={"class": "form-control"}),
            "cidade": forms.TextInput(attrs={"class": "form-control"}),
            "estado": forms.TextInput(attrs={"class": "form-control", "maxlength": 2}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
        }


class GarantiaForm(ModelForm):
    class Meta:
        model = Garantia
        fields = [
            "cliente", "codigo_peca", "marca", "defeito", "numero_lote",
            "nota_recebida", "valor", "data_recebimento", "tipo",
            "nota_retorno", "data_retorno", "mao_de_obra", "valor_mao_de_obra"
        ]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "codigo_peca": forms.TextInput(attrs={"class": "form-control"}),
            "marca": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex.: Marca da peca"}),
            "defeito": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "numero_lote": forms.TextInput(attrs={"class": "form-control"}),
            "nota_recebida": forms.TextInput(attrs={"class": "form-control"}),
            "valor": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "data_recebimento": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "class": "form-control"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "nota_retorno": forms.TextInput(attrs={"class": "form-control"}),
            "data_retorno": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "mao_de_obra": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "id_mao_de_obra"}),
            "valor_mao_de_obra": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "id": "id_valor_mao"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_recebimento"].input_formats = ["%Y-%m-%d", "%d/%m/%Y"]
        if self.instance and getattr(self.instance, "data_recebimento", None):
            self.initial.setdefault("data_recebimento", self.instance.data_recebimento)

    def clean_codigo_peca(self):
        codigo = self.cleaned_data.get("codigo_peca", "").strip()
        if not codigo:
            return codigo
        exists = Produto.objects.filter(codigo=codigo).exists()
        if not exists:
            if getattr(self.instance, 'pk', None) and self.instance.codigo_peca == codigo:
                return codigo
            raise forms.ValidationError(
                "Codigo de peca nao encontrado entre os produtos cadastrados."
            )
        return codigo

    def clean_marca(self):
        marca = (self.cleaned_data.get("marca") or "").strip()
        if not marca:
            raise forms.ValidationError("Informe a marca da peca.")
        return marca.upper()

    def clean(self):
        data = super().clean()
        if data.get("mao_de_obra"):
            if not data.get("valor_mao_de_obra"):
                self.add_error("valor_mao_de_obra", "Informe o valor da mao de obra.")
        else:
            data["valor_mao_de_obra"] = data.get("valor_mao_de_obra") or 0
        return data


class GarantiaHeaderForm(forms.Form):
    nota_recebida = forms.CharField(
        label="Nota recebida",
        required=True,
        error_messages={"required": "Informe o numero da nota recebida."},
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cliente = forms.ModelChoiceField(
        label="Cliente",
        queryset=Cliente.objects.all(),
        required=True,
        error_messages={"required": "Selecione um cliente."},
        widget=forms.Select(attrs={"class": "form-select", "id": "id_cliente"}),
    )
    data_recebimento = forms.DateField(
        label="Data de recebimento",
        required=True,
        error_messages={"required": "Informe a data de recebimento."},
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    tipo = forms.ChoiceField(
        label="Tipo",
        choices=(
            ("garantia", "Garantia"),
            ("devolucao", "Devolucao"),
        ),
        initial="garantia",
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class GarantiaItemForm(forms.Form):
    codigo_peca = forms.ChoiceField(label="Codigo da peca", choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    marca = forms.CharField(label="Marca", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Marca da peca"}))
    numero_lote = forms.CharField(label="Numero do lote", required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    defeito = forms.CharField(label="Defeito", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    valor = forms.DecimalField(label="Valor", required=False, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))
    nota_retorno = forms.CharField(label="Nota de retorno", required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    data_retorno = forms.DateField(label="Data de retorno", required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    mao_de_obra = forms.BooleanField(label="Com mao de obra", required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))
    valor_mao_de_obra = forms.DecimalField(label="Valor mao de obra", required=False, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}))

    def clean_codigo_peca(self):
        codigo = self.cleaned_data.get("codigo_peca", "")
        if not Produto.objects.filter(codigo=codigo).exists():
            raise forms.ValidationError("Codigo de peca invalido.")
        return codigo

    def clean_marca(self):
        marca = (self.cleaned_data.get("marca") or "").strip()
        if not marca:
            raise forms.ValidationError("Informe a marca da peca.")
        return marca.upper()

    def clean(self):
        data = super().clean()
        if data.get("mao_de_obra"):
            if not data.get("valor_mao_de_obra"):
                self.add_error("valor_mao_de_obra", "Informe o valor da mao de obra.")
        else:
            data["valor_mao_de_obra"] = data.get("valor_mao_de_obra") or 0
        return data


