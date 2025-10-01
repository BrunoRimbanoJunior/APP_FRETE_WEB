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
    # Produtos
    path("produtos/", views.produto_list, name="produto_list"),
    path("produtos/novo/", views.produto_create, name="produto_create"),
    path("produtos/<int:pk>/editar/", views.produto_update, name="produto_update"),
    path("produtos/autocomplete/", views.produtos_autocomplete, name="produtos_autocomplete"),
    path("produtos/descricao/", views.produto_descricao_fragment, name="produto_descricao"),
    path("produtos/options/", views.produtos_options, name="produtos_options"),
    # Clientes
    path("clientes/", views.cliente_list, name="cliente_list"),
    path("clientes/novo/", views.cliente_create, name="cliente_create"),
    path("clientes/<int:pk>/editar/", views.cliente_update, name="cliente_update"),
    path("clientes/options/", views.clientes_options, name="clientes_options"),
    # Garantias
    path("garantias/", views.garantia_list, name="garantia_list"),
    path("garantias/novo/", views.garantia_create_multi, name="garantia_create"),
    path("garantias/<int:pk>/editar/", views.garantia_update, name="garantia_update"),
    # Ferramentas administrativas
    path("admin/tools/importar-produtos/", views.admin_import_produtos, name="admin_import_produtos"),
    path("admin/tools/importar-clientes/", views.admin_import_clientes, name="admin_import_clientes"),
    path("admin/tools/template-clientes/", views.admin_template_clientes, name="admin_template_clientes"),
    path("admin/tools/logs/", views.audit_log_view, name="audit_logs"),
]
