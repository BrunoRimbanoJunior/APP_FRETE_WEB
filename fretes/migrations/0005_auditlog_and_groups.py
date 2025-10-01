from django.db import migrations, models
from django.conf import settings


def seed_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    def perm(codename):
        try:
            return Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            return None

    def ctype(model):
        return ContentType.objects.get(app_label='fretes', model=model)

    # Model permissions
    models_ct = {
        'pedido': ctype('pedido'),
        'pedidovolume': ctype('pedidovolume'),
        'produto': ctype('produto'),
        'cliente': ctype('cliente'),
        'garantia': ctype('garantia'),
        'fretecalculado': ctype('fretecalculado'),
    }

    def mp(model, kind):
        return perm(f"{kind}_{model}")

    # Custom permissions (declared on Produto.Meta.permissions)
    p_import_produtos = perm('can_import_products')
    p_import_clientes = perm('can_import_clients')
    p_view_reports = perm('can_view_reports')
    p_use_calcular = perm('can_use_calcular')

    # Expedicao
    expedicao, _ = Group.objects.get_or_create(name='expedicao')
    to_add = filter(None, [
        mp('pedido', 'view'),
        mp('produto', 'view'),
        mp('cliente', 'view'),
        p_view_reports, p_use_calcular,
    ])
    expedicao.permissions.add(*list(to_add))

    # Garantia
    garantia, _ = Group.objects.get_or_create(name='garantia')
    to_add = filter(None, [
        mp('garantia', 'view'), mp('garantia', 'add'), mp('garantia', 'change'), mp('garantia', 'delete'),
        mp('pedido', 'view'),
        mp('produto', 'view'), mp('produto', 'change'),
        mp('cliente', 'view'), mp('cliente', 'change'),
    ])
    garantia.permissions.add(*list(to_add))

    # Conferencia
    conferencia, _ = Group.objects.get_or_create(name='conferencia')
    to_add = filter(None, [
        mp('pedido', 'view'), mp('pedido', 'add'), mp('pedido', 'change'), mp('pedido', 'delete'),
        mp('pedidovolume', 'view'), mp('pedidovolume', 'add'), mp('pedidovolume', 'change'), mp('pedidovolume', 'delete'),
        mp('produto', 'view'), mp('produto', 'change'),
        mp('cliente', 'view'),
        p_view_reports,
    ])
    conferencia.permissions.add(*list(to_add))

    # Vendas (leitura em tudo)
    vendas, _ = Group.objects.get_or_create(name='vendas')
    to_add = filter(None, [
        mp('pedido', 'view'), mp('pedidovolume', 'view'), mp('produto', 'view'), mp('cliente', 'view'), mp('garantia', 'view'), mp('fretecalculado', 'view')
    ])
    vendas.permissions.add(*list(to_add))


class Migration(migrations.Migration):

    dependencies = [
        ('fretes', '0004_garantia_mao_de_obra'),
        ('auth', '__latest__'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=150)),
                ('action', models.CharField(choices=[('create', 'create'), ('update', 'update'), ('delete', 'delete'), ('import', 'import'), ('export', 'export'), ('login', 'login'), ('logout', 'logout'), ('view', 'view')], max_length=16)),
                ('module', models.CharField(blank=True, max_length=50)),
                ('object_type', models.CharField(blank=True, max_length=50)),
                ('object_id', models.CharField(blank=True, max_length=64)),
                ('object_repr', models.CharField(blank=True, max_length=255)),
                ('path', models.CharField(blank=True, max_length=255)),
                ('method', models.CharField(blank=True, max_length=8)),
                ('status_code', models.PositiveIntegerField(default=0)),
                ('ip', models.CharField(blank=True, max_length=64)),
                ('user_agent', models.CharField(blank=True, max_length=255)),
                ('changes', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at', '-id'], 'verbose_name': 'Log de Auditoria', 'verbose_name_plural': 'Logs de Auditoria'},
        ),
        migrations.AlterModelOptions(
            name='produto',
            options={'ordering': ['codigo'], 'permissions': (('can_import_products', 'Pode importar produtos'), ('can_import_clients', 'Pode importar clientes'), ('can_view_reports', 'Pode acessar relatórios'), ('can_use_calcular', 'Pode usar a ferramenta Calcular')), 'verbose_name': 'Produto', 'verbose_name_plural': 'Produtos'},
        ),
        migrations.RunPython(seed_groups, migrations.RunPython.noop),
    ]

