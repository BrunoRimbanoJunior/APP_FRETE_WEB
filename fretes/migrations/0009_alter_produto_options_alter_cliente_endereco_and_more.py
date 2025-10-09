from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fretes", "0008_garantia_marca"),
    ]

    # Esta migration existia no histórico; como o schema atual já está compatível,
    # mantemos vazia apenas para preservar a cadeia.
    operations = []

