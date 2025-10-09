from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fretes", "0009_alter_produto_options_alter_cliente_endereco_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="freighttable",
            name="valor_despacho",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name="Valor de despacho"),
        ),
        migrations.AddField(
            model_name="freighttable",
            name="gris_perc",
            field=models.DecimalField(decimal_places=3, default=0, max_digits=6, verbose_name="GRIS %"),
        ),
    ]

