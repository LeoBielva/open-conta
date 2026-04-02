from django.contrib import admin

from .models import CuotaMexico, PagoSAT, Periodo, ResultadoReconciliacion


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "mes", "anio", "created_at")
    list_filter = ("anio",)


@admin.register(CuotaMexico)
class CuotaMexicoAdmin(admin.ModelAdmin):
    list_display = ("numero_contrato", "canal", "interes", "impuesto", "periodo")
    list_filter = ("canal", "periodo")
    search_fields = ("numero_contrato",)


@admin.register(PagoSAT)
class PagoSATAdmin(admin.ModelAdmin):
    list_display = ("numero_contrato", "canal", "interes", "impuesto", "periodo")
    list_filter = ("canal", "periodo")
    search_fields = ("numero_contrato",)


@admin.register(ResultadoReconciliacion)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = ("numero_contrato", "tipo", "canal", "interes", "impuesto", "periodo")
    list_filter = ("tipo", "canal", "periodo")
    search_fields = ("numero_contrato",)
