from PySide6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout,
                               QGridLayout, QPushButton, QLabel)
from PySide6.QtCore import QThread
from .workers.updater import Updater


class MainWidget(QWidget):
    """Main window"""

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('text'))
        self.setLayout(layout)

        # Pop up dialog prompting to update database
        dialog = QMessageBox(self)
        dialog.setWindowTitle('meme-generator')
        dialog.setText('Update database with new posts?')
        dialog.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        button = dialog.exec()
        if button == QMessageBox.Yes:
            self.update_database()

    def update_database(self):
        plan = {
            'memy_pro_kotow': 100,
            'eternalclassic': 100,
            'reddit': 100,
            'dank_memes_ayylmao': 100,
            'poiskmemow': 100,
            'mudakoff': 100,
        }

        self.thread = QThread()
        self.worker = Updater(plan)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
