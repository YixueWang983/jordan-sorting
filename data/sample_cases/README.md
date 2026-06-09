# Sample Test Cases

This directory contains small JSON test cases generated from the current Week 1 generators.

Each JSON file stores:

- `id`: stable test-case identifier
- `n`: sequence length
- `family`: generator family
- `seed`: random seed, or `null` for deterministic generators
- `sequence`: generated Jordan sequence candidate
- `oracle`: oracle certification result

These files are small examples for checking the data format. Larger experimental datasets can be generated later.

`random_permutation` is a neutral random family: cases may be valid or invalid depending on the oracle result.

`random_invalid` is filtered by the oracle and only stores cases certified as invalid.

`mutation_based_invalid` starts from a valid base sequence, applies swap mutations, and stores only cases certified invalid by the oracle.
