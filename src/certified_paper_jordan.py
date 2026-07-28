"""Safe certification boundary for the valid-input paper Jordan sorter."""

from oracle import oracle
from paper_execution_policy import CHECKED_MODE
from paper_jordan_sort import paper_jordan_sort_valid


def certified_paper_jordan_sort(seq, execution_mode=CHECKED_MODE):
    """Certify ``seq`` with the oracle, then run the valid-input paper sorter.

    This wrapper is intended for safe public use. Experiments that measure the
    pure paper sorter must certify the exact case before timing and then call
    ``paper_jordan_sort_valid`` directly inside the timed region.
    """
    values = list(seq)
    oracle_result = oracle(values)
    if not oracle_result["valid"]:
        raise ValueError(
            "paper Jordan sorting requires an oracle-certified valid input: "
            f"{oracle_result['reason']}"
        )
    return paper_jordan_sort_valid(values, execution_mode=execution_mode)
