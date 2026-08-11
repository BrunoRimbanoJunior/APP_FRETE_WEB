from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("fretes", "0016_grant_romaneio_to_expedicao")]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="rtg",
            field=models.CharField(blank=True, db_index=True, max_length=60, verbose_name="RTG"),
        ),
    ]
