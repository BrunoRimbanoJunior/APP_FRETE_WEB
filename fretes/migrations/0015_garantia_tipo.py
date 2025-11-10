from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fretes", "0014_normalize_garantia_marca_upper"),
    ]

    operations = [
        migrations.AddField(
            model_name="garantia",
            name="tipo",
            field=models.CharField(
                verbose_name="Tipo",
                max_length=16,
                choices=[("garantia", "Garantia"), ("devolucao", "Devolucao")],
                default="garantia",
            ),
        ),
    ]

