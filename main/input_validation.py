"""
Pre-flight checks run at the start of each task, so problems with the selected files are reported
up front in plain language rather than as a confusing error halfway through.
All of these raise ValueError with a message written for the user.
"""
import os

EXCEL_EXTENSIONS = (".xlsx", ".xls", ".xlsm")
PDF_EXTENSIONS = (".pdf",)


def require_file(path, description: str, extensions: tuple[str, ...] | None = None) -> None:
    """Check that a selected input file exists, is a file, and has an expected extension."""
    if not path:
        raise ValueError(f"No {description} selected.")
    if not os.path.exists(path):
        raise ValueError(f"The {description} could not be found: '{path}'. Has it been moved or deleted?")
    if os.path.isdir(path):
        raise ValueError(f"The {description} is a folder, but a file was expected: '{path}'.")
    if extensions and os.path.splitext(path)[1].lower() not in extensions:
        raise ValueError(
            f"The {description} should be a {' / '.join(extensions)} file, "
            f"but '{os.path.basename(path)}' is not."
        )


def require_folder(path, description: str) -> None:
    if not path:
        raise ValueError(f"No {description} selected.")
    if not os.path.isdir(path):
        raise ValueError(f"The {description} could not be found: '{path}'. Has it been moved or deleted?")


def require_writable_output(path, description: str = "output file") -> None:
    """
    Check we'll be able to save the output, before doing the (possibly long, possibly interactive) work.
    Catches a missing/read-only folder and an existing file that is locked (e.g. open in Excel on Windows).
    """
    folder = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(folder):
        raise ValueError(f"The folder for the {description} does not exist: '{folder}'.")
    if not os.access(folder, os.W_OK):
        raise ValueError(f"Cannot save the {description} in '{folder}' because it is not writable. Choose another location.")
    if os.path.exists(path):
        try:
            with open(path, "r+b"):
                pass
        except OSError:
            raise ValueError(
                f"Cannot overwrite '{os.path.basename(path)}'. If it is open in Excel, close it and try again."
            )
