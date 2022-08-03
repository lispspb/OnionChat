import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

import config
import gui


def main():
    app = QApplication(sys.argv)
    window = gui.window.MainWindow()
    window.show()
    if not config.App.VERSION_STABLE:
        QMessageBox(QMessageBox.Icon.Warning, 'Unstable Release',
                    'You are running an unstable release of OnionChat.\n'
                    'Never use it for anything but development!').exec_()
    app.exec()


if __name__ == '__main__':
    main()
