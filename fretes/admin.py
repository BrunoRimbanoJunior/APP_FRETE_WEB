from django.contrib import admin
from .models import Carrier, FreightTable, Pedido, PedidoVolume, FreteCalculado, Produto, Cliente, Garantia, AuditLog


admin.site.site_header = "Configurações App Frete"
admin.site.site_title = "Configurações App Frete"
admin.site.index_title = "Bem-vindo"



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


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao", "peso_bruto_kg", "peso_liquido_kg")
    search_fields = ("codigo", "descricao")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cnpj", "cidade", "estado", "email", "telefone")
    search_fields = ("nome", "cnpj")
    list_filter = ("estado",)


@admin.register(Garantia)
class GarantiaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "codigo_peca", "nota_recebida", "nota_retorno", "data_recebimento", "data_retorno", "valor")
    search_fields = ("codigo_peca", "nota_recebida", "nota_retorno", "cliente__nome", "cliente__cnpj")
    list_filter = ("data_recebimento", "data_retorno")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "username", "action", "module", "object_type", "object_id", "status_code")
    list_filter = ("action", "module", "status_code", "created_at")
    search_fields = ("username", "object_type", "object_id", "object_repr", "path")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
