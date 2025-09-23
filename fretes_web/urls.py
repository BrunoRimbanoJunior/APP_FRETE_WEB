from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
# Make admin "Ver site" link point to /fretes/ (relative, preserves host:port)
admin.site.site_url = "/fretes/"
urlpatterns = [
    path('admin/', admin.site.urls),
    path('fretes/', include('fretes.urls', namespace='fretes')),
    path('', RedirectView.as_view(pattern_name='fretes:index', permanent=False)),  # ✅
]
