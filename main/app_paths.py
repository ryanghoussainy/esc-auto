import os
import platform


def get_app_data_dir() -> str:
    """Folder where we keep its settings (rates.json) and log file."""
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.expanduser("~"), "AppData", "Local", "ESCAuto")
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "ESCAuto")
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")
