import pathlib
import os.path
import sys
from PyQt5.QtCore import QSize


STATUS_OFFLINE = 0
STATUS_HANDSHAKE = 1
STATUS_ONLINE = 2
STATUS_AWAY = 3
STATUS_XA = 4
STATUS_ALL = 5


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
        'notification_popup': 1,
        'notification_method': 'generic',
        'notification_flash_window': 1,
        'open_main_window_hidden': 0,
        'open_chat_window_hidden': 0,
        'time_stamp_format': '(%H:%M:%S)',
        'color_time_stamp': '#808080',
        'color_nick_myself': '#0000c0',
        'color_nick_buddy': '#c00000',
        'color_text_background': '#ffffff',
        'color_text_foreground': '#000000',
        'color_text_use_system_colors': 1,
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

SCRIPT_DIR = pathlib.Path(sys.argv[0]).parent.resolve()


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
