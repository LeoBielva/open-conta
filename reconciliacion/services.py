"""
Logica de reconciliacion extraida de reconciliacion_sat.py.

Trabaja con DataFrames de pandas para la comparacion, pero persiste
los resultados en la base de datos via los modelos Django.
"""

from decimal import Decimal
from io import BytesIO

import pandas as pd

from .models import Canal, CuotaMexico, PagoSAT, Periodo, ResultadoReconciliacion

# ── Configuracion ─────────────────────────────────────────────────────────────

CUOTAS_COLS = ["numero_contrato", "interes", "impuesto"]
SAT_COLS = ["numero_contrato", "INTERESES_PAGAR", "IMPUESTOS"]
KEY_COLS = ["numero_contrato", "interes", "impuesto"]
DECIMAL_PLACES = 4

SHEET_MAP = {
    "ALIADOS": Canal.ALIADOS,
    "OXXO": Canal.OXXO,
    "PAYNET": Canal.PAYNET,
}


# ── Helpers (misma logica que el script original) ─────────────────────────────

def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columna _seq para match 1-a-1 entre filas con la misma clave."""
    out = df[KEY_COLS].copy().reset_index(drop=True)
    out["_seq"] = out.groupby(KEY_COLS).cumcount()
    return out


def _find_discrepancies(df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
    """Filas de df_left que NO tienen correspondencia en df_right."""
    left = _prepare(df_left)
    right = _prepare(df_right)
    merged = left.merge(right, on=KEY_COLS + ["_seq"], how="left", indicator=True)
    return merged.loc[merged["_merge"] == "left_only", KEY_COLS].reset_index(drop=True)


def _find_matches(df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
    """Filas de df_left que SI tienen correspondencia en df_right."""
    left = _prepare(df_left)
    right = _prepare(df_right)
    merged = left.merge(right, on=KEY_COLS + ["_seq"], how="left", indicator=True)
    return merged.loc[merged["_merge"] == "both", KEY_COLS].reset_index(drop=True)


# ── Carga de Excel a DB ──────────────────────────────────────────────────────

def _load_cuotas_sheet(file_bytes: bytes, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet, usecols=CUOTAS_COLS)
    df["interes"] = df["interes"].round(DECIMAL_PLACES)
    df["impuesto"] = df["impuesto"].round(DECIMAL_PLACES)
    return df.reset_index(drop=True)


def _load_sat_sheet(file_bytes: bytes, sheet: str) -> pd.DataFrame:
    df = pd.read_excel(BytesIO(file_bytes), sheet_name=sheet, usecols=SAT_COLS)
    df = df.rename(columns={"INTERESES_PAGAR": "interes", "IMPUESTOS": "impuesto"})
    df["interes"] = df["interes"].round(DECIMAL_PLACES)
    df["impuesto"] = df["impuesto"].round(DECIMAL_PLACES)
    return df.reset_index(drop=True)


def importar_cuotas(periodo: Periodo, file_bytes: bytes) -> int:
    """Lee todas las hojas del archivo CUOTAS y persiste en DB. Retorna total de filas."""
    total = 0
    # Limpiar datos previos del periodo
    CuotaMexico.objects.filter(periodo=periodo).delete()

    for sheet_name, canal_value in SHEET_MAP.items():
        df = _load_cuotas_sheet(file_bytes, sheet_name)
        objs = [
            CuotaMexico(
                periodo=periodo,
                canal=canal_value,
                numero_contrato=row["numero_contrato"],
                interes=Decimal(str(row["interes"])),
                impuesto=Decimal(str(row["impuesto"])),
            )
            for _, row in df.iterrows()
            if pd.notna(row["numero_contrato"])
        ]
        CuotaMexico.objects.bulk_create(objs, batch_size=5000)
        total += len(objs)
    return total


def importar_sat(periodo: Periodo, file_bytes: bytes) -> int:
    """Lee todas las hojas del archivo SAT y persiste en DB. Retorna total de filas."""
    total = 0
    PagoSAT.objects.filter(periodo=periodo).delete()

    for sheet_name, canal_value in SHEET_MAP.items():
        df = _load_sat_sheet(file_bytes, sheet_name)
        objs = [
            PagoSAT(
                periodo=periodo,
                canal=canal_value,
                numero_contrato=row["numero_contrato"],
                interes=Decimal(str(row["interes"])),
                impuesto=Decimal(str(row["impuesto"])),
            )
            for _, row in df.iterrows()
            if pd.notna(row["numero_contrato"])
        ]
        PagoSAT.objects.bulk_create(objs, batch_size=5000)
        total += len(objs)
    return total


# ── Reconciliacion ────────────────────────────────────────────────────────────

def ejecutar_reconciliacion(periodo: Periodo) -> dict:
    """
    Ejecuta la reconciliacion para un periodo dado.
    Compara CuotaMexico vs PagoSAT por canal y guarda ResultadoReconciliacion.
    Retorna resumen con conteos por tipo y canal.
    """
    # Limpiar resultados previos
    ResultadoReconciliacion.objects.filter(periodo=periodo).delete()

    resumen = {}

    for canal_value, canal_label in Canal.choices:
        cuotas_qs = CuotaMexico.objects.filter(periodo=periodo, canal=canal_value)
        sat_qs = PagoSAT.objects.filter(periodo=periodo, canal=canal_value)

        df_cuotas = pd.DataFrame(
            cuotas_qs.values("numero_contrato", "interes", "impuesto")
        )
        df_sat = pd.DataFrame(
            sat_qs.values("numero_contrato", "interes", "impuesto")
        )

        # Convertir Decimal a float para pandas
        for col in ["interes", "impuesto"]:
            if not df_cuotas.empty:
                df_cuotas[col] = df_cuotas[col].astype(float)
            if not df_sat.empty:
                df_sat[col] = df_sat[col].astype(float)

        if df_cuotas.empty and df_sat.empty:
            continue

        # Faltantes (en CUOTAS pero no en SAT)
        faltantes = _find_discrepancies(df_cuotas, df_sat) if not df_cuotas.empty else pd.DataFrame()
        # De mas (en SAT pero no en CUOTAS)
        de_mas = _find_discrepancies(df_sat, df_cuotas) if not df_sat.empty else pd.DataFrame()
        # Completos (match exacto)
        completos = _find_matches(df_cuotas, df_sat) if not df_cuotas.empty else pd.DataFrame()

        # Persistir resultados
        def _crear_resultados(df, tipo):
            if df.empty:
                return 0
            df = df.dropna(subset=["numero_contrato"])
            objs = [
                ResultadoReconciliacion(
                    periodo=periodo,
                    tipo=tipo,
                    canal=canal_value,
                    numero_contrato=row["numero_contrato"],
                    interes=Decimal(str(row["interes"])),
                    impuesto=Decimal(str(row["impuesto"])),
                )
                for _, row in df.iterrows()
            ]
            ResultadoReconciliacion.objects.bulk_create(objs, batch_size=5000)
            return len(objs)

        n_falt = _crear_resultados(faltantes, ResultadoReconciliacion.Tipo.FALTANTE)
        n_demas = _crear_resultados(de_mas, ResultadoReconciliacion.Tipo.DE_MAS)
        n_comp = _crear_resultados(completos, ResultadoReconciliacion.Tipo.COMPLETO)

        resumen[canal_value] = {
            "faltantes": n_falt,
            "de_mas": n_demas,
            "completos": n_comp,
        }

    return resumen
