import pytest


@pytest.fixture(autouse=True)
def staticfiles_sem_manifest(settings):
    """Testes nao dependem de um collectstatic executado anteriormente."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
