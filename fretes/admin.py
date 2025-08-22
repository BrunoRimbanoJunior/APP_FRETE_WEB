from django.contrib import admin
from .models import Carrier, FreightTable, Pedido, PedidoVolume, FreteCalculado

class FreightTableInline(admin.StackedInline):
    model = FreightTable
    extra = 0
    max_num = 1

@admin.register(Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)
    inlines = [FreightTableInline]

class PedidoVolumeInline(admin.TabularInline):
    model = PedidoVolume
    extra = 1

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("numero_pedido", "carrier", "m3")
    search_fields = ("numero_pedido",)
    list_filter = ("carrier",)
    inlines = [PedidoVolumeInline]

@admin.register(FreteCalculado)
class FreteCalculadoAdmin(admin.ModelAdmin):
    list_display = ("data_calculo", "numero_pedido", "carrier", "frete_total")
    list_filter = ("data_calculo", "carrier")
    search_fields = ("numero_pedido", "numero_nota")
