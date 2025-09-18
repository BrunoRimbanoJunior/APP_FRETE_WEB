from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.utils import timezone
from django.contrib import messages
from .models import Pedido, PedidoVolume, Carrier, FreteCalculado
from .forms import CalcularFreteForm, PedidoForm, PedidoVolumeForm
from .filters import FreteCalculadoFilter
from .services import calcular_frete
from .exports import exportar_fretes_excel, exportar_fretes_pdf


VolumeFormSet = inlineformset_factory(
    Pedido, PedidoVolume,
    form=PedidoVolumeForm,
    extra=1,                 # sempre mostra 1 linha vazia
    can_delete=True)

# fretes/views.py



VolumeFormSet = inlineformset_factory(
    Pedido,
    PedidoVolume,
    form=PedidoVolumeForm,
    extra=1,
    can_delete=True
)

def _calcular_m3_total_pedido(pedido):
    """
    Função auxiliar para somar a cubagem de todos os volumes de um pedido,
    considerando a quantidade.
    """
    total_m3 = Decimal("0")
    for volume in pedido.volumes.all():
        largura = volume.largura_cm / Decimal("100")
        altura = volume.altura_cm / Decimal("100")
        comprimento = volume.comprimento_cm / Decimal("100")
        
        # 💡 Multiplica o volume pela quantidade antes de somar
        m3_volume = (largura * altura * comprimento) * Decimal(volume.quantidade)
        total_m3 += m3_volume
    return total_m3.quantize(Decimal("0.001"))


def pedido_create(request):
    if request.method == "POST":
        form = PedidoForm(request.POST)
        formset = VolumeFormSet(request.POST, prefix="vol")
        if form.is_valid() and formset.is_valid():
            numero_pedido = form.cleaned_data.get("numero_pedido")
            pedido, created = Pedido.objects.get_or_create(
                numero_pedido=numero_pedido,
                defaults={
                    "picking": form.cleaned_data.get("picking"),
                    "carrier": form.cleaned_data.get("carrier"),
                }
            )
            if not created:
                pedido.picking = form.cleaned_data.get("picking")
                pedido.carrier = form.cleaned_data.get("carrier")
                pedido.save(update_fields=["picking", "carrier"])
            
            # 💡 Removemos a linha 'pedido.volumes.all().delete()'
            #    que estava causando o problema.
            
            # Associa a instância do pedido ao formset e salva
            formset.instance = pedido
            formset.save()

            messages.success(request, "Pedido salvo com sucesso.")
            return redirect("fretes:pedido_list")
        else:
            # Lógica de erro para formulário
            for err in formset.non_form_errors():
                messages.error(request, err)
            for f in formset.forms:
                for field, errs in f.errors.items():
                    messages.error(request, f"Volume: {field} -> {', '.join(errs)}")
    else:
        form = PedidoForm()
        formset = VolumeFormSet(prefix="vol")
    
    return render(request, "fretes/pedidos_form.html",
                  {"form": form, "formset": formset, "is_new": True})

# fretes/views.py

def calcular_view(request):
    context = {}
    if request.method == "POST":
        form = CalcularFreteForm(request.POST)
        if form.is_valid():
            # 💡 Obtemos o número do pedido dos dados limpos do formulário
            numero_pedido = form.cleaned_data["numero_pedido"]
            carrier = form.cleaned_data["carrier"]
            kg_nota = form.cleaned_data["kg_nota"]
            valor_nota = form.cleaned_data.get("valor_nota")
            numero_nota = form.cleaned_data.get("numero_nota", "")

            # 💡 Buscamos o pedido novamente, desta vez com prefetch_related
            # para garantir que os volumes estão carregados.
            try:
                pedido = Pedido.objects.prefetch_related('volumes').get(numero_pedido=numero_pedido)
            except Pedido.DoesNotExist:
                # Caso o pedido não seja encontrado (mesmo após a validação)
                form.add_error("numero_pedido", "Pedido não encontrado.")
                context["form"] = form
                return render(request, "fretes/calcular.html", context)

            # Nova lógica: recalcula o m3 total do pedido a partir dos volumes
            m3_total_pedido = _calcular_m3_total_pedido(pedido)

            # Atualiza o campo m3 do pedido com o valor total calculado
            pedido.m3 = m3_total_pedido
            pedido.save(update_fields=["m3"])
            
            # Passa o m3 atualizado para a função de cálculo de frete
            r = calcular_frete(pedido, carrier, kg_nota, valor_nota)

            FreteCalculado.objects.update_or_create(
                numero_pedido=pedido.numero_pedido,
                carrier=carrier,
                defaults={
                    "data_calculo": timezone.now().date(),
                    "numero_nota": numero_nota,
                    "valor_nota": valor_nota or 0,
                    "kg_nota": kg_nota,
                    "m3": r["m3"],
                    "peso_cubico": r["peso_cubico"],
                    "peso_usado": r["peso_usado"],
                    "frete_total": r["frete_total"],
                },
            )
            context.update({"resultado": r, "pedido": pedido, "carrier": carrier, "form": form})
            if request.headers.get("HX-Request") == "true":
                return render(request, "fretes/_resultado.html", context)
        else:
            if request.headers.get("HX-Request") == "true":
                return render(request, "fretes/_resultado.html", {"form": form})
    else:
        form = CalcularFreteForm()
    context["form"] = form
    return render(request, "fretes/calcular.html", context)


def index_view(request):
    return render(request, "fretes/index.html")

def pedido_list(request):
    pedidos = Pedido.objects.select_related("carrier").prefetch_related("volumes").order_by("-id")
    return render(request, "fretes/pedidos_list.html", {"pedidos": pedidos})


    
def pedido_update(request, pk: int):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST":
        form = PedidoForm(request.POST, instance=pedido)
        formset = VolumeFormSet(request.POST, instance=pedido, prefix="vol")  # << prefix
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Pedido atualizado.")
            return redirect("fretes:pedido_list")
        else:
            for err in formset.non_form_errors():
                messages.error(request, err)
            for f in formset.forms:
                for field, errs in f.errors.items():
                    messages.error(request, f"Volume: {field} -> {', '.join(errs)}")
    else:
        form = PedidoForm(instance=pedido)
        formset = VolumeFormSet(instance=pedido, prefix="vol")  # << prefix
    return render(request, "fretes/pedidos_form.html",
                  {"form": form, "formset": formset, "pedido": pedido, "is_new": False})


def relatorios_view(request):
    f = FreteCalculadoFilter(request.GET, queryset=FreteCalculado.objects.select_related("carrier").all())
    export = request.GET.get("export")
    if export == "xlsx":
        return exportar_fretes_excel(f.qs)
    if export == "pdf":
        return exportar_fretes_pdf(f.qs)
    return render(request, "fretes/relatorios.html", {"filter": f})

def relatorios_pdf_view(request):
    f = FreteCalculadoFilter(request.GET, queryset=FreteCalculado.objects.select_related("carrier").all())
    return exportar_fretes_pdf(f.qs)

def pedidos_autocomplete(request):
    q = request.GET.get("numero_pedido", "").strip()
    qs = Pedido.objects.all().order_by("-id")
    if q:
        qs = qs.filter(numero_pedido__icontains=q)
    qs = qs[:20]
    return render(request, "fretes/_pedidos_datalist.html", {"qs": qs})
