"""
API views para la reconciliacion SAT.
"""

from django.db.models import Count, Sum
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permissions import IsAdmin, IsAdminOrReadOnly

from .models import Periodo, ResultadoReconciliacion
from .serializers import (
    PeriodoSerializer,
    ResumenCanalSerializer,
    ResultadoSerializer,
    UploadSerializer,
)
from .services import ejecutar_reconciliacion, importar_cuotas, importar_sat


class PeriodoListCreateView(generics.ListCreateAPIView):
    """GET: listar periodos. POST: crear periodo (admin)."""

    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer
    permission_classes = [IsAdminOrReadOnly]


class UploadReconciliacionView(APIView):
    """
    POST: Sube archivos Excel de CUOTAS y SAT, importa datos y ejecuta
    la reconciliacion para el periodo indicado.
    Solo admin.
    """

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        periodo_id = serializer.validated_data["periodo_id"]
        try:
            periodo = Periodo.objects.get(pk=periodo_id)
        except Periodo.DoesNotExist:
            return Response(
                {"error": f"Periodo {periodo_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cuotas_bytes = serializer.validated_data["archivo_cuotas"].read()
        sat_bytes = serializer.validated_data["archivo_sat"].read()

        # Importar datos
        n_cuotas = importar_cuotas(periodo, cuotas_bytes)
        n_sat = importar_sat(periodo, sat_bytes)

        # Ejecutar reconciliacion
        resumen = ejecutar_reconciliacion(periodo)

        return Response(
            {
                "periodo": str(periodo),
                "filas_cuotas": n_cuotas,
                "filas_sat": n_sat,
                "resumen": resumen,
            },
            status=status.HTTP_201_CREATED,
        )


class ResultadosListView(generics.ListAPIView):
    """
    GET: Consultar resultados de reconciliacion.
    Filtros via query params: periodo, tipo, canal.
    """

    serializer_class = ResultadoSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = ResultadoReconciliacion.objects.all()
        periodo = self.request.query_params.get("periodo")
        tipo = self.request.query_params.get("tipo")
        canal = self.request.query_params.get("canal")

        if periodo:
            qs = qs.filter(periodo_id=periodo)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if canal:
            qs = qs.filter(canal=canal)

        return qs.order_by("canal", "numero_contrato")


class ResumenView(APIView):
    """
    GET: Resumen de totales por tipo y canal para un periodo dado.
    Query param requerido: periodo.
    """

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        periodo_id = request.query_params.get("periodo")
        if not periodo_id:
            return Response(
                {"error": "El query param 'periodo' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultados = (
            ResultadoReconciliacion.objects.filter(periodo_id=periodo_id)
            .values("tipo", "canal")
            .annotate(
                conteo=Count("id"),
                total_interes=Sum("interes"),
                total_impuesto=Sum("impuesto"),
            )
            .order_by("tipo", "canal")
        )

        serializer = ResumenCanalSerializer(resultados, many=True)
        return Response(serializer.data)
