from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog
from django.shortcuts import redirect
from django.urls import reverse


class AuditMiddleware(MiddlewareMixin):
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def process_response(self, request, response):
        try:
            # Loga somente alterações ou acessos importantes
            should_log = request.method not in self.SAFE_METHODS
            # Exportações/Importações também
            if request.method == "GET" and (
                request.path.endswith("/relatorios/")
                or request.GET.get("export") in {"xlsx", "pdf"}
                or "/admin/tools/" in request.path
            ):
                should_log = True
            if not should_log:
                return response

            user = getattr(request, "user", None)
            username = ""
            u = None
            if user and user.is_authenticated:
                username = user.get_username()
                u = user
            ua = request.META.get("HTTP_USER_AGENT", "")[:255]
            ip = request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR", "")
            module = "tools" if "/admin/tools/" in request.path else "view"

            AuditLog.objects.create(
                user=u,
                username=username,
                action="view" if request.method == "GET" else request.method.lower(),
                module=module,
                object_type="",
                object_id="",
                object_repr="",
                path=request.path[:255],
                method=request.method,
                status_code=getattr(response, "status_code", 0) or 0,
                ip=str(ip)[:64],
                user_agent=ua,
            )
        except Exception:
            # Nunca quebrar a requisição por conta de log
            pass
        return response


class LoginRequiredForAppMiddleware(MiddlewareMixin):
    WHITELIST_PREFIXES = (
        "/static/",
        "/admin/login/",
    )

    def process_request(self, request):
        path = request.path or ""
        if not path.startswith("/fretes/"):
            return None
        if any(path.startswith(p) for p in self.WHITELIST_PREFIXES):
            return None
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return None
        # Redireciona para login do admin, preservando next
        login_url = "/admin/login/?next=" + path
        return redirect(login_url)
