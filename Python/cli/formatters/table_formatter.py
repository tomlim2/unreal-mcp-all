"""Table formatter for CLI output"""
from typing import List, Dict, Any
from tabulate import tabulate


def format_as_table(data: List[Dict[str, Any]], headers: List[str] = None) -> str:
    """
    Format data as a table.

    Args:
        data: List of dictionaries to format
        headers: Optional list of column headers (uses dict keys if None)

    Returns:
        Formatted table string
    """
    if not data:
        return "No data to display"

    if headers is None:
        headers = list(data[0].keys())

    # Extract rows
    rows = []
    for item in data:
        row = [item.get(h, "") for h in headers]
        rows.append(row)

    return tabulate(rows, headers=headers, tablefmt="grid")


def format_preview_table(preview: List[Dict[str, Any]]) -> str:
    """
    Format asset rename preview as a table.

    Args:
        preview: List of preview dictionaries

    Returns:
        Formatted table string
    """
    if not preview:
        return "No assets to preview"

    # Separate assets that need renaming from those that don't
    to_rename = [p for p in preview if p.get("needs_rename")]
    already_correct = [p for p in preview if not p.get("needs_rename")]

    output = []

    if to_rename:
        output.append("Assets to Rename:")
        headers = ["Asset Type", "Old Name", "New Name"]
        rows = [[p["asset_type"], p["old_name"], p["new_name"]] for p in to_rename]
        output.append(tabulate(rows, headers=headers, tablefmt="grid"))
        output.append("")

    if already_correct:
        output.append("Assets Already Correct (No Change):")
        for p in already_correct:
            output.append(f"  • {p['old_name']} ({p['asset_type']})")
        output.append("")

    output.append(f"Total: {len(to_rename)} to rename, {len(already_correct)} unchanged")

    return "\n".join(output)
