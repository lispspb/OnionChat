import os.path
from PyQt5.QtCore import Qt, QEvent, QPoint, QTimer
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QHBoxLayout, QRadioButton, \
    QButtonGroup, QVBoxLayout, QComboBox, QFrame, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QBrush, QPalette, QEnterEvent, QMouseEvent

import config
import core.contacts
import gui


global ignore_mouse_press_events, show_status, chat_list_changed
ignore_mouse_press_events: bool = False
show_group: int = 0  # Defaults to Everyone
show_status = config.STATUS_ALL
chat_list_changed: bool = True


class StatusSelectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()

        self.status = QButtonGroup()
        self.status_all = QRadioButton('All')
        self.status_all.setChecked(True)
        self.status_online = QRadioButton('Online')
        self.status_offline = QRadioButton('Offline')
        self.status_buttons = [self.status_all, self.status_online, self.status_offline]
        self.status.buttonToggled.connect(self.button_toggled)

        for button in self.status_buttons:
            self.status.addButton(button)
            self.layout.addWidget(button)

        self.setLayout(self.layout)

    def button_toggled(self, button: QRadioButton, checked: bool):
        if checked:
            global show_status, chat_list_changed
            chat_list_changed = True
            match button:
                case self.status_all:
                    show_status = config.STATUS_ALL
                case self.status_online:
                    show_status = config.STATUS_ONLINE
                case self.status_offline:
                    show_status = config.STATUS_OFFLINE


class GroupSelectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout()
        self.layout.setContentsMargins(6, 3, 0, 0)

        self.items = core.contacts.groups
        self.item_actions = {item: 'action' for item in self.items}

        self.select = QComboBox()
        self.select.addItems(self.items)
        self.select.setCurrentIndex(0)
        self.select.currentIndexChanged.connect(self.index_changed)
        self.layout.addWidget(self.select)

        self.setLayout(self.layout)

    @staticmethod
    def index_changed(index: int):
        global chat_list_changed, show_group
        chat_list_changed = True
        show_group = index


class ChatListItem(QFrame):
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.id = item['id']
        self.position = item['position']
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.setCursor(Qt.PointingHandCursor)

        icon = QLabel('')
        icon.setPixmap(item['icon'])
        self.layout.addWidget(icon)
        name = QLabel(item['name'])
        self.layout.addWidget(name)
        message = QLabel(item['message'])
        self.layout.addWidget(message)
        self.setLayout(self.layout)

        self.enterEvent = self.mouse_enter
        self.leaveEvent = self.mouse_leave
        self.mousePressEvent = self.mouse_pressed
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def mouse_enter(self, event: QEnterEvent):
        self.setStyleSheet('QFrame {background-color: rgba(255, 255, 255, 0.4);}'
                           'QLabel {background-color: rgba(255, 255, 255, 0);}')
        return QWidget.enterEvent(self, event)

    def mouse_leave(self, event: QEvent):
        self.setStyleSheet('QFrame {background-color: rgba(255, 255, 255, 0);}')
        return QWidget.leaveEvent(self, event)

    def mouse_pressed(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            global ignore_mouse_press_events
            if not ignore_mouse_press_events:
                print('left pressed')
            else:
                ignore_mouse_press_events = False
        elif event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())
        return QFrame.mousePressEvent(self, event)

    def show_context_menu(self, point: QPoint):
        context_menu = QMenu()
        profile = QAction('Open Profile')
        context_menu.addAction(profile)
        context_menu.addSeparator()
        dialog = QAction('New Dialog')
        context_menu.addAction(dialog)
        clear = QAction('Clear Dialog')
        context_menu.addAction(clear)
        context_menu.addSeparator()
        remove = QAction('Remove from Buddies')
        context_menu.addAction(remove)
        block = QAction('Remove and Block')
        context_menu.addAction(block)
        self.setCursor(Qt.ArrowCursor)
        action = context_menu.exec_(point)

        # After mouse clicked
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet('QFrame {background-color: rgba(255, 255, 255, 0);}')
        # Clicked outside
        if action is None:
            global ignore_mouse_press_events
            ignore_mouse_press_events = True


class ChatListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.widgets = []
        self.ids = []
        global show_group, show_status
        self.show_group = show_group
        self.show_status = show_status

        self.setLayout(self.layout)

    def insert(self, position, widget):
        # Found - show hidden widget
        try:
            widget_index = self.widgets.index(widget)
            self.widgets[widget_index].setVisible(True)
        # Not found - add widget
        except ValueError:
            self.widgets.insert(position, widget)
            self.ids.append(widget.id)
            self.layout.insertWidget(position, widget)

    def remove(self, item_id):
        for widget in self.widgets:
            if widget['id'] == item_id:
                widget.setVisible(False)

    def clear(self):
        for widget in self.widgets:
            self.layout.removeWidget(widget)
            widget.setVisible(False)
        self.widgets = []
        self.ids = []


