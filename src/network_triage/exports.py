"""Export utilities for Network Triage Tool results.

Provides functions to export scan results to various formats (JSON, CSV).
"""

import csv
import json
from pathlib import Path
from typing import Any

from .logging import get_logger

logger = get_logger(__name__)


def export_to_json(data: list[dict[str, Any]] | dict[str, Any], file_path: Path) -> bool:
    """Export data to a JSON file.

    Args:
        data: Data to export.
        file_path: Destination path.

    Returns:
        bool: True if successful, False otherwise.

    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        logger.info("Successfully exported to JSON", path=str(file_path))
        return True
    except Exception as e:
        logger.error("Failed to export to JSON", path=str(file_path), error=str(e))
        return False


def export_to_csv(data: list[dict[str, Any]], file_path: Path) -> bool:
    """Export a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries with consistent keys.
        file_path: Destination path.

    Returns:
        bool: True if successful, False otherwise.

    """
    if not data:
        logger.warning("No data provided for CSV export")
        return False

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        keys = data[0].keys()
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        logger.info("Successfully exported to CSV", path=str(file_path))
        return True
    except Exception as e:
        logger.error("Failed to export to CSV", path=str(file_path), error=str(e))
        return False
