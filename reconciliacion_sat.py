"""
reconciliacion_sat.py
=====================
Compara CUOTAS_MEXICO <MES>.xlsx  vs  Base SAT Mexico <MES>.xlsx

Lógica:
  - Los archivos de entrada ya vienen filtrados (solo cuotas facturadas).
  - Se compara a nivel de fila por la clave compuesta:
        (numero_contrato, interes, impuesto)
    Los valores numéricos se redondean a 2 decimales antes de comparar para
    absorber diferencias de precisión entre los dos sistemas.

Salidas:
  PagosFaltantes<YYYYMMDD>.xlsx  →  filas en CUOTAS que NO tienen
                                    equivalente en SAT.
  PagosDeMas<YYYYMMDD>.xlsx      →  filas en SAT que NO tienen equivalente en
                                    CUOTAS.

  Cada archivo tiene 3 pestañas: aliados | oxxo | paynet
  Cada pestaña tiene las columnas: numero_contrato | interes | impuesto
  (permitiendo sumas de interes e impuesto por canal).

Uso:
  python reconciliacion_sat.py
  python reconciliacion_sat.py --dir /ruta/al/directorio
"""

import argparse
import os
import sys
from datetime import datetime

import pandas as pd


# ── Configuración ─────────────────────────────────────────────────────────────
MES = "MARZO"

SHEET_PAIRS = [
    # (hoja CUOTAS,  hoja SAT,   etiqueta salida)
    ("ALIADOS", "ALIADOS", "aliados"),
    ("OXXO",    "OXXO",    "oxxo"),
    ("PAYNET",  "PAYNET",  "paynet"),
]

# Columnas a leer de cada fuente
CUOTAS_COLS = ["numero_contrato", "interes", "impuesto"]
SAT_COLS    = ["numero_contrato", "INTERESES_PAGAR", "IMPUESTOS"]

# Columnas clave para el merge (nombre normalizado)
KEY_COLS = ["numero_contrato", "interes", "impuesto"]

DECIMAL_PLACES = 4  # precisión para comparar valores numéricos


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_cuotas_sheet(path: str, sheet: str) -> pd.DataFrame:
    """
    Lee la hoja de CUOTAS y devuelve las columnas clave con los numéricos
    redondeados.
    """
    df = pd.read_excel(path, sheet_name=sheet, usecols=CUOTAS_COLS)
    df["interes"]  = df["interes"].round(DECIMAL_PLACES)
    df["impuesto"] = df["impuesto"].round(DECIMAL_PLACES)
    return df.reset_index(drop=True)


