from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory   # ✅ para o formset
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import Pedido, PedidoVolume, Carrier, FreteCalculado
from .forms import CalcularFreteForm, PedidoForm, PedidoVolumeForm
from .filters import FreteCalculadoFilter
from .services import calcular_frete
from .exports import exportar_fretes_excel, exportar_fretes_pdf
from django.db.models import Q
from django.contrib import messages

def calcular_view(request):
    context = {}
    if request.method == "POST":
        form = CalcularFreteForm(request.POST)
        if form.is_valid():
            pedido = form.cleaned_data["pedido"]
            carrier = form.cleaned_data["carrier"]
            kg_nota = form.cleaned_data["kg_nota"]
            valor_nota = form.cleaned_data.get("valor_nota")
            numero_nota = form.cleaned_data.get("numero_nota", "")

            r = calcular_frete(pedido, carrier, kg_nota, valor_nota)

            obj, created = FreteCalculado.objects.update_or_create(
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

            context.update({
                "resultado": r,
                "pedido": pedido,
                "carrier": carrier,
            })

            # ✅ mensagem amigável
            if created:
                messages.success(request, f"Frete criado para o pedido {pedido.numero_pedido} ({carrier}).")
            else:
                messages.info(request, f"Frete atualizado para o pedido {pedido.numero_pedido} ({carrier}).")

            if request.headers.get("HX-Request") == "true":
                return render(request, "fretes/_resultado.html", context)

        else:
            if request.headers.get("HX-Request") == "true":
                return render(request, "fretes/_resultado.html", {"form": form})
    else:
        form = CalcularFreteForm()

    context["form"] = form
    return render(request, "fretes/calcular.html", context)


def relatorios_view(request):
    f = FreteCalculadoFilter(request.GET, queryset=FreteCalculado.objects.select_related("carrier").all())
    if "export" in request.GET:
        return exportar_fretes_excel(f.qs)
    return render(request, "fretes/relatorios.html", {"filter": f})


def index_view(request):
    return render(request, "fretes/index.html")

def pedido_list(request):
    qs = Pedido.objects.select_related("carrier").order_by("-id")
    return render(request, "fretes/pedidos_list.html", {"pedidos": qs})

def pedido_create(request):
    VolumeFormSet = inlineformset_factory(
        Pedido, PedidoVolume, form=PedidoVolumeForm,
        extra=1, can_delete=True
    )
    if request.method == "POST":
        form = PedidoForm(request.POST)
        formset = VolumeFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            pedido = form.save()
            formset.instance = pedido
            formset.save()
            return redirect("fretes:pedido_update", pk=pedido.pk)
    else:
        initial = {}
        num = request.GET.get("numero_pedido")
        if num:
            initial["numero_pedido"] = num
        form = PedidoForm(initial=initial)
        formset = VolumeFormSet()

    return render(
        request, "fretes/pedidos_form.html",
        {"form": form, "formset": formset, "is_new": True}
    )


def pedido_update(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    VolumeFormSet = inlineformset_factory(
        Pedido, PedidoVolume, form=PedidoVolumeForm,
        extra=1, can_delete=True
    )
    if request.method == "POST":
        form = PedidoForm(request.POST, instance=pedido)
        formset = VolumeFormSet(request.POST, instance=pedido)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("fretes:pedido_update", pk=pedido.pk)
    else:
        form = PedidoForm(instance=pedido)
        formset = VolumeFormSet(instance=pedido)
    return render(request, "fretes/pedidos_form.html", {"form": form, "formset": formset, "pedido": pedido, "is_new": False})




def relatorios_view(request):
    f = FreteCalculadoFilter(request.GET, queryset=FreteCalculado.objects.select_related("carrier").all())
    if "export" in request.GET:
        if request.GET.get("export") == "xlsx":
            return exportar_fretes_excel(f.qs)
        if request.GET.get("export") == "pdf":
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
    qs = qs[:20]  # limita sugestões
    return render(request, "fretes/_pedidos_datalist.html", {"qs": qs})
