"""
Modelos para la reconciliacion SAT.

Los datos que antes vivian en archivos Excel ahora se almacenan en
PostgreSQL (Supabase). Cada fila de cuota o pago SAT se guarda con su
canal y periodo.
"""

from django.db import models


class Canal(models.TextChoices):
    ALIADOS = "aliados", "Aliados"
    OXXO = "oxxo", "Oxxo"
    PAYNET = "paynet", "Paynet"


class Periodo(models.Model):
    """Periodo mensual de reconciliacion (ej. Marzo 2026)."""

    class Mes(models.IntegerChoices):
        ENERO = 1, "Enero"
        FEBRERO = 2, "Febrero"
        MARZO = 3, "Marzo"
        ABRIL = 4, "Abril"
        MAYO = 5, "Mayo"
        JUNIO = 6, "Junio"
        JULIO = 7, "Julio"
        AGOSTO = 8, "Agosto"
        SEPTIEMBRE = 9, "Septiembre"
        OCTUBRE = 10, "Octubre"
        NOVIEMBRE = 11, "Noviembre"
        DICIEMBRE = 12, "Diciembre"

    mes = models.IntegerField(choices=Mes.choices)
    anio = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("mes", "anio")
        ordering = ["-anio", "-mes"]
        verbose_name = "Periodo"
        verbose_name_plural = "Periodos"

    def __str__(self):
        return f"{self.get_mes_display()} {self.anio}"


class CuotaMexico(models.Model):
    """Fila del archivo CUOTAS_MEXICO (ya filtrada / facturada)."""

    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="cuotas")
    canal = models.CharField(max_length=10, choices=Canal.choices)
    numero_contrato = models.CharField(max_length=50)
    interes = models.DecimalField(max_digits=16, decimal_places=4)
    impuesto = models.DecimalField(max_digits=16, decimal_places=4)

    class Meta:
        verbose_name = "Cuota Mexico"
        verbose_name_plural = "Cuotas Mexico"
        indexes = [
            models.Index(fields=["periodo", "canal"]),
            models.Index(fields=["numero_contrato"]),
        ]

    def __str__(self):
        return f"CUOTA {self.canal} | {self.numero_contrato}"


class PagoSAT(models.Model):
    """Fila del archivo Base SAT Mexico."""

    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="pagos_sat")
    canal = models.CharField(max_length=10, choices=Canal.choices)
    numero_contrato = models.CharField(max_length=50)
    interes = models.DecimalField(max_digits=16, decimal_places=4)
    impuesto = models.DecimalField(max_digits=16, decimal_places=4)

    class Meta:
        verbose_name = "Pago SAT"
        verbose_name_plural = "Pagos SAT"
        indexes = [
            models.Index(fields=["periodo", "canal"]),
            models.Index(fields=["numero_contrato"]),
        ]

    def __str__(self):
        return f"SAT {self.canal} | {self.numero_contrato}"


class ResultadoReconciliacion(models.Model):
    """Resultado de una ejecucion de reconciliacion."""

    class Tipo(models.TextChoices):
        FALTANTE = "faltante", "Pago Faltante"
        DE_MAS = "de_mas", "Pago de Mas"
        COMPLETO = "completo", "Pago Completo"

    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="resultados")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    canal = models.CharField(max_length=10, choices=Canal.choices)
    numero_contrato = models.CharField(max_length=50)
    interes = models.DecimalField(max_digits=16, decimal_places=4)
    impuesto = models.DecimalField(max_digits=16, decimal_places=4)
    ejecutado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Resultado Reconciliacion"
        verbose_name_plural = "Resultados Reconciliacion"
        indexes = [
            models.Index(fields=["periodo", "tipo", "canal"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.canal} | {self.numero_contrato}"
