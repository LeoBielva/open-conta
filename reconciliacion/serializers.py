from rest_framework import serializers

from .models import CuotaMexico, PagoSAT, Periodo, ResultadoReconciliacion


class PeriodoSerializer(serializers.ModelSerializer):
    mes_display = serializers.CharField(source="get_mes_display", read_only=True)

    class Meta:
        model = Periodo
        fields = ["id", "mes", "mes_display", "anio", "created_at"]


class CuotaMexicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuotaMexico
        fields = ["id", "periodo", "canal", "numero_contrato", "interes", "impuesto"]


class PagoSATSerializer(serializers.ModelSerializer):
    class Meta:
        model = PagoSAT
        fields = ["id", "periodo", "canal", "numero_contrato", "interes", "impuesto"]


class ResultadoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ResultadoReconciliacion
        fields = [
            "id", "periodo", "tipo", "tipo_display",
            "canal", "numero_contrato", "interes", "impuesto",
        ]


class UploadSerializer(serializers.Serializer):
    """Validacion para el endpoint de upload de archivos Excel."""
    periodo_id = serializers.IntegerField()
    archivo_cuotas = serializers.FileField()
    archivo_sat = serializers.FileField()


class ResumenCanalSerializer(serializers.Serializer):
    """Resumen de totales por canal."""
    canal = serializers.CharField()
    tipo = serializers.CharField()
    conteo = serializers.IntegerField()
    total_interes = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_impuesto = serializers.DecimalField(max_digits=16, decimal_places=2)
