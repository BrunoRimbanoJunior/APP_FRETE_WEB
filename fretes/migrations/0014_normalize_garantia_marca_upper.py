from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("fretes", "0013_freighttable_tipo_calculo"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                """
                -- Normaliza campo marca em maiusculas e remove espacos
                UPDATE fretes_garantia
                SET marca = CASE
                    WHEN COALESCE(BTRIM(marca), '') = '' THEN 'NAO INFORMADO'
                    ELSE UPPER(BTRIM(marca))
                END;
                """
            ),
            reverse_sql=(
                """
                -- No-op reverse (nao ha como recuperar o casing original)
                SELECT 1;
                """
            ),
        )
    ]

