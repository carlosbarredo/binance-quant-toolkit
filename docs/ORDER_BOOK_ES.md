# Reconstrucción del order book

Un order book combina estado y eventos ordenados. Un snapshot queda obsoleto al
instante. Los deltas no sirven sin estado inicial.

## Secuencia segura para USD-M

1. Abre el WebSocket de profundidad y acumula eventos.
2. Descarga un snapshot REST.
3. Guarda su `lastUpdateId`.
4. Descarta eventos cuyo ID final `u` sea anterior.
5. El primer evento aceptado debe cumplir `U <= lastUpdateId <= u`.
6. Aplica cambios. Una cantidad cero elimina el nivel.
7. En cada evento posterior, exige que `pu` coincida con el `u` anterior.
8. Reinicia el proceso tras un hueco o una reconexión.

`LocalOrderBook` implementa estos controles. El grabador conserva mensajes
crudos. La reconstrucción se hace después, en un paso separado y comprobable.

## Variables básicas

Con mejor bid `b`, mejor ask `a` y cantidades `q_b`, `q_a`:

```text
mid = (a + b) / 2
spread = a - b
spread relativo = (a - b) / mid
microprice = (a*q_b + b*q_a) / (q_a + q_b)
imbalance = (q_b - q_a) / (q_b + q_a)
```

Son descriptores. No son precios ejecutables. La liquidez puede cancelarse. La
posición en cola no se conoce con datos de nivel dos.

