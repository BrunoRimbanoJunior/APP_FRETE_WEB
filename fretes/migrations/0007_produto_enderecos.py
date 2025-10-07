from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fretes', '0006_garantia_quantidade'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='enderecos',
            field=models.CharField(blank=True, max_length=1024, verbose_name='Enderecos'),
        ),
    ]
