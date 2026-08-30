# Inicio rápido

Este recorrido empieza sin conexión. Después añade una fuente cada vez.

## 1. Instala

```bash
python -m venv .venv
python -m pip install -e .
```

Activa el entorno con el comando correspondiente a tu sistema operativo.

## 2. Explora el catálogo

```bash
bqt catalog
bqt catalog --market usdm
bqt catalog --transport websocket
```

El catálogo explica qué mide cada dataset. También muestra su principal límite.

## 3. Ejecuta la lección offline

```bash
bqt demo
```

El resultado esperado son doce velas horarias sin errores estructurales y unas
pocas estadísticas de cierre a cierre. Los precios incluidos son sintéticos.
Sirven para aprender. No forman un histórico de mercado.

## 4. Descarga velas

```bash
bqt klines BTCUSDT 1m \
  --market usdm \
  --start 2024-01-01T00:00:00Z \
  --end 2024-01-02T00:00:00Z \
  --output data/btcusdt_1m.csv
```

En USD-M puedes usar `--price-type mark`, `index` o `premium`.
Usa `--market spot` para velas spot basadas en trades.

## 5. Audita antes de modelar

```bash
bqt audit data/btcusdt_1m.csv --interval 1m --strict
```

El modo estricto falla ante huecos, duplicados, OHLC incoherente, volumen o
trades negativos y timestamps desordenados.

## 6. Añade contexto de derivados

```bash
bqt funding BTCUSDT \
  --start 2024-01-01 \
  --end 2024-02-01 \
  --output data/btcusdt_funding.csv

bqt stats open_interest_history BTCUSDT 5m \
  --output data/btcusdt_open_interest.csv
```

Los endpoints estadísticos tienen poca retención. Usa archivos cuando exista
cobertura para ese dataset y fecha.

## 7. Planifica un histórico grande

```bash
bqt archive-plan klines BTCUSDT \
  --market um \
  --interval 1m \
  --frequency monthly \
  --start 2023-01-01 \
  --end 2024-01-01
```

La planificación enseña todos los objetos esperados. No descarga nada.

```bash
bqt archive-download klines BTCUSDT \
  --market um \
  --interval 1m \
  --frequency monthly \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --output-dir data/archives
```

El checksum se verifica por defecto. Los objetos ausentes se muestran y omiten.
Usa `--fail-missing` si necesitas cobertura completa.

## 8. Captura microestructura en vivo

```bash
python -m pip install -e .[stream]
bqt stream \
  --market usdm \
  --streams btcusdt@aggTrade btcusdt@bookTicker btcusdt@depth@100ms \
  --seconds 60 \
  --output data/btcusdt_live.ndjson
```

También puedes limitar por mensajes. La captura nunca es ilimitada por defecto.
El crecimiento del disco debe ser una decisión consciente.

## Siguiente paso

- Lee [Cómo elegir datos](CHOOSING_DATA_ES.md).
- Lee [Reconstrucción del order book](ORDER_BOOK_ES.md) antes de usar deltas.
- Lee [Metodología](METHODOLOGY_ES.md) antes de unir datos o hacer backtests.
- Usa las [recetas de investigación](RECIPES_ES.md) como punto de partida.

