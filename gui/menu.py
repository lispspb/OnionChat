from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QGridLayout, QLabel, QToolBar, QStatusBar, QAction, \
    QMenuBar, QMenu, QVBoxLayout, QTextBrowser
from PyQt5.QtGui import QPixmap, QMouseEvent, QFont, QIcon
import os.path
from functools import partial

from config import *
from gui.settings import SettingsDialog


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window |
                            Qt.WindowCloseButtonHint |
                            Qt.WindowTitleHint)
        self.setWindowTitle('About')
        self.setFixedSize(Gui.about_dialog_size)

        self.layout = QVBoxLayout()

        self.label = QLabel('This is about label Lorem Ipsum.')
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        self.exec()


class Toolbar(QToolBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.menu = self.parent().main_window.menu
        self.toggle_view = self.toggleViewAction()
        self.toggle_view.setText('&Toolbar')
        self.setMaximumWidth(Gui.TOOLBAR_MAX_WIDTH)
        self.setFloatable(False)

        self.font = QFont('serif', 16, 400)

        self.profile = QAction('🧑')  # 👤
        self.profile.setToolTip('My Profile')
        self.profile.setFont(self.font)
        self.dialog = QAction('💬')
        self.dialog.setToolTip('New Dialog')
        self.dialog.setFont(self.font)
        self.group = QAction('👪🏻')  # 👥👪
        self.group.setToolTip('New Group')
        self.group.setFont(self.font)
        self.lock = QAction('🔐')  # 🔒
        self.lock.setToolTip('Lock')
        self.lock.setFont(self.font)
        self.add = QAction('➕')
        self.add.setToolTip('Add Quick Action')
        self.add.setFont(self.font)

        self.actions = (self.profile, self.dialog, self.group, self.lock, self.add)
        self.addActions(self.actions)
        self.visibilityChanged.connect(self.visibility_changed)

    def visibility_changed(self, visible: bool) -> None:
        if visible:
            self.menu.toolbar.setVisible(False)
        else:
            self.menu.toolbar.setVisible(True)


class Menubar(QMenuBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.toolbar = QMenuBar()
        self.menubar = QMenuBar()
        self.main_window = parent

        self.profile = QAction('My &Profile')
        self.toolbar.addAction(self.profile)
        self.dialog = QAction('New &Dialog')
        self.toolbar.addAction(self.dialog)
        self.group = QAction('New &Group')
        self.toolbar.addAction(self.group)
        self.lock = QAction('&Lock')
        self.toolbar.addAction(self.lock)

        self.view = QMenu('&View')
        self.view_full_screen = QAction('&Full Screen')
        self.view_full_screen.setCheckable(True)
        self.view_full_screen.changed.connect(self.full_screen_changed)
        self.view.addAction(self.view_full_screen)
        self.view.addSeparator()

        self.view_status_bar = QAction('&Status Bar')
        self.view_status_bar.setCheckable(True)
        self.view_status_bar.setChecked(True)
        self.view_status_bar.changed.connect(self.status_bar_changed)
        self.view.addAction(self.view_status_bar)

        self.settings = QAction('&Settings')
        self.settings.triggered.connect(self.setting_triggered)

        self.help = QMenu('&Help')
        self.help_help = QAction('&Help')
        self.help_help.setShortcut('F1')
        self.help_help.triggered.connect(self.help_triggered)
        self.help.addAction(self.help_help)
        self.help.addSeparator()
        self.help_bugreport = QAction('Submit a Bug Report...')
        self.help.addAction(self.help_bugreport)
        self.help_feedback = QAction('Submit &Feedback...')
        self.help.addAction(self.help_feedback)
        self.help.addSeparator()
        self.help_update = QAction('&Check for Updates...')
        self.help.addAction(self.help_update)
        self.help_about = QAction('&About')
        self.help_about.triggered.connect(self.about_triggered)
        self.help.addAction(self.help_about)

        self.menubar.addMenu(self.view)
        self.menubar.addAction(self.settings)
        self.menubar.addMenu(self.help)

        self.menubar.setStyleSheet('font-size: 10.5pt;')

        self.setCornerWidget(self.toolbar, Qt.TopLeftCorner)
        self.setCornerWidget(self.menubar, Qt.TopRightCorner)

    def full_screen_changed(self):
        if self.view_full_screen.isChecked():
            if not self.main_window.isFullScreen():
                self.main_window.showFullScreen()
        else:
            if self.main_window.isFullScreen():
                self.main_window.showNormal()

    def status_bar_changed(self):
        if self.view_status_bar.isChecked():
            if self.main_window.statusbar.isHidden():
                self.main_window.statusbar.show()
        else:
            if not self.main_window.statusbar.isHidden():
                self.main_window.statusbar.hide()

    @staticmethod
    def setting_triggered():
        SettingsDialog()

    @staticmethod
    def help_triggered():
        HelpBrowser()

    @staticmethod
    def about_triggered():
        AboutDialog()


class StatusBar(QStatusBar):
    def __init__(self):
        super().__init__()
        self.showMessage('Welcome!', Gui.statusbar_welcome_msec)
