import traceback
import zipfile

from openpyxl.utils.exceptions import InvalidFileException
from pypdf.errors import PyPdfError


def friendly_message(exc: BaseException) -> tuple[str, bool]:
    """
    Turn an exception into text for the user.
    Returns (message, expected) where expected=False means "this is a bug or something we didn't anticipate".
    """
    if isinstance(exc, ValueError):
        return str(exc), True
    if isinstance(exc, FileNotFoundError):
        return f"File or folder not found: {exc.filename or exc}. Has it been moved or deleted?", True
    if isinstance(exc, PermissionError):
        return (
            f"Permission denied for '{exc.filename or 'a file'}'. "
            f"If it is open in Excel or another program, close it and try again."
        ), True
    if isinstance(exc, (zipfile.BadZipFile, InvalidFileException)):
        return "That file is not a valid Excel (.xlsx) file. Check you selected the right file.", True
    if isinstance(exc, PyPdfError):
        return "That file is not a valid PDF (or is damaged). Check you selected the right file.", True
    return f"{type(exc).__name__}: {exc}", False


def report_error(exc: BaseException, error_callback) -> None:
    """
    Show an error via error_callback(message, color). Unexpected errors include the full traceback.
    """
    message, expected = friendly_message(exc)
    text = f"❌ ERROR: {message}"
    if not expected:
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).rstrip()
        text += f"\n(This was unexpected. Technical details:)\n{details}"
    error_callback(text, "red")
