from PySide6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout,
                               QGridLayout, QPushButton, QLabel)
from PySide6.QtCore import Qt, QThread, Slot, QByteArray
from PySide6.QtGui import QPixmap
from io import BytesIO
from .workers.updater import Updater
from mixer.mixer import Mixer


class MainWidget(QWidget):
    """Main window"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        # self.mixer = Mixer()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.imageLabel = QLabel(self, alignment=Qt.AlignCenter)
        layout.addWidget(self.imageLabel)

        button = QPushButton(text='Generate')
        button.clicked.connect(self.open_image)
        layout.addWidget(button)

        # Pop up dialog prompting to update database
        # dialog = QMessageBox(self)
        # dialog.setWindowTitle('meme-generator')
        # dialog.setText('Update database with new posts?')
        # dialog.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        # button = dialog.exec()
        # if button == QMessageBox.Yes:
        #     self.update_database()

    @Slot()
    def open_image(self):
        pass
        # mix = self.mixer.random_mix(
        #     include_publics=['memy_pro_kotow'],
        #     max_pics=1
        # )
        # buff = BytesIO()
        # picture = self.mixer.compose(*mix)[0]
        # picture.thumbnail((600, 600))
        # picture.save(buff, format='JPEG')
        # picture_bytes = buff.getvalue()
        # pixmap = QPixmap()
        # pixmap.loadFromData(QByteArray(picture_bytes), 'JPEG')
        # self.imageLabel.setPixmap(pixmap)


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
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
