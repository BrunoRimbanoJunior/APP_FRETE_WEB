from django.db import migrations, models


def set_default_quantidade(apps, schema_editor):
    Garantia = apps.get_model('fretes', 'Garantia')
    Garantia.objects.filter(quantidade__isnull=True).update(quantidade=1)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('fretes', '0005_auditlog_and_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='garantia',
            name='quantidade',
            field=models.PositiveIntegerField(default=1, verbose_name='Quantidade'),
        ),
        migrations.RunPython(set_default_quantidade, noop),
    ]

