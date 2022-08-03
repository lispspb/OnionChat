import pathlib
import os.path
import sys
import json
from PyQt5.QtCore import QSize


STATUS_OFFLINE = 0
STATUS_HANDSHAKE = 1
STATUS_ONLINE = 2
STATUS_AWAY = 3
STATUS_XA = 4
STATUS_ALL = 5


SCRIPT_DIR = pathlib.Path(sys.argv[0]).parent.resolve()


global ini
ini: dict = {}

config_defaults = {
    'tor': {
        'address': '127.0.0.1',
        'socks_port': 9050,
        'control_port': 9051,
    },
    'tor_portable': {
        'address': '127.0.0.1',
        'socks_port': 11109,
        'control_port': 11119,
    },
    'client': {
        'hostname': 'm' * 56,
        'listen_interface': '127.0.0.1',
        'listen_port': 11009,
    },
    'logging': {
        'log_file': '',
        'log_level': 0,
    },
    'files': {
        'temp_files_data_dir': True,
        'temp_files_custom_dir': '',
    },
    'gui': {
        'language': 'en',
        'open_main_window_hidden': False,
        'open_chat_window_hidden': False,
        'notification_popup': True,
        'notification_method': 'generic',
        'notification_flash_window': True,

        'time_stamp_format': '(%H:%M:%S)',
        'color_time_stamp': '#808080',
        'color_nick_myself': '#0000c0',
        'color_nick_buddy': '#c00000',
        'color_text_background': '#ffffff',
        'color_text_foreground': '#000000',
        'color_text_use_system_colors': True,
        'chat_font_name': 'Arial',
        'chat_font_size': 10,
        'chat_window_width': 400,
        'chat_window_height': 400,
        'chat_window_height_lower': 50,
        'main_window_width': 260,
        'main_window_height': 350,
    },
    'profile': {
        'name': '',
        'text': '',
    }
}


def write_default_json(filename: str = 'onionchat.json.ini') -> bool:
    try:
        ini_file = open(filename, 'w')
        ini_file.write(json.dumps(config_defaults, indent=4))
        ini_file.close()
    except IOError as err:
        print(f'Could not write default ini to {filename}: {err}')
        return False
    print(f"Successfully written JSON ini to '{filename}'")
    return True


def load_from_json(filename: str = 'onionchat.json.ini') -> bool:
    global ini
    try:
        ini_file = open(filename, 'r')
        config_json = json.loads(ini_file.read())
        ini_file.close()
    except FileNotFoundError:
        print(f"Could not find JSON ini file '{filename}'.")
        print('Loading ini defaults.')
        ini = config_defaults
        print(f"Saving JSON ini defaults to '{filename}' so we could use it next time.")
        write_default_json()
        return False
    except IOError as err:
        print(f"Could not read JSON ini from '{filename}': {err}")
        print(f'Loading ini defaults.')
        ini = config_defaults
        return False
    except json.JSONDecodeError as err:
        print(f"Could not decode ini JSON from '{filename}': {err}")
        print(f'Loading ini defaults.')
        ini = config_defaults
        return False
    print(f"Successfully read JSON ini from '{filename}'. Now parsing...")

    sections = config_defaults.keys()
    # Check section existence
    # Load the entire section from config_defaults if not found
    for section in sections:
        config_json.get(section)
        section_json = config_json.get(section)
        if section_json is None:
            print(f"Could not find section '{section}' in JSON ini '{filename}'.")
            print('Loading section from ini defaults.')
            ini[section] = config_defaults[section]
            continue

        # Section: check each of its keys to exist
        # Load key from config_defaults if not found
        for key in config_defaults[section].keys():
            key_json = section_json.get(key)
            if key_json is None:
                print(f"Could not find '{key}', section '{section}' in JSON ini '{filename}'.")
                print('Loading value from ini defaults.')
        ini[section] = config_defaults[section]

    return True


class App:
    NAME = 'OnionChat'
    VERSION_MAJOR = 0
    VERSION_MINOR = 1
    VERSION_PATCH = 0
    VERSION_STABLE = False
    VERSION = f'{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{"stable" if VERSION_STABLE else "unstable"}'
    TITLE = f'{NAME} {VERSION}'
    DATA_DIR = pathlib.Path('data')
    BACKGROUND_DIR = pathlib.Path(DATA_DIR, 'background')
    HELP_DIR = pathlib.Path(DATA_DIR, 'help')
    ICON_DIR = pathlib.Path(DATA_DIR, 'icon')
    PROFILE_DIR = pathlib.Path('profile')


class Login:
    pass


class Gui:
    WINDOW_MIN_SIZE = QSize(690, 500)
    TOOLBAR_MAX_WIDTH = 420
    CHAT_LIST_MAX_WIDTH = TOOLBAR_MAX_WIDTH
    MESSAGE_LIST_MIN_WIDTH = 540

    BACKGROUND_MESSAGE_LIST = os.path.join(App.BACKGROUND_DIR, 'message_list.png')
    BACKGROUND_CHAT_LIST = os.path.join(App.BACKGROUND_DIR, 'chat_list.png')

    ICON_APP = os.path.join(App.ICON_DIR, 'app.png')
    ICON_SETTINGS = os.path.join(App.ICON_DIR, 'settings.png')

    statusbar_welcome_msec = 3000
    statusbar_icon_size = QSize(20, 20)

    chat_list_update_ms = 100

    settings_dialog_size = QSize(320, 400)

    about_dialog_size = QSize(200, 300)

    donate_dialog_size = QSize(450, 300)
    donate_icon_size = QSize(20, 20)
    donate_address_copied_msec = 2000
