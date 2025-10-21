from decimal import Decimal

import pytest
from django.test import TestCase

from fretes.models import Carrier, FreightTable
from fretes.services import calcular_frete


class Tipo2CalculoTest(TestCase):
    def setUp(self):
        self.carrier = Carrier.objects.create(nome="XPTO")
        # Configura tabela conforme planilha do anexo e descricao
        self.tab = FreightTable.objects.create(
            carrier=self.carrier,
            tipo_calculo=2,
            fator_peso_cubico=Decimal("230"),
            peso_ate_100=Decimal("119.27"),  # valor fixo para os primeiros 100kg
            frete_ton=Decimal("650.00"),      # 0.65 por kg no excedente
            frete_minimo=Decimal("0.00"),
            frete_valor_perc=Decimal("0.40"), # %
            gris_perc=Decimal("0.20"),        # %
            pedagio=Decimal("3.00"),          # valor por cada 100kg
            valor_despacho=Decimal("1.90"),
        )

    def test_calculo_tipo2_planilha(self):
        m3 = Decimal("1.235")
        kg_nota = Decimal("175")
        valor_nota = Decimal("16069.98")

        r = calcular_frete(m3, self.carrier, kg_nota, valor_nota)

        # Validacoes principais
        self.assertEqual(r["peso_cubico"], Decimal("284.05"))  # 1.235 * 230

        # Base: 100kg (119.27) + excedente(184.05)*0.65 = 119.63 => 238.90
        # Adicionais: frete_valor(0.4%)=64.28, gris(0.2%)=32.14, despacho=1.90
        # Pedagio: ceil(284.05/100)=3 blocos -> 3 * 3.00 = 9.00
        # Total esperado: 238.90 + 64.28 + 32.14 + 9.00 + 1.90 = 346.22
        self.assertEqual(r["frete_total"], Decimal("346.22"))
