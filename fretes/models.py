
from decimal import Decimal
from datetime import date, datetime
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models import JSONField

class Carrier(models.Model):
    nome = models.CharField("Nome", max_length=120, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Transportadora"
        verbose_name_plural = "Transportadoras"

    def __str__(self) -> str:
        return self.nome

class FreightTable(models.Model):
    carrier = models.OneToOneField(
        Carrier, on_delete=models.CASCADE, related_name="tabela"
    )
    tipo_calculo = models.PositiveSmallIntegerField(
        "Tipo de calculo", default=1
    )
    peso_ate_50 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_100 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_150 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_200 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_300 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frete_ton = models.DecimalField("Frete por Tonelada", max_digits=10, decimal_places=2, default=0)
    frete_minimo = models.DecimalField("Frete Minimo", max_digits=10, decimal_places=2, default=0)
    pedagio = models.DecimalField("Pedagio", max_digits=10, decimal_places=2, default=0)
    frete_valor_perc = models.DecimalField("Frete Valor %", max_digits=6, decimal_places=3, default=0)
    valor_despacho = models.DecimalField("Valor de despacho", max_digits=10, decimal_places=2, default=0)
    gris_perc = models.DecimalField("GRIS %", max_digits=6, decimal_places=3, default=0)
    fator_peso_cubico = models.DecimalField("Fator Peso Cubico", max_digits=10, decimal_places=2, default=230)

    class Meta:
        verbose_name = "Tabela de Frete"
        verbose_name_plural = "Tabelas de Frete"

    def __str__(self) -> str:
        return f"Tabela - {self.carrier.nome}"

class Pedido(models.Model):
    numero_pedido = models.CharField(max_length=60, unique=True)
    picking = models.CharField(max_length=120, blank=True)
    carrier = models.ForeignKey(Carrier, null=True, blank=True, on_delete=models.SET_NULL)
    m3 = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self) -> str:
        return self.numero_pedido

class PedidoVolume(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="volumes")
    largura_cm = models.DecimalField(max_digits=8, decimal_places=2)
    altura_cm = models.DecimalField(max_digits=8, decimal_places=2)
    comprimento_cm = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)
    # importante: default=0 para nao quebrar no insert
    m3 = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        verbose_name = "Volume do Pedido"
        verbose_name_plural = "Volumes do Pedido"

    def __str__(self) -> str:
        return f"{self.pedido} - {self.largura_cm}x{self.altura_cm}x{self.comprimento_cm} x {self.quantidade}"

class FreteCalculado(models.Model):
    data_calculo = models.DateField(auto_now_add=True)
    # Historico legado: numero_pedido permanece para compatibilidade e auditoria
    numero_pedido = models.CharField(max_length=60)
    # Novo: permite vincular varios pedidos a um mesmo calculo (nota)
    pedidos = models.ManyToManyField('Pedido', related_name='fretes', blank=True)
    numero_nota = models.CharField(max_length=60, blank=True)
    valor_nota = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    kg_nota = models.DecimalField(max_digits=12, decimal_places=2)
    m3 = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    peso_cubico = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    peso_usado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frete_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)
    # Novo: tipo de frete e autorizacao
    TIPO_PAGO = 'pago'
    TIPO_A_PAGAR = 'a_pagar'
    TIPOS_FRETE = (
        (TIPO_PAGO, 'Frete Pago'),
        (TIPO_A_PAGAR, 'Frete a Pagar'),
    )
    tipo_frete = models.CharField(max_length=16, choices=TIPOS_FRETE, default=TIPO_PAGO)
    autorizado_por = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Frete Calculado"
        verbose_name_plural = "Fretes Calculados"
        indexes = [
            models.Index(fields=["data_calculo"], name="frete_data_calculo_idx"),
            models.Index(fields=["tipo_frete"], name="frete_tipo_idx"),
        ]
        # Removido constraint antigo de (numero_pedido, carrier) para permitir multi-pedido por nota

    def __str__(self) -> str:
        return f"{self.numero_pedido} - {self.carrier} - {self.frete_total}"


