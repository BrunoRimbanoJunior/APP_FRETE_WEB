# fretes/filters.py
import django_filters
from django import forms
from .models import FreteCalculado, Carrier

class FreteCalculadoFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="data_calculo",
        lookup_expr="gte",
        label="De",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    end_date = django_filters.DateFilter(
        field_name="data_calculo",
        lookup_expr="lte",
        label="Até",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"})
    )
    carrier = django_filters.ModelChoiceFilter(
        queryset=Carrier.objects.all(),
        label="Transportadora"
    )

    class Meta:
        model = FreteCalculado
        fields = ["carrier", "start_date", "end_date"]
