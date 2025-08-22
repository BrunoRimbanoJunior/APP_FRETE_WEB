from django.urls import path
from . import views

app_name = "fretes"

urlpatterns = [
    path("", views.index_view, name="index"),
    # Pedidos
    path("pedidos/", views.pedido_list, name="pedido_list"),
    path("pedidos/novo/", views.pedido_create, name="pedido_create"),
    path("pedidos/<int:pk>/editar/", views.pedido_update, name="pedido_update"),
    # 🔎 Auto-complete de pedidos
    path("pedidos/autocomplete/", views.pedidos_autocomplete, name="pedidos_autocomplete"),
    # Calcular
    path("calcular/", views.calcular_view, name="calcular"),
    # Relatórios
    path("relatorios/", views.relatorios_view, name="relatorios"),
    path("relatorios/pdf/", views.relatorios_pdf_view, name="relatorios_pdf"),
]
