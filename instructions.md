# Documentación — `reconciliacion_sat.py`

## Descripción general

Script de reconciliación contable que compara dos fuentes de datos:

- **CUOTAS_MEXICO \<MES\>.xlsx** — archivo base con cuotas facturadas por canal de cobro (ya filtrado).
- **Base SAT Mexico \<MES\>.xlsx** — extracción del SAT con los pagos registrados por canal.

El objetivo es identificar qué pagos están en CUOTAS pero no en el SAT (*faltantes*), qué pagos están en el SAT pero no en CUOTAS (*de más*), y qué pagos coinciden exactamente en ambas fuentes (*completos*).

---

## Requerimientos

### Python
- Python 3.10 o superior (pyenv disponible globalmente)

### Dependencias
```
pandas
openpyxl
```
Instalación:
```bash
pip install pandas openpyxl
```

### Archivos de entrada
Ambos archivos deben estar en el mismo directorio que el script (o especificar la ruta con `--dir`):

| Archivo | Descripción |
|---|---|
| `CUOTAS_MEXICO <MES>.xlsx` | Archivo base con cuotas por canal (ya filtrado) |
| `Base SAT Mexico <MES>.xlsx` | Extracción SAT con pagos registrados |

---

## Archivos de salida

El script genera tres archivos `.xlsx` en el mismo directorio, con la fecha de ejecución en el nombre:

| Archivo | Contenido |
|---|---|
| `PagosFaltantes<YYYYMMDD>.xlsx` | Filas en CUOTAS que no tienen equivalente en el SAT |
| `PagosDeMas<YYYYMMDD>.xlsx` | Filas en el SAT que no tienen equivalente en CUOTAS |
| `PagoCompleto<YYYYMMDD>.xlsx` | Filas que coinciden exactamente en ambas fuentes |

Cada archivo contiene **3 pestañas**: `aliados`, `oxxo`, `paynet`.

Cada pestaña contiene las columnas:

| Columna | Tipo | Descripción |
|---|---|---|
| `numero_contrato` | string | Identificador del contrato |
| `interes` | número | Monto de interés (redondeado a 8 decimales) |
| `impuesto` | número | Monto de impuesto (redondeado a 8 decimales) |

Al final de cada pestaña se incluye una fila `TOTAL` con la suma de `interes` e `impuesto`.

---

## Uso

```bash
# Desde el mismo directorio donde están los archivos
python reconciliacion_sat.py

# Especificando el directorio de los archivos
python reconciliacion_sat.py --dir /ruta/al/directorio
```

---

## Lógica paso a paso

### Paso 1 — Carga y filtrado de CUOTAS

Para cada canal se lee la hoja correspondiente del archivo CUOTAS:

| Canal | Hoja CUOTAS |
|---|---|
| aliados | `ALIADOS` |
| oxxo | `OXXO` |
| paynet | `PAYNET` |

Los archivos ya vienen pre-filtrados (solo cuotas facturadas). Las columnas que se extraen son `numero_contrato`, `interes` e `impuesto`.

### Paso 2 — Carga del SAT

Para cada canal se lee la hoja correspondiente del archivo SAT:

| Canal | Hoja SAT |
|---|---|
| aliados | `ALIADOS` |
| oxxo | `OXXO` |
| paynet | `PAYNET` |

Las columnas relevantes son `numero_contrato`, `INTERESES_PAGAR` e `IMPUESTOS`. Estas se renombran a `numero_contrato`, `interes` e `impuesto` para unificar el esquema con CUOTAS.

### Paso 3 — Normalización numérica

Los valores de `interes` e `impuesto` de ambas fuentes se redondean a **8 decimales** (`DECIMAL_PLACES = 8`) antes de cualquier comparación. Esto absorbe diferencias menores de punto flotante entre sistemas manteniendo alta precisión.

### Paso 4 — Comparación por clave compuesta

La comparación se realiza sobre la **clave compuesta**:
```
(numero_contrato, interes, impuesto)
```

