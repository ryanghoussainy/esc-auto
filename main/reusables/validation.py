import pandas as pd


def require_columns(df: pd.DataFrame, columns: list[str], context: str) -> None:
    """
    Raise a readable error if any of the expected columns are missing from a table.
    `context` says where the table came from, e.g. "the finals sheet (event 25m Free)".
    """
    missing = [c for c in columns if c not in df.columns]
    if missing:
        found = ", ".join(str(c) for c in df.columns)
        raise ValueError(f"Missing column(s) {', '.join(repr(c) for c in missing)} in {context}. Columns found: {found}")


def check_event_counts(excel_count: int, pdf_count: int, excel_desc: str, pdf_desc: str) -> None:
    """
    The Excel tables and PDF tables are matched up by position, so the PDF must have
    at least as many events as the Excel file. Otherwise we would fail later with an
    unhelpful 'list index out of range'.
    """
    if pdf_count < excel_count:
        raise ValueError(
            f"{excel_desc} has {excel_count} events but {pdf_desc} only has {pdf_count}. "
            f"Check that you selected the right files (and that the PDF is complete)."
        )
