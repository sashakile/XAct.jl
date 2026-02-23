# Architecture

sxAct has three main layers:

## Oracle

The oracle is a Dockerized Wolfram Engine running xAct. The `sxact.oracle` module provides an HTTP client to send tensor expressions and receive xAct-normalized results.

```
Docker container
└── Wolfram Engine 14.3.0
    └── xAct 1.2.0
        ├── xTensor
        ├── xCoba
        └── xPert
```

## Normalize

Raw xAct output is not always in a canonical form — index names may vary, terms may be reordered. The `sxact.normalize` pipeline canonicalizes expressions so they can be reliably compared.

## Compare

The `sxact.compare` module provides:

- **Comparator**: asserts that two expressions are equivalent after normalization
- **Sampling**: generates diverse test expressions to stress-test implementations

## Data Flow

```
User expression
    → OracleClient.evaluate()
    → OracleResult (raw xAct output)
    → normalize.pipeline()
    → canonical string
    → compare.comparator()
    → pass / fail
```
