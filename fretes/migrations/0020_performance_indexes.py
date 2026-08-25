from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fretes", "0019_warranty_management_permission"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="fretecalculado",
            index=models.Index(fields=["data_calculo"], name="frete_data_calculo_idx"),
        ),
        migrations.AddIndex(
            model_name="fretecalculado",
            index=models.Index(fields=["tipo_frete"], name="frete_tipo_idx"),
        ),
        migrations.AddIndex(
            model_name="cliente",
            index=models.Index(fields=["nome"], name="cliente_nome_idx"),
        ),
        migrations.AddIndex(
            model_name="garantia",
            index=models.Index(fields=["data_recebimento"], name="garantia_data_idx"),
        ),
        migrations.AddIndex(
            model_name="garantia",
            index=models.Index(fields=["tipo"], name="garantia_tipo_idx"),
        ),
        migrations.AddIndex(
            model_name="garantia",
            index=models.Index(fields=["marca"], name="garantia_marca_idx"),
        ),
        migrations.AddIndex(
            model_name="garantia",
            index=models.Index(fields=["codigo_peca"], name="garantia_codigo_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["created_at"], name="audit_created_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["action"], name="audit_action_idx"),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["module"], name="audit_module_idx"),
        ),
    ]
