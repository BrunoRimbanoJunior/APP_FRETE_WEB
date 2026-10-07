import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from fretes.models import AuditLog


@pytest.mark.django_db
def test_auditoria_renderiza_opcoes_e_preserva_filtros(client):
    user = User.objects.create_superuser(username="auditor", password="senha")
    AuditLog.objects.create(action="export", module="tools", object_repr="Exportação procurada")
    AuditLog.objects.create(action="create", module="model", object_repr="Registro fora do filtro")
    client.force_login(user)
    response = client.get(reverse("fretes:audit_logs"), {"action": "export", "module": "tools"})
    assert response.status_code == 200
    assert len(response.context["logs"]) == 1
    assert response.context["logs"][0].object_repr == "Exportação procurada"
    assert 'value="export" selected' in response.content.decode()
    assert 'value="tools" selected' in response.content.decode()


@pytest.mark.django_db
def test_auditoria_exige_permissao(client):
    user = User.objects.create_user(username="sem-auditoria", password="senha")
    client.force_login(user)
    assert client.get(reverse("fretes:audit_logs")).status_code == 403
