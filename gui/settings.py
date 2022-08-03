from functools import partial
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QTabWidget, QVBoxLayout, QHBoxLayout,  QFormLayout, QLabel, QLineEdit, \
    QPushButton, QFileDialog, QComboBox, QCheckBox, QGroupBox, QTabBar
from PyQt5.QtGui import QIcon, QMouseEvent

import config
import core.contacts
import core.utils


class TabNetwork(QTabBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        tor_portable_label = QLabel('Tor portable')
        tor_portable_layout = QFormLayout()
        tor_portable_address = QLineEdit(config.ini['tor_portable']['address'])
        tor_portable_layout.addRow('Tor address:', tor_portable_address)
        tor_portable_socks_port = QLineEdit(str(config.ini['tor_portable']['socks_port']))
        tor_portable_layout.addRow('Tor SOCKS port:', tor_portable_socks_port)
        tor_portable_control_port = QLineEdit(str(config.ini['tor_portable']['control_port']))
        tor_portable_layout.addRow('Tor control port:', tor_portable_control_port)
        self.layout.addWidget(tor_portable_label)
        self.layout.addLayout(tor_portable_layout)

        tor_label = QLabel('Tor')
        tor_layout = QFormLayout()
        tor_address = QLineEdit(config.ini['tor']['address'])
        tor_layout.addRow('Tor address:', tor_address)
        tor_socks_port = QLineEdit(str(config.ini['tor']['socks_port']))
        tor_layout.addRow('Tor SOCKS port:', tor_socks_port)
        tor_control_port = QLineEdit(str(config.ini['tor']['control_port']))
        tor_layout.addRow('Tor control port:', tor_control_port)
        self.layout.addWidget(tor_label)
        self.layout.addLayout(tor_layout)

        client_label = QLabel('Client')
        client_layout = QFormLayout()
        client_hostname = QLineEdit(core.contacts.shorten_hostname(config.ini['client']['hostname']))
        client_hostname.setReadOnly(True)
        client_layout.addRow('Hostname:', client_hostname)
        client_listen_interface = QLineEdit(config.ini['client']['listen_interface'])
        client_layout.addRow('Listen interface:', client_listen_interface)
        client_listen_port = QLineEdit(str(config.ini['client']['listen_port']))
        client_layout.addRow('Listen port:', client_listen_port)
        self.layout.addWidget(client_label)
        self.layout.addLayout(client_layout)

        self.setLayout(self.layout)


class TabInterface(QTabBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        gui_layout = QFormLayout()
        gui_language = QComboBox()
        gui_language.addItems(['de', 'fr', 'en', 'pt', 'ru'])
        gui_language.setCurrentText(config.ini['gui']['language'])
        gui_layout.addRow('GUI language:', gui_language)

        gui_open_main_window_hidden = QCheckBox('Open main window hidden')
        gui_open_main_window_hidden.setChecked(config.ini['gui']['open_main_window_hidden'])
        gui_layout.addWidget(gui_open_main_window_hidden)
        gui_open_chat_window_hidden = QCheckBox('Open chat window hidden')
        gui_open_chat_window_hidden.setChecked(config.ini['gui']['open_chat_window_hidden'])
        gui_layout.addWidget(gui_open_chat_window_hidden)
        gui_notification_popup = QCheckBox('Notification popup')
        gui_notification_popup.setChecked(config.ini['gui']['notification_popup'])
        gui_layout.addWidget(gui_notification_popup)
        gui_notification_method = QComboBox()
        gui_notification_method.addItems(['generic', 'other'])
        gui_notification_method.setCurrentText(config.ini['gui']['notification_method'])
        gui_layout.addRow('Notification method:', gui_notification_method)
        gui_flash_window = QCheckBox('GUI flash window')
        gui_flash_window.setChecked(config.ini['gui']['notification_flash_window'])
        gui_layout.addWidget(gui_flash_window)

        self.layout.addLayout(gui_layout)

        self.setLayout(self.layout)


class TabMiscellaneous(QTabBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout()

        temp_data_dir_checkbox = QCheckBox('Temp files in data dir')
        temp_data_dir_checkbox.setChecked(config.ini['files']['temp_files_data_dir'])
        self.layout.addWidget(temp_data_dir_checkbox)

        temp_dir_input = QLineEdit()
        temp_dir_input.setReadOnly(True)
        temp_dir_input.mousePressEvent = partial(self.temp_dir_input_pressed, temp_dir_input)

        temp_dir_button = QPushButton('Set temp files custom dir')
        temp_dir_button.pressed.connect(
            partial(self.get_temp_custom_dir, temp_dir_input)
        )

        temp_dir_group_box = QGroupBox('Choose custom temp file directory:')
        # Set group box border, set title position and fix it's padding
        # (so it is in the center of the frame both horizontally and vertically)
        temp_dir_group_box.setStyleSheet('QGroupBox {border: 1px solid black; margin-top: 0.6em;}'
                                         'QGroupBox::title {subcontrol-position: top center; padding-top: -1em}')
        temp_dir_group_box.mousePressEvent = partial(
            self.temp_dir_input_pressed, temp_dir_input
        )

        temp_dir_layout = QHBoxLayout()
        temp_dir_group_box.setLayout(temp_dir_layout)
        temp_dir_layout.addWidget(temp_dir_input)
        temp_dir_layout.addWidget(temp_dir_button)
        self.layout.addWidget(temp_dir_group_box)

        self.setLayout(self.layout)

    def temp_dir_input_pressed(self, line_edit: QLineEdit, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.get_temp_custom_dir(line_edit)

    def get_temp_custom_dir(self, line_edit: QLineEdit):
        file_dialog = QFileDialog()
        result = file_dialog.getExistingDirectory(self, caption='Title')
        print(result)
        if result is not None:
            line_edit.setText(core.utils.get_relative_path(result))


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Window |
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowTitleHint)
        self.setFixedSize(config.Gui.settings_dialog_size)
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon(config.Gui.ICON_SETTINGS))
        self.layout = QVBoxLayout()

        self.tab_widget = QTabWidget(self)
        self.tab_network = TabNetwork(self)
        self.tab_widget.addTab(self.tab_network, 'Network')

        self.tab_interface = TabInterface(self)
        self.tab_widget.addTab(self.tab_interface, 'Interface')

        self.tab_miscellaneous = TabMiscellaneous(self)
        self.tab_widget.addTab(self.tab_miscellaneous, 'Miscellaneous')
        self.layout.addWidget(self.tab_widget)

        self.setLayout(self.layout)
        self.exec()
