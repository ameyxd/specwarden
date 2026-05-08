"""Example script that uses the logger module.

Calls the logging functions in various inconsistent ways.
"""
from logger import debug, info, warn, error, critical


def process_record(record_id: int) -> dict:
    debug(f"processing record {record_id}")

    if record_id < 0:
        error(f"record id must be non-negative, got {record_id}")
        return {}

    if record_id == 0:
        warn("record id is zero — this may be a sentinel value")

    info(f"record {record_id} processed successfully")
    return {"id": record_id, "status": "ok"}


def run_batch(records: list) -> list:
    info(f"starting batch of {len(records)} records")
    results = []

    for r in records:
        result = process_record(r)
        if result:
            results.append(result)
        else:
            warn(f"skipped record {r}")

    if not results:
        critical("batch produced no results")
    else:
        info(f"batch complete: {len(results)} successful")

    return results


if __name__ == "__main__":
    run_batch([1, 2, 0, -1, 3])
