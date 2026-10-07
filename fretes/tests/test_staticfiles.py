import base64
import hashlib
import re
from pathlib import Path

from django.contrib.staticfiles import finders
from django.core.management import call_command


def test_collectstatic_preserva_integridade_e_gera_brotli(settings, tmp_path):
    settings.STATIC_ROOT = tmp_path / "staticfiles"
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    call_command("collectstatic", interactive=False, verbosity=0)
    from django.contrib.staticfiles.storage import staticfiles_storage

    root = Path(__file__).resolve().parents[1] / "templates" / "fretes"
    for template, asset in (
        ("base.html", "vendor/bootstrap/bootstrap-5.3.8.min.css"),
        ("_htmx_head.html", "vendor/htmx/htmx-2.0.11.min.js"),
    ):
        expected = re.search(r'integrity="(sha384-[^"]+)"', (root / template).read_text()).group(1)
        original = Path(finders.find(asset)).read_bytes()
        hashed_name = staticfiles_storage.stored_name(asset)
        processed = (settings.STATIC_ROOT / hashed_name).read_bytes()
        assert processed == original
        assert "sha384-" + base64.b64encode(hashlib.sha384(processed).digest()).decode() == expected
        assert Path(str(settings.STATIC_ROOT / hashed_name) + ".br").is_file()
