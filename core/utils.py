import os.path
from signal import SIGTERM

from config import *


def get_relative_path(path: str | pathlib.Path) -> str:
    path = pathlib.Path(path).resolve()
    if path.is_relative_to(SCRIPT_DIR):
        return os.path.relpath(path, SCRIPT_DIR)
    return str(path)


def is_portable() -> bool:
    """Checks whether portable mode is enabled.

    If the file portable.txt exists in the same directory
    then we know that we are running in portable mode.

    :return: Whether the portable mode is enabled.
    :rtype: bool
    """
    if os.path.exists(os.path.join(SCRIPT_DIR, 'portable.txt')):
        return True
    return False


def is_windows() -> bool:
    """Checks if OnionChat runs on Windows.

    :return: Whether OnionChat runs on Windows platform.
    :rtype: bool
    """
    return sys.platform.startswith('win')


def kill_process(pid):
    try:
        os.kill(pid, SIGTERM)
    except Exception:
        print(f'(1) could not kill process {pid}')
        tb()
