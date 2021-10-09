from PySide6.QtWidgets import QApplication
from sys import exit
from gui.app import MainWidget


if __name__ == "__main__":
    app = QApplication([])

    widget = MainWidget()
    widget.resize(800, 600)
    widget.window_title = 'meme-generate'
    widget.show()

    exit(app.exec())
