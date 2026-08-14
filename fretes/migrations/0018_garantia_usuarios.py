from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("fretes", "0017_produto_rtg"),
    ]

    operations = [
        migrations.AddField(
            model_name="garantia",
            name="criado_por",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="garantias_criadas",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Criado por",
            ),
        ),
        migrations.AddField(
            model_name="garantia",
            name="alterado_por",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="garantias_alteradas",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Alterado por",
            ),
        ),
    ]
