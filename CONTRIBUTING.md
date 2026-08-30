# Contributing

Small, reviewable changes are easiest to validate.

1. Open an issue that names the dataset, market and transport.
2. State the exchange field semantics and retention assumptions.
3. Add network-free tests with representative payloads.
4. Keep raw field names at the boundary. Normalise in one place.
5. Update `DATA.md` when a schema or source changes.
6. Run `pytest` and `ruff check .`.

Do not add authenticated trading endpoints, secrets, profit claims or hidden
network calls to tests. New live collectors must be bounded by time, message
count, file size or an equally explicit limit.

