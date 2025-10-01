
from decimal import Decimal
from datetime import date, datetime
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
    peso_ate_50 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_100 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_150 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_200 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_300 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frete_ton = models.DecimalField("Frete por Tonelada", max_digits=10, decimal_places=2, default=0)
    frete_minimo = models.DecimalField("Frete Mínimo", max_digits=10, decimal_places=2, default=0)
    pedagio = models.DecimalField("Pedágio", max_digits=10, decimal_places=2, default=0)
    frete_valor_perc = models.DecimalField("Frete Valor %", max_digits=6, decimal_places=3, default=0)
    fator_peso_cubico = models.DecimalField("Fator Peso Cúbico", max_digits=10, decimal_places=2, default=230)

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
    # ⚠️ importante: default=0 para não quebrar no insert
    m3 = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        verbose_name = "Volume do Pedido"
        verbose_name_plural = "Volumes do Pedido"

    def __str__(self) -> str:
        return f"{self.pedido} - {self.largura_cm}×{self.altura_cm}×{self.comprimento_cm} × {self.quantidade}"

class FreteCalculado(models.Model):
    data_calculo = models.DateField(auto_now_add=True)
    numero_pedido = models.CharField(max_length=60)
    numero_nota = models.CharField(max_length=60, blank=True)
    valor_nota = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    kg_nota = models.DecimalField(max_digits=12, decimal_places=2)
    m3 = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    peso_cubico = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    peso_usado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    frete_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    carrier = models.ForeignKey(Carrier, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Frete Calculado"
        verbose_name_plural = "Fretes Calculados"
        constraints = [
            models.UniqueConstraint(fields=["numero_pedido", "carrier"], name="uniq_pedido_carrier")
        ]

    def __str__(self) -> str:
        return f"{self.numero_pedido} - {self.carrier} - {self.frete_total}"


# Novos cadastros
class Produto(models.Model):
    codigo = models.CharField("Código", max_length=60, unique=True)
    descricao = models.CharField("Descrição", max_length=255)
    peso_bruto_kg = models.DecimalField("Peso bruto (kg)", max_digits=10, decimal_places=3, default=0)
    peso_liquido_kg = models.DecimalField("Peso líquido (kg)", max_digits=10, decimal_places=3, default=0)
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
            ("can_view_reports", "Pode acessar relatórios"),
            ("can_use_calcular", "Pode usar a ferramenta Calcular"),
        )

    def __str__(self) -> str:
        return f"{self.codigo} - {self.descricao}"


class Cliente(models.Model):
    nome = models.CharField("Nome", max_length=255)
    cnpj = models.CharField("CNPJ", max_length=20, unique=True)
    endereco = models.CharField("Endereço", max_length=255, blank=True)
    cidade = models.CharField("Cidade", max_length=120, blank=True)
    estado = models.CharField("Estado", max_length=2, blank=True)
    email = models.EmailField("Email", blank=True)
    telefone = models.CharField("Telefone", max_length=40, blank=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return f"{self.nome} ({self.cnpj})"


class Garantia(models.Model):
    STATUS_EM_ABERTO = "em_aberto"
    STATUS_ATENDIDO = "atendido"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="garantias")
    codigo_peca = models.CharField("Código da peça", max_length=80)
    defeito = models.TextField("Defeito")
    numero_lote = models.CharField("Número do lote", max_length=80, blank=True)
    nota_recebida = models.CharField("Nota recebida", max_length=80)
    valor = models.DecimalField("Valor", max_digits=12, decimal_places=2, default=0)
    data_recebimento = models.DateField("Data de recebimento")
    nota_retorno = models.CharField("Nota de retorno", max_length=80, blank=True)
    data_retorno = models.DateField("Data de retorno", null=True, blank=True)
    mao_de_obra = models.BooleanField("Com mão de obra", default=False)
    valor_mao_de_obra = models.DecimalField("Valor mão de obra", max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-data_recebimento", "-id"]
        verbose_name = "Garantia"
        verbose_name_plural = "Garantias"

    def __str__(self) -> str:
        return f"Garantia {self.id} - {self.cliente}"

    @property
    def status(self) -> str:
        return self.STATUS_ATENDIDO if self.nota_retorno else self.STATUS_EM_ABERTO


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

    def __str__(self) -> str:
        return f"{self.created_at} {self.username} {self.action} {self.object_type}#{self.object_id}"


def _serialize_change_value(value):
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
                new = getattr(instance, k, None)
                if old != new:
                    changes[k] = [_serialize_change_value(old), _serialize_change_value(new)]
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






