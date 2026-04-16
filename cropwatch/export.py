"""Export crop progress data to CSV or JSON formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any


class ExportError(Exception):
    pass


SUPPORTED_FORMATS = ("csv", "json")


def export_data(records: list[dict[str, Any]], fmt: str) -> str:
    """Serialize *records* to the requested format string.

    Args:
        records: List of crop-progress dicts as returned by UsdaClient.
        fmt: One of ``'csv'`` or ``'json'``.

    Returns:
        A string in the requested format.

    Raises:
        ExportError: If *fmt* is unsupported or *records* is empty.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    if not records:
        raise ExportError("No data to export.")

    if fmt == "json":
        return json.dumps(records, indent=2)

    # CSV
    buf = io.StringIO()
    fieldnames = list(records[0].keys())
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue()


def write_export(records: list[dict[str, Any]], fmt: str, path: str) -> None:
    """Export *records* to a file at *path*."""
    content = export_data(records, fmt)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
