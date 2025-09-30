from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fretes", "0003_produto_cliente_garantia"),
    ]

    operations = [
        migrations.AddField(
            model_name="garantia",
            name="mao_de_obra",
            field=models.BooleanField(default=False, verbose_name="Com mão de obra"),
        ),
        migrations.AddField(
            model_name="garantia",
            name="valor_mao_de_obra",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name="Valor mão de obra"),
        ),
    ]

