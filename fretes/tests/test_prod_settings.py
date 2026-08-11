import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured


def test_producao_exige_secret_key(monkeypatch):
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    sys.modules.pop("fretes_web.settings.prod", None)

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        importlib.import_module("fretes_web.settings.prod")
