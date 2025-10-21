from decimal import Decimal

from django.test import TestCase

from fretes.models import Carrier, FreightTable
from fretes.services import calcular_frete


class Tipo1CalculoTest(TestCase):
    def setUp(self):
        self.carrier = Carrier.objects.create(nome="Tipo1 Co")
        # Parametros configurados para refletir a planilha fornecida,
        # mantendo a logica do tipo 1 atual (faixas + pedagio linear).
        self.tab = FreightTable.objects.create(
            carrier=self.carrier,
            tipo_calculo=1,
            fator_peso_cubico=Decimal("230"),
            peso_ate_300=Decimal("161.12"),  # base para <= 300 kg
            frete_ton=Decimal("650.00"),
            frete_minimo=Decimal("0.00"),
            frete_valor_perc=Decimal("0.20"),  # %
            gris_perc=Decimal("0.00"),         # nao considerado no exemplo
            pedagio=Decimal("4.75"),            # ajustado para pedagio linear
            valor_despacho=Decimal("0.00"),
        )

    def test_calculo_tipo1(self):
        # Dados do exemplo
        m3 = Decimal("1.235")
        kg_nota = Decimal("175")
        valor_nota = Decimal("16069.98")

        r = calcular_frete(m3, self.carrier, kg_nota, valor_nota)

        # Peso cubico considerando fator 230
        self.assertEqual(r["peso_cubico"], Decimal("284.05"))

        # Total conforme regras do tipo 1: base(161.12) + frete_valor(32.14) + pedagio(~13.48)
        # Pedagio linear = (284.05/100) * 4.75 = 13.48 (arredondado 0.01)
        self.assertEqual(r["frete_total"], Decimal("206.75"))

