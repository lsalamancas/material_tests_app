# Material Testing Analyzer

Aplicación de escritorio para análisis y visualización de ensayos mecánicos de materiales:
- **Tracción** — curva esfuerzo-deformación, módulo de Young, resistencia máxima, límite elástico
- **Flexión** — comparativa de especímenes, módulo de flexión
- **Impacto** — energía absorbida, tenacidad, estadísticas (ASTM D256)

## Requisitos

- Python 3.10+
- Dependencias listadas en `requirements.txt`

## Instalación

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar entorno
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
# Con el entorno activado
python -m app.main
```

## Formatos de archivo soportados

| Ensayo   | Formato esperado                              |
|----------|-----------------------------------------------|
| Tensión  | `.xlsx` con series temporales por espécimen   |
| Flexión  | `.xlsx` con resultados resumen por espécimen  |
| Impacto  | `.xlsx` con energía y tenacidad por espécimen |

También se pueden cargar archivos `.csv` y `.txt` con columnas separadas por comas o tabulaciones.

## Propiedades calculadas

### Tracción
- Módulo de Young (E) — regresión lineal en región elástica
- Límite elástico (σy) — método del 0.2% de deformación compensada
- Resistencia máxima (UTS)
- Deformación de rotura
- Tenacidad (área bajo la curva)

### Flexión (3 puntos)
- Resistencia máxima a flexión
- Módulo de flexión
- Deformación máxima

### Impacto (ASTM D256 — Charpy/Izod)
- Energía de impacto (J)
- Tenacidad al impacto (J/mm²)
- Estadísticas: mínimo, máximo, media, desviación estándar

## Estructura del proyecto

```
src/
└── app/
    ├── main.py          # Punto de entrada
    ├── ui/              # Widgets de interfaz gráfica
    ├── parsers/         # Lectura y normalización de archivos
    └── analysis/        # Cálculo de propiedades mecánicas
```
