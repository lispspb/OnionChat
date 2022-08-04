import os.path
from signal import SIGTERM
from base64 import b32decode
import hashlib
import binascii

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
