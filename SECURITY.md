# Security policy

## Scope

This project reads public market data. It does not need an API key. Do not place
credentials in examples, issues, notebooks, metadata or test fixtures.

Report a vulnerability through GitHub's private vulnerability reporting feature
for this repository. Do not publish an exploit before a fix is available.

## Data safety

- Archive filenames and symbols are validated before URL construction.
- ZIP extraction removes archive path components.
- WebSocket names are restricted to documented public stream patterns.
- Captures must have a message or time bound.
- REST hosts are fixed in code. User input cannot select an arbitrary host.

These controls reduce risk. They do not make third-party data trustworthy.
Validate downloaded content and keep the package updated.