def load_sat_sheet(path: str, sheet: str) -> pd.DataFrame:
    """
    Lee la hoja de SAT, renombra columnas a la clave normalizada y redondea.
    """
    df = pd.read_excel(path, sheet_name=sheet, usecols=SAT_COLS)
    df = df.rename(columns={
        "INTERESES_PAGAR": "interes",
        "IMPUESTOS":       "impuesto",
    })
    df["interes"]  = df["interes"].round(DECIMAL_PLACES)
    df["impuesto"] = df["impuesto"].round(DECIMAL_PLACES)
    return df.reset_index(drop=True)


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columna _seq para match 1-a-1 entre filas con la misma clave."""
    out = df[KEY_COLS].copy().reset_index(drop=True)
    out["_seq"] = out.groupby(KEY_COLS).cumcount()
    return out


def find_discrepancies(df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
    """Filas de df_left que NO tienen correspondencia en df_right."""
    left  = _prepare(df_left)
    right = _prepare(df_right)
    merged = left.merge(right, on=KEY_COLS + ["_seq"], how="left", indicator=True)
    return merged[merged["_merge"] == "left_only"][KEY_COLS].copy().reset_index(drop=True)


def find_matches(df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
    """Filas de df_left que SÍ tienen correspondencia en df_right."""
    left  = _prepare(df_left)
    right = _prepare(df_right)
    merged = left.merge(right, on=KEY_COLS + ["_seq"], how="left", indicator=True)
    return merged[merged["_merge"] == "both"][KEY_COLS].copy().reset_index(drop=True)


def write_output_xlsx(results: dict, path: str) -> dict:
    """
    Escribe un xlsx con una pestaña por canal (aliados, oxxo, paynet).
    Cada pestaña contiene: numero_contrato | interes | impuesto
    Al final de cada pestaña se agrega una fila de TOTAL.
    Devuelve un dict con los conteos de filas (sin contar la fila de total).
    """
    counts = {}
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        for label, df in results.items():
            out = df[KEY_COLS].reset_index(drop=True)

            # Fila de totales
            total_row = pd.DataFrame([{
                "numero_contrato": "TOTAL",
                "interes":  out["interes"].sum(),
                "impuesto": out["impuesto"].sum(),
            }])
            out_con_total = pd.concat([out, total_row], ignore_index=True)
            out_con_total.to_excel(w, sheet_name=label, index=False)
            counts[label] = len(out)
    return counts


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Reconciliación SAT vs CUOTAS")
    parser.add_argument(
        "--dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Directorio donde se encuentran los archivos xlsx (default: mismo directorio del script)",
    )
    args = parser.parse_args()

    base_dir = args.dir
    file_cuotas = os.path.join(base_dir, f"input/CUOTAS_MEXICO {MES}.xlsx")
    file_sat    = os.path.join(base_dir, f"input/Base SAT Mexico {MES}.xlsx")

    for f in [file_cuotas, file_sat]:
        if not os.path.exists(f):
            print(f"[ERROR] No se encontró el archivo: {f}", file=sys.stderr)
            sys.exit(1)

    date_str = datetime.now().strftime("%Y%m%d")
    out_faltantes = os.path.join(base_dir, f"output/PagosFaltantes{date_str}.xlsx")
    out_de_mas    = os.path.join(base_dir, f"output/PagosDeMas{date_str}.xlsx")
    out_completo  = os.path.join(base_dir, f"output/PagoCompleto{date_str}.xlsx")

    pagos_faltantes: dict[str, pd.DataFrame] = {}
    pagos_de_mas:    dict[str, pd.DataFrame] = {}
    pagos_completo:  dict[str, pd.DataFrame] = {}

    for cuotas_sheet, sat_sheet, label in SHEET_PAIRS:
        print(f"\n{'─'*60}")
        print(f"  Procesando: {label.upper()}")
        print(f"    CUOTAS hoja : {cuotas_sheet}")
        print(f"    SAT hoja    : {sat_sheet}")

        df_cuotas = load_cuotas_sheet(file_cuotas, cuotas_sheet)
        df_sat    = load_sat_sheet(file_sat, sat_sheet)

        print(f"    Filas CUOTAS : {len(df_cuotas):,}")
        print(f"    Filas SAT    : {len(df_sat):,}")

        # ── Comparación 1: numero_contrato  (+ interes + impuesto como clave)
        # ── Comparación 2: interes / INTERESES_PAGAR
        # ── Comparación 3: impuesto / IMPUESTOS
        # Las 3 comparaciones se resuelven en un solo merge por clave compuesta.

        # PagosFaltantes: en CUOTAS pero no en SAT
        faltantes = find_discrepancies(df_cuotas, df_sat)

        # PagosDeMas: en SAT pero no en CUOTAS
        de_mas = find_discrepancies(df_sat, df_cuotas)

        print(f"    → PagosFaltantes : {len(faltantes):,}  "
              f"(en CUOTAS/{cuotas_sheet} sin equivalente en SAT/{sat_sheet})")
        print(f"    → PagosDeMas     : {len(de_mas):,}  "
              f"(en SAT/{sat_sheet} sin equivalente en CUOTAS/{cuotas_sheet})")

        completo = find_matches(df_cuotas, df_sat)

        print(f"    → PagoCompleto   : {len(completo):,}  "
              f"(coincidencias exactas entre CUOTAS/{cuotas_sheet} y SAT/{sat_sheet})")

        pagos_faltantes[label] = faltantes.dropna(subset=["numero_contrato"]).reset_index(drop=True)
        pagos_de_mas[label]    = de_mas.dropna(subset=["numero_contrato"]).reset_index(drop=True)
        pagos_completo[label]  = completo.dropna(subset=["numero_contrato"]).reset_index(drop=True)

    # ── Generar archivos de salida ─────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("  Generando archivos de salida…")

    counts_falt     = write_output_xlsx(pagos_faltantes, out_faltantes)
    counts_demas    = write_output_xlsx(pagos_de_mas,    out_de_mas)
    counts_completo = write_output_xlsx(pagos_completo,  out_completo)

    # ── Resumen en consola ────────────────────────────────────────────────────
    labels = [pair[2] for pair in SHEET_PAIRS]

    def print_file_totals(filename: str, results: dict):
        print(f"\n  {filename}")
        for lbl in labels:
            df    = results[lbl]
            t_int = df['interes'].sum()
            t_imp = df['impuesto'].sum()
            print(f"    {lbl:<10}  interés: {t_int:>14,.2f}   impuesto: {t_imp:>14,.2f}   total: {t_int+t_imp:>14,.2f}")

    print(f"\n{'─'*60}")
    print_file_totals(os.path.basename(out_faltantes), pagos_faltantes)
    print_file_totals(os.path.basename(out_de_mas),    pagos_de_mas)
    print_file_totals(os.path.basename(out_completo),  pagos_completo)

    print(f"\n{'─'*60}\n  Listo.\n")


if __name__ == "__main__":
    main()