# Novos cadastros
class Produto(models.Model):
    codigo = models.CharField("Codigo", max_length=60, unique=True)
    rtg = models.CharField("RTG", max_length=60, blank=True, db_index=True)
    descricao = models.CharField("Descricao", max_length=255)
    enderecos = models.CharField("Enderecos", max_length=1024, blank=True)
    peso_bruto_kg = models.DecimalField("Peso bruto (kg)", max_digits=10, decimal_places=3, default=0)
    peso_liquido_kg = models.DecimalField("Peso liquido (kg)", max_digits=10, decimal_places=3, default=0)
    largura_cm = models.DecimalField("Largura (cm)", max_digits=8, decimal_places=2, default=0)
    altura_cm = models.DecimalField("Altura (cm)", max_digits=8, decimal_places=2, default=0)
    comprimento_cm = models.DecimalField("Comprimento (cm)", max_digits=8, decimal_places=2, default=0)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        permissions = (
            ("can_import_products", "Pode importar produtos"),
            ("can_import_clients", "Pode importar clientes"),
            ("can_view_reports", "Pode acessar relatorios"),
            ("can_view_warranty_management", "Pode acessar o gerencial de garantias"),
            ("can_use_calcular", "Pode usar a ferramenta Calcular"),
        )

    def __str__(self) -> str:
        return f"{self.codigo} - {self.descricao}"


class Cliente(models.Model):
    nome = models.CharField("Nome", max_length=255)
    cnpj = models.CharField("CNPJ", max_length=20, unique=True)
    endereco = models.CharField("Endereco", max_length=255, blank=True)
    cidade = models.CharField("Cidade", max_length=120, blank=True)
    estado = models.CharField("Estado", max_length=2, blank=True)
    email = models.EmailField("Email", blank=True)
    telefone = models.CharField("Telefone", max_length=40, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        indexes = [
            models.Index(fields=["nome"], name="cliente_nome_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.cnpj})"


class Garantia(models.Model):
    STATUS_EM_ABERTO = "em_aberto"
    STATUS_ATENDIDO = "atendido"

    TIPO_GARANTIA = "garantia"
    TIPO_DEVOLUCAO = "devolucao"
    TIPOS = (
        (TIPO_GARANTIA, "Garantia"),
        (TIPO_DEVOLUCAO, "Devolucao"),
    )

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="garantias")
    codigo_peca = models.CharField("Codigo da peca", max_length=80)
    marca = models.CharField("Marca", max_length=120, default="Nao Informado")
    quantidade = models.PositiveIntegerField("Quantidade", default=1)
    defeito = models.TextField("Defeito")
    numero_lote = models.CharField("Numero do lote", max_length=80, blank=True)
    nota_recebida = models.CharField("Nota recebida", max_length=80)
    valor = models.DecimalField("Valor", max_digits=12, decimal_places=2, default=0)
    data_recebimento = models.DateField("Data de recebimento")
    nota_retorno = models.CharField("Nota de retorno", max_length=80, blank=True)
    data_retorno = models.DateField("Data de retorno", null=True, blank=True)
    mao_de_obra = models.BooleanField("Com mao de obra", default=False)
    valor_mao_de_obra = models.DecimalField("Valor mao de obra", max_digits=12, decimal_places=2, default=0)
    tipo = models.CharField("Tipo", max_length=16, choices=TIPOS, default=TIPO_GARANTIA)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criado por",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="garantias_criadas",
    )
    alterado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Alterado por",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name="garantias_alteradas",
    )

    class Meta:
        ordering = ["-data_recebimento", "-id"]
        verbose_name = "Garantia"
        verbose_name_plural = "Garantias"
        indexes = [
            models.Index(fields=["data_recebimento"], name="garantia_data_idx"),
            models.Index(fields=["tipo"], name="garantia_tipo_idx"),
            models.Index(fields=["marca"], name="garantia_marca_idx"),
            models.Index(fields=["codigo_peca"], name="garantia_codigo_idx"),
        ]

    def __str__(self) -> str:
        return f"Garantia {self.id} - {self.cliente}"

    @property
    def status(self) -> str:
        return self.STATUS_ATENDIDO if self.nota_retorno else self.STATUS_EM_ABERTO


