# Metodología de investigación

El descargador resuelve la adquisición. No resuelve el diseño del estudio.

## Pipeline defendible

1. Escribe la hipótesis antes de mirar el holdout.
2. Define mercado, universo, contrato y familia de precio.
3. Fija el reloj del evento y el primer instante observable.
4. Conserva los datos crudos, checksums y metadatos.
5. Audita huecos, duplicados, cambios de esquema y valores imposibles.
6. Construye variables solo con información pasada.
7. Modela fees, spread, slippage, funding, latencia y límites.
8. Divide el tiempo en orden. Entrena en el pasado. Evalúa en el futuro.
9. Comprueba estabilidad de parámetros, universo y régimen.
10. Publica también fallos y resultados negativos.

## Unir fuentes

Prefiere uniones as-of hacia atrás. Una fila solo puede usar un dato disponible
antes de decidir. Limita la antigüedad máxima. No rellenes hacia delante durante
un corte sin explicar. Conserva el timestamp original tras cada unión.

## Backtests con velas

Una vela no dice si ocurrió primero el máximo o el mínimo. Si toca stop y target,
el resultado depende del camino. Usa datos más finos, una regla conservadora o
marca el caso como ambiguo. No elijas el orden favorable después de verlo.

## Funding

Separa estimaciones anunciadas, tasas realizadas y flujo de caja. Un valor
publicado después no puede ser una variable anterior. Aplica funding solo si la
posición simulada era elegible en el instante correspondiente.

## Registro reproducible

Guarda revisión de código, parámetros, objetos de origen, checksum, fecha de
descarga, zona horaria, versiones y auditoría. Si el resultado no puede
reconstruirse, no debe convertirse en conclusión de estrategia.

