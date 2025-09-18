
from decimal import Decimal
from django.db import models
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver

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