@receiver(pre_save, sender=Garantia)
def _upper_marca_on_save(sender, instance: "Garantia", **kwargs):
    try:
        marca = (getattr(instance, "marca", "") or "").strip()
        if not marca:
            instance.marca = "NAO INFORMADO"
        else:
            instance.marca = marca.upper()
    except Exception:
        # Nao impede o save caso algo inusitado ocorra
        pass


# Auditoria
class AuditLog(models.Model):
    ACTIONS = (
        ("create", "create"),
        ("update", "update"),
        ("delete", "delete"),
        ("import", "import"),
        ("export", "export"),
        ("login", "login"),
        ("logout", "logout"),
        ("view", "view"),
    )
    user = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
    username = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=16, choices=ACTIONS)
    module = models.CharField(max_length=50, blank=True)
    object_type = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    path = models.CharField(max_length=255, blank=True)
    method = models.CharField(max_length=8, blank=True)
    status_code = models.PositiveIntegerField(default=0)
    ip = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    changes = JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        indexes = [
            models.Index(fields=["created_at"], name="audit_created_idx"),
            models.Index(fields=["action"], name="audit_action_idx"),
            models.Index(fields=["module"], name="audit_module_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.created_at} {self.username} {self.action} {self.object_type}#{self.object_id}"


def _serialize_change_value(value):
    if isinstance(value, models.Model):
        return value.pk
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value

def _capture_original(instance):
    data = {}
    for f in instance._meta.fields:
        if f.name in ("id",):
            continue
        try:
            data[f.name] = _serialize_change_value(getattr(instance, f.name))
        except Exception:
            pass
    instance._original_state = data


def _log_model_action(instance, action):
    from django.contrib.auth.models import AnonymousUser
    try:
        changes = None
        if action == "update" and hasattr(instance, "_original_state"):
            changes = {}
            for k, old in instance._original_state.items():
                new = _serialize_change_value(getattr(instance, k, None))
                if old != new:
                    changes[k] = [old, new]
            if not changes:
                changes = None
    except Exception:
        changes = None
    AuditLog.objects.create(
        user=None,
        username="",
        action=action,
        module="model",
        object_type=instance.__class__.__name__,
        object_id=str(getattr(instance, "pk", "")),
        object_repr=str(instance)[:255],
        changes=changes,
    )


@receiver(pre_save, sender=Produto)
@receiver(pre_save, sender=Cliente)
@receiver(pre_save, sender=Garantia)
@receiver(pre_save, sender=Pedido)
@receiver(pre_save, sender=PedidoVolume)
def _pre_save_capture(sender, instance, **kwargs):
    if getattr(instance, "pk", None):
        try:
            original = sender.objects.get(pk=instance.pk)
            _capture_original(original)
            instance._original_state = getattr(original, "_original_state", {})
        except sender.DoesNotExist:
            instance._original_state = {}


@receiver(post_save, sender=Produto)
@receiver(post_save, sender=Cliente)
@receiver(post_save, sender=Garantia)
@receiver(post_save, sender=Pedido)
@receiver(post_save, sender=PedidoVolume)
def _post_save_log(sender, instance, created, **kwargs):
    _log_model_action(instance, "create" if created else "update")


@receiver(post_delete, sender=Produto)
@receiver(post_delete, sender=Cliente)
@receiver(post_delete, sender=Garantia)
@receiver(post_delete, sender=Pedido)
@receiver(post_delete, sender=PedidoVolume)
def _post_delete_log(sender, instance, **kwargs):
    _log_model_action(instance, "delete")








