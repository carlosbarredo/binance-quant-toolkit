# Order-book reconstruction

An order book is state plus an ordered event stream. A depth snapshot alone is
stale immediately. Deltas alone have no starting state.

## Safe USD-M sequence

1. Open the diff-depth WebSocket and buffer events.
2. Fetch a REST depth snapshot.
3. Record its `lastUpdateId`.
4. Drop buffered events whose final ID `u` is older than that ID.
5. The first accepted event must satisfy `U <= lastUpdateId <= u`.
6. Apply bid and ask changes. Quantity zero deletes a level.
7. For every later event, require `pu` to equal the previous `u`.
8. Restart from step one after any sequence gap or reconnect.

`LocalOrderBook` implements these state checks. The recorder deliberately stores
raw messages. Reconstruction should happen in a separate, testable step.

## Book features

For best bid `b`, best ask `a`, bid size `q_b` and ask size `q_a`:

```text
mid = (a + b) / 2
spread = a - b
relative spread = (a - b) / mid
microprice = (a*q_b + b*q_a) / (q_a + q_b)
top imbalance = (q_b - q_a) / (q_b + q_a)
```

These are descriptors. They are not executable prices. Displayed liquidity can
cancel before an order arrives. Queue position is not known from level-two data.

## What to store

Keep the raw message, exchange event time, transaction time, update IDs and local
receipt time. Keep reconnection boundaries. Keep the snapshot used to bootstrap
each segment. Without these fields, sequence audits are much harder.

