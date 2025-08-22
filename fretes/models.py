from django.db import models
from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Carrier(models.Model):
    nome = models.CharField("Nome", max_length=120, unique=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Transportadora"
        verbose_name_plural = "Transportadoras"

    def __str__(self):
        return self.nome

class FreightTable(models.Model):
    carrier = models.OneToOneField(Carrier, on_delete=models.CASCADE, related_name="tabela")
    peso_ate_50   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_100  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_150  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_200  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    peso_ate_300  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frete_ton     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frete_minimo  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pedagio       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    frete_valor_perc = models.DecimalField(max_digits=6, decimal_places=3, default=0)  # %
    fator_peso_cubico = models.DecimalField(max_digits=10, decimal_places=2, default=230)

    class Meta:
        verbose_name = "Tabela de Frete"
        verbose_name_plural = "Tabelas de Frete"

    def __str__(self):
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

    def __str__(self):
        return self.numero_pedido

class PedidoVolume(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="volumes")
    largura_cm = models.DecimalField(max_digits=8, decimal_places=2)
    altura_cm = models.DecimalField(max_digits=8, decimal_places=2)
    comprimento_cm = models.DecimalField(max_digits=8, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)
    m3 = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        verbose_name = "Volume do Pedido"
        verbose_name_plural = "Volumes do Pedido"

    def __str__(self):
        return f"Volume {self.id} do {self.pedido}"

class FreteCalculado(models.Model):
    data_calculo = models.DateField(auto_now_add=True)
    numero_pedido = models.CharField(max_length=60)
    numero_nota = models.CharField(max_length=60, blank=True)
    valor_nota = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    kg_nota = models.DecimalField(max_digits=12, decimal_places=2)
    carrier = models.ForeignKey(Carrier, null=True, on_delete=models.SET_NULL)
    m3 = models.DecimalField(max_digits=12, decimal_places=3)
    peso_cubico = models.DecimalField(max_digits=12, decimal_places=2)
    peso_usado = models.DecimalField(max_digits=12, decimal_places=2)
    frete_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Frete Calculado"
        verbose_name_plural = "Fretes Calculados"
        constraints = [
            models.UniqueConstraint(
                fields=["numero_pedido", "carrier"],
                name="uniq_pedido_carrier"
            )
        ]

    def __str__(self):
        return f"{self.numero_pedido} - {self.carrier} - {self.frete_total}"




def _calc_m3_volume(v: "PedidoVolume") -> Decimal:
    # converte cm -> m e aplica quantidade
    l = Decimal(v.largura_cm) / Decimal("100")
    a = Decimal(v.altura_cm) / Decimal("100")
    c = Decimal(v.comprimento_cm) / Decimal("100")
    return (l * a * c) * Decimal(v.quantidade or 1)

def recomputa_m3_pedido(pedido: "Pedido"):
    total = Decimal("0")
    for v in pedido.volumes.all():
        total += _calc_m3_volume(v)
    pedido.m3 = total.quantize(Decimal("0.001"))
    pedido.save(update_fields=["m3"])

@receiver(post_save, sender=PedidoVolume)
def _pv_saved(sender, instance, **kwargs):
    # atualiza campo m3 do volume e do pedido
    m3 = _calc_m3_volume(instance).quantize(Decimal("0.001"))
    if instance.m3 != m3:
        PedidoVolume.objects.filter(pk=instance.pk).update(m3=m3)
    recomputa_m3_pedido(instance.pedido)

@receiver(post_delete, sender=PedidoVolume)
def _pv_deleted(sender, instance, **kwargs):
    recomputa_m3_pedido(instance.pedido)
