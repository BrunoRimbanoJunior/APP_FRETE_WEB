from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fretes", "0011_alter_produto_options_alter_cliente_endereco_and_more"),
    ]

    operations = [
        # Remove constraint antigo de unicidade por (numero_pedido, carrier)
        migrations.RemoveConstraint(
            model_name="fretecalculado",
            name="uniq_pedido_carrier",
        ),
        # Campo ManyToMany para vincular varios pedidos a um calculo
        migrations.AddField(
            model_name="fretecalculado",
            name="pedidos",
            field=models.ManyToManyField(blank=True, related_name="fretes", to="fretes.pedido"),
        ),
        # Campos para tipo de frete e autorizacao
        migrations.AddField(
            model_name="fretecalculado",
            name="tipo_frete",
            field=models.CharField(choices=[("pago", "Frete Pago"), ("a_pagar", "Frete a Pagar")], default="pago", max_length=16),
        ),
        migrations.AddField(
            model_name="fretecalculado",
            name="autorizado_por",
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
