from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fretes", "0012_multi_pedido_tipo_frete"),
    ]

    operations = [
        migrations.AddField(
            model_name="freighttable",
            name="tipo_calculo",
            field=models.PositiveSmallIntegerField(default=1, verbose_name="Tipo de calculo"),
        ),
    ]

