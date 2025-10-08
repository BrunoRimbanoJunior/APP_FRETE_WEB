from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fretes', '0007_produto_enderecos'),
    ]

    operations = [
        migrations.AddField(
            model_name='garantia',
            name='marca',
            field=models.CharField(default='Nao Informado', max_length=120, verbose_name='Marca'),
        ),
    ]