Para manejar correctamente contratos con múltiples cuotas del mismo monto, se utiliza `cumcount()` de pandas: numera cada ocurrencia de una misma clave dentro de su grupo (0, 1, 2...) y la incluye como columna `_seq` antes del merge. Esto garantiza un match **1 a 1** entre filas idénticas:

- Si CUOTAS tiene **4 filas** con la misma clave y SAT tiene **3**, se reporta **1 faltante**.
- Si SAT tiene **3 filas** con la misma clave y CUOTAS tiene **1**, se reportan **2 de más**.

### Paso 5 — Clasificación de resultados

Usando merge con `indicator=True`:

| Resultado | Origen | Criterio |
|---|---|---|
| **PagosFaltantes** | CUOTAS | Filas de CUOTAS sin equivalente en SAT |
| **PagosDeMas** | SAT | Filas de SAT sin equivalente en CUOTAS |
| **PagoCompleto** | CUOTAS | Filas de CUOTAS con coincidencia exacta en SAT |

### Paso 6 — Limpieza

Antes de guardar los resultados se descartan las filas donde `numero_contrato` sea nulo. Esto elimina registros del SAT que carecen de identificador de contrato y que de otro modo inflarían los totales.

### Paso 7 — Escritura de archivos de salida

Para cada uno de los tres archivos de salida:
1. Se itera sobre los canales (aliados, oxxo, paynet).
2. Se escribe cada canal como una pestaña separada en el `.xlsx`.
3. Al final de cada pestaña se agrega una fila `TOTAL` con la suma de `interes` e `impuesto`.

### Paso 8 — Resumen en consola

Al finalizar se imprime en consola el total de `interés`, `impuesto` y su suma por canal y por archivo:

```
  PagosFaltantes<fecha>.xlsx
    aliados    interés: X,XXX.XX   impuesto: X,XXX.XX   total: X,XXX.XX
    oxxo       interés: X,XXX.XX   impuesto: X,XXX.XX   total: X,XXX.XX
    paynet     interés: X,XXX.XX   impuesto: X,XXX.XX   total: X,XXX.XX
  PagosDeMas<fecha>.xlsx
    ...
  PagoCompleto<fecha>.xlsx
    ...
```

---

## Estructura del script

```
reconciliacion_sat.py
├── Constantes
│   ├── MES              — mes de los archivos de entrada (hardcodeado)
│   ├── SHEET_PAIRS      — mapeo de hojas CUOTAS ↔ SAT ↔ etiqueta de canal
│   ├── CUOTAS_COLS      — columnas a leer de CUOTAS
│   ├── SAT_COLS         — columnas a leer del SAT
│   ├── KEY_COLS         — clave compuesta de comparación
│   └── DECIMAL_PLACES   — precisión de redondeo numérico (8)
│
├── Funciones
│   ├── load_cuotas_sheet()   — carga hoja de CUOTAS
│   ├── load_sat_sheet()      — carga hoja SAT y normaliza nombres de columnas
│   ├── _prepare()            — agrega columna _seq para match 1-a-1
│   ├── find_discrepancies()  — retorna filas de left sin match en right
│   ├── find_matches()        — retorna filas de left con match en right
│   └── write_output_xlsx()   — escribe xlsx con pestañas y fila TOTAL
│
└── main()
    ├── Parseo de argumentos (--dir)
    ├── Validación de archivos de entrada
    ├── Loop por canal → carga, comparación, clasificación
    ├── Escritura de los 3 archivos de salida
    └── Impresión del resumen en consola
```

---

## Notas técnicas

- **Hojas adicionales ignoradas:** Ambos archivos contienen más pestañas que las procesadas. El script solo opera sobre las 3 hojas definidas en `SHEET_PAIRS`.
- **Mismo dataset base:** Las tres hojas de CUOTAS tienen ~118,000 filas totales cada una; el filtro por `FACT`/`FACTU` selecciona únicamente las cuotas facturadas de cada canal.
- **Diferencias de precisión entre sistemas:** Los valores de interés en CUOTAS (ej. `152.54`) y en el SAT (ej. `152.50862069...`) provienen de cálculos con diferente precisión. El redondeo a 8 decimales mantiene mayor fidelidad que el redondeo a 2 para respetar la intención original de los datos.