import os
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

import theme
from main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("BO3 Weapon CSV Editor")
    app.setStyle("Fusion")
    app.setFont(QFont(theme.FONT, 9))
    app.setStyleSheet(theme.QSS)

    window = MainWindow()
    window.show()

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        window.load_file(sys.argv[1])

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
