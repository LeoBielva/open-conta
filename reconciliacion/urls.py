from django.urls import path

from . import views

app_name = "reconciliacion"

urlpatterns = [
    path("periodos/", views.PeriodoListCreateView.as_view(), name="periodos"),
    path("reconciliacion/upload/", views.UploadReconciliacionView.as_view(), name="upload"),
    path("reconciliacion/resultados/", views.ResultadosListView.as_view(), name="resultados"),
    path("reconciliacion/resumen/", views.ResumenView.as_view(), name="resumen"),
]
