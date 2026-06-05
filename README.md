# Jordan Sorting

Implementation and experimental evaluation of the simplified Jordan-sorting framework.

This project is part of a master's thesis preparation. The current milestone is to build:

- a correctness oracle,
- controlled test-instance generators,
- sorting baselines,
- and later a reference implementation of the simplified 1990 Jordan-sorting framework.

## Current Focus

The first milestone is not the full Jordan-sorting algorithm. The first milestone is:

1. define upper and lower pairs,
2. implement laminarity checks,
3. build an oracle based on standard sorting,
4. generate valid and invalid test instances,
5. prepare baseline sorting algorithms.

## Project Structure

```text
src/
  oracle.py
  generators.py
  baselines.py
  stats.py

tests/
  test_oracle.py
  test_generators.py

docs/
  oracle_and_test_generation.md
  notes.md

experiments/
  run_small_tests.py
```

## Current Status

The repository currently contains:

- a first correctness oracle for upper/lower laminarity checks,
- small valid and invalid test-instance generators,
- unit tests for the oracle and generators,
- and a design note for oracle and test generation.

## Running Tests

The current test suite uses Python's built-in `unittest` module:

```bash
python -m unittest discover -s tests
```
