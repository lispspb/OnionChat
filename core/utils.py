import os.path
from signal import SIGTERM
from base64 import b32decode
import hashlib
import binascii
import shutil
import ctypes

from config import *


global cached_data_dir


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


def terminate_process(pid: int) -> bool:
    """Sends SIGTERM to a process.

    :param: pid
    :type: int

    :return: Whether a process was successfully terminated.
    :rtype: bool
    """
    try:
        os.kill(pid, SIGTERM)
        return True
    except PermissionError:
        # Should never happen
        print(f'Could not terminate process {pid}: not enough permission.')
        return False
    except OSError as err:
        print(f'Could not terminate process {pid}: {err}.')
        return False


def is_valid_address(v3_address) -> bool:
    """
    Checks if a received address is a correct v3 onion address.

    V3 Onion address consists of 56 base32 chars, e.g.
    pzhdfe7jraknpj2qgu5cz2u3i4deuyfwmonvzu5i3nyw4t4bmg7o5pad
    We measure address length, try to decode it, check onion version
    in address, calculate checksum and compare it with the one
    that is in the address.
    See Tor rend-spec-v3.txt for details of implementation.

    :return: Whether onion v3 address is correct
    :rtype: bool
    """
    if not len(v3_address) == 56:
        print(f'Incorrect address length: {v3_address}')
        return False

    try:
        # onion_address = base32(PUBKEY | CHECKSUM | VERSION) + ".onion"
        address_decoded = b32decode(v3_address)
    except binascii.Error:
        # Incorrect padding or chars that are not from b32 alphabet
        print(f'Could not decode onion address: {v3_address}')
        return False

    version = address_decoded[-1]
    # If not a V3 onion
    if not version == 3:
        print(f'Incorrect onion version number in address: {v3_address}')
        return False

    pubkey = address_decoded[:-3]  # Truncate two checksum bytes and one version byte
    # Specs don't specify hash function (it's sha3-256)
    # CHECKSUM = sha3_256(".onion checksum" | PUBKEY | VERSION)[:2]
    checksum_bytes = '.onion checksum'.encode('utf-8') + pubkey + version.to_bytes(1, byteorder='little')
    checksum = hashlib.sha3_256(checksum_bytes).digest()[:2]
    if not checksum == address_decoded[-3:-1]:
        print(f'Incorrect onion checksum in address: {v3_address}')
        return False
    return True


def get_data_dir():
    global cached_data_dir

    if is_portable():
        return SCRIPT_DIR

    if cached_data_dir:
        return cached_data_dir

    if is_windows():
        CSIDL_APPDATA = 0x001a
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.shell32.SHGetSpecialFolderPathW(None, buf, CSIDL_APPDATA, 0)
        appdata = buf.value
        data_dir = os.path.join(appdata, 'onionchat')
    else:
        home = os.path.expanduser('~')
        data_dir = os.path.join(home, '.onionchat')

    # test for optional profile name in command line
    try:
        data_dir += '_' + sys.argv[1]
    except IndexError:
        pass

    # create it if necessary
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    # and create the folder 'Tor' with tor.exe and torrc.txt in it if necessary
    data_dir_tor = os.path.join(data_dir, 'Tor')
    if is_windows():
        tor_exe = 'tor.exe'
    else:
        tor_exe = 'tor.sh'
    if not os.path.exists(data_dir_tor):
        os.mkdir(data_dir_tor)
        shutil.copy(os.path.join('Tor', tor_exe), data_dir_tor)
        shutil.copy(os.path.join('Tor', 'torrc.txt'), data_dir_tor)

    # fix permissions
    for filename in os.listdir(data_dir):
        if os.path.isfile(filename):
            # old log files still lying around in the data folder
            os.chmod(os.path.join(data_dir, filename), 0o600)
    os.chmod(data_dir, 0o700)
    os.chmod(data_dir_tor, 0o700)
    os.chmod(os.path.join(data_dir_tor, tor_exe), 0o700)
    os.chmod(os.path.join(data_dir_tor, 'torrc.txt'), 0o600)

    cached_data_dir = data_dir
    return data_dir


def split_line(line) -> tuple[str, str]:
    """Split a line of text.

    Splits a given line on the first space character and returns
    two strings, the first word and the remaining string. This is
    used for parsing the incoming messages from left to right since
    the command and its arguments are all delimited by spaces and
    the command may not contain spaces.

    :param: Line.
    :type: bool
    :return: Tuple of two strings: first word of a line and the remaining string.
    :rtype: tuple[str, str]
    """
    line = line.split(' ')
    try:
        a = line[0]
        b = ' '.join(line[1:])
    except IndexError:
        a = line
        b = ''
    return a, b
