from django.db import migrations


PERMISSION_CODENAME = "can_view_warranty_management"


def grant_warranty_management_permission(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="fretes",
        model="produto",
    )
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename=PERMISSION_CODENAME,
        defaults={"name": "Pode acessar o gerencial de garantias"},
    )
    garantia, _ = Group.objects.get_or_create(name="garantia")
    garantia.permissions.add(permission)


def revoke_warranty_management_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    garantia = Group.objects.filter(name="garantia").first()
    permission = Permission.objects.filter(
        content_type__app_label="fretes",
        codename=PERMISSION_CODENAME,
    ).first()
    if garantia and permission:
        garantia.permissions.remove(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("fretes", "0018_garantia_usuarios"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="produto",
            options={
                "ordering": ["codigo"],
                "permissions": (
                    ("can_import_products", "Pode importar produtos"),
                    ("can_import_clients", "Pode importar clientes"),
                    ("can_view_reports", "Pode acessar relatorios"),
                    ("can_view_warranty_management", "Pode acessar o gerencial de garantias"),
                    ("can_use_calcular", "Pode usar a ferramenta Calcular"),
                ),
                "verbose_name": "Produto",
                "verbose_name_plural": "Produtos",
            },
        ),
        migrations.RunPython(
            grant_warranty_management_permission,
            revoke_warranty_management_permission,
        ),
    ]
