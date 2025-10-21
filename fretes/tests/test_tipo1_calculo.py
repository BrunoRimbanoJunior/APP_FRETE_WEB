from decimal import Decimal

from django.test import TestCase

from fretes.models import Carrier, FreightTable
from fretes.services import calcular_frete


class Tipo1CalculoTest(TestCase):
    def setUp(self):
        self.carrier = Carrier.objects.create(nome="Tipo1 Co")
        # Parametros conforme tabela "IZABEL" (faixas + pedagio por blocos de 100kg)
        self.tab = FreightTable.objects.create(
            carrier=self.carrier,
            tipo_calculo=1,
            fator_peso_cubico=Decimal("230"),
            peso_ate_50=Decimal("81.47"),
            peso_ate_100=Decimal("91.66"),
            peso_ate_150=Decimal("103.28"),
            peso_ate_200=Decimal("113.47"),
            peso_ate_300=Decimal("133.84"),
            frete_ton=Decimal("509.16"),
            frete_minimo=Decimal("116.38"),
            frete_valor_perc=Decimal("0.23"),
            gris_perc=Decimal("0.00"),
            pedagio=Decimal("3.91"),
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

        # Total conforme planilha: base(<=300)=133.84 + frete_valor(0.23%)=36.96 + pedagio=ceil(284.05/100)*3.91=11.73
        self.assertEqual(r["frete_total"], Decimal("182.53"))