class ChatListPanel(QMainWindow):
    def __init__(self, parent):
        super().__init__()
        self.main_window = parent
        self.toolbar = gui.menu.Toolbar(self)
        self.addToolBar(self.toolbar)
        self.setMaximumWidth(config.Gui.CHAT_LIST_MAX_WIDTH)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.timeout)
        self.timer.start(config.Gui.chat_list_update_ms)

        self.background_pixmap = QPixmap(config.Gui.BACKGROUND_CHAT_LIST).scaled(self.size(), Qt.IgnoreAspectRatio)
        self.background_brush = QBrush(self.background_pixmap)
        self.background_palette = QPalette()
        self.background_palette.setBrush(QPalette.Background, self.background_brush)
        self.setPalette(self.background_palette)
        self.setAutoFillBackground(True)

        self.chat_list_widget = QWidget()
        self.chat_list_layout = QVBoxLayout()
        self.chat_list_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_list_layout.setSpacing(0)
        self.chat_list_layout.setAlignment(Qt.AlignTop)

        self.select_widget = QWidget()
        self.select_layout = QHBoxLayout()

        self.select_layout.setContentsMargins(0, 0, 0, 0)
        self.select_layout.addWidget(GroupSelectWidget())
        self.select_layout.addWidget(StatusSelectWidget())
        self.select_widget.setLayout(self.select_layout)
        self.chat_list_layout.addWidget(self.select_widget)

        self.list_widget = ChatListWidget()
        self.buddies = []
        self.item_list = []

        self.set_list()

        self.chat_list_layout.addWidget(self.list_widget)
        self.chat_list_widget.setLayout(self.chat_list_layout)

        self.setCentralWidget(self.chat_list_widget)

    def set_list(self, status: int = config.STATUS_ALL):
        global chat_list_changed
        if not chat_list_changed:
            return
        chat_list_changed = False

        global show_group, show_status
        # If group select option changed
        if not self.list_widget.show_group == show_group:
            self.list_widget.clear()
            self.list_widget.show_group = show_group
        # If status radio button changed (and group option is the same)
        if not self.list_widget.show_status == show_status:
            self.list_widget.clear()
            self.list_widget.show_status = show_status

        self.buddies = core.contacts.get_buddies(group=show_group, status=status)

        for buddy in self.buddies:
            if not buddy['id'] in self.list_widget.ids:
                list_item = ChatListItem(buddy)
                self.list_widget.insert(buddy['position'], list_item)

        self.list_widget.setLayout(self.list_widget.layout)

    def timeout(self) -> None:
        global show_status, chat_list_changed
        if chat_list_changed:
            self.set_list(show_status)


class MessageListItem(QFrame):
    def __init__(self, message):
        super().__init__()
        self.layout = QHBoxLayout()

        self.label = QLabel(message)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)


class MessageListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.timer = QTimer(self)
        self.timer.start(100)

        self.label = QLabel('No messages yet.')
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)
        self.show_messages('1')

    def show_messages(self, buddy_id):
        self.label.setVisible(False)
        for message in core.contacts.get_messages(buddy_id):
            self.layout.addWidget(MessageListItem(message))


class MessageListPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(config.Gui.MESSAGE_LIST_MIN_WIDTH)
        self.background_pixmap = QPixmap(config.Gui.BACKGROUND_MESSAGE_LIST).scaled(self.size(), Qt.IgnoreAspectRatio)
        self.background_brush = QBrush(self.background_pixmap)
        self.background_palette = QPalette()
        self.background_palette.setBrush(QPalette.Background, self.background_brush)
        self.setPalette(self.background_palette)
        self.setAutoFillBackground(True)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)

        self.message_list_widget = MessageListWidget()

        self.layout.addWidget(self.message_list_widget)
        self.setLayout(self.layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.App.TITLE)
        self.setMinimumSize(config.Gui.WINDOW_MIN_SIZE)
        self.setWindowIcon(QIcon(config.Gui.ICON_APP))

        self.menu = gui.menu.Menubar(self)
        self.chat_list_panel = ChatListPanel(self)
        self.message_list_panel = MessageListPanel()

        # Insert toolbar menu show/hide action before status bar action
        self.menu.view.insertAction(self.menu.view_status_bar, self.chat_list_panel.toolbar.toggle_view)
        self.setMenuBar(self.menu)

        self.statusbar = gui.menu.StatusBar()
        self.setStatusBar(self.statusbar)
        status_pixmap = QPixmap(os.path.join(config.App.ICON_DIR, 'disconnected.png')
                                ).scaled(config.Gui.statusbar_icon_size)
        self.status_label = QLabel('Status: Disconnected')
        self.status_icon = QLabel('')
        self.status_icon.setPixmap(status_pixmap)
        self.status_icon.setToolTip(self.status_label.text())
        self.statusbar.addPermanentWidget(self.status_label)
        self.statusbar.addPermanentWidget(self.status_icon)

        self.central_widget = QWidget()
        self.central_layout = QHBoxLayout()
        self.central_layout.setSpacing(0)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.addWidget(self.chat_list_panel)
        self.central_layout.addWidget(self.message_list_panel)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)
