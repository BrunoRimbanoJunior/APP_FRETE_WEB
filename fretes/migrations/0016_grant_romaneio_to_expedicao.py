from django.db import migrations


def grant_romaneio_permission(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    content_type, _ = ContentType.objects.get_or_create(
        app_label="fretes",
        model="produto",
    )
    permission, _ = Permission.objects.get_or_create(
        content_type=content_type,
        codename="can_view_reports",
        defaults={"name": "Pode acessar relatorios"},
    )
    expedicao, _ = Group.objects.get_or_create(name="expedicao")
    expedicao.permissions.add(permission)


def revoke_romaneio_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    expedicao = Group.objects.filter(name="expedicao").first()
    permission = Permission.objects.filter(
        content_type__app_label="fretes",
        codename="can_view_reports",
    ).first()
    if expedicao and permission:
        expedicao.permissions.remove(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("fretes", "0015_garantia_tipo"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(grant_romaneio_permission, revoke_romaneio_permission),
    ]
