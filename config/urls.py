from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("reconciliacion.urls")),
    # Catch-all: serve React SPA for any non-API, non-admin route
    re_path(r"^(?!api/|admin/).*$", TemplateView.as_view(template_name="index.html")),
]
