from PySide6.QtWidgets import (QWidget, QMessageBox, QVBoxLayout,
                               QGridLayout, QPushButton, QLabel)

from PySide6.QtCore import Qt, QThread, Slot, QByteArray
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from io import BytesIO
from typing import List
from .workers.updater import Updater, QtMixer
from mixer.mixer import Mixer


class MainWidget(QWidget):
    """Main window"""

    def __init__(self):
        super().__init__()
        # Meme mixer instance
        self.mixer = Mixer()
        # Pregenerated posts list for snappy UX
        self.posts_idx = 0
        self.posts = []
        self.pixmaps = []
        for _ in range(5):
            self._generate_post()
        # Pixmaps of current post
        # Initializing all of gui
        self.init_ui()
        # Preload first post
        self.pixmaps_idx = 0
        self._set_pixmaps()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.imageLabel = QLabel(self, alignment=Qt.AlignCenter)
        layout.addWidget(self.imageLabel)

        buttonLayout = QGridLayout()

        self.prevPostButton = QPushButton(text='<<')
        self.prevPostButton.clicked.connect(self.prev_post)
        buttonLayout.addWidget(self.prevPostButton, 0, 0, 1, 1)
        QShortcut(QKeySequence(Qt.Key_K), self, self.prev_post)

        self.prevPixmapButton = QPushButton(text='<')
        self.prevPixmapButton.clicked.connect(self.prev_image)
        buttonLayout.addWidget(self.prevPixmapButton, 0, 1, 1, 1)
        QShortcut(QKeySequence(Qt.Key_H), self, self.prev_image)

        button = QPushButton(text='Save and post')
        # button.clicked.connect(self.next_post)
        buttonLayout.addWidget(button, 0, 2, 1, 16)

        self.nextPixmapButton = QPushButton(text='>')
        self.nextPixmapButton.clicked.connect(self.next_image)
        buttonLayout.addWidget(self.nextPixmapButton, 0, 18, 1, 1)
        QShortcut(QKeySequence(Qt.Key_L), self, self.next_image)

        self.prevPostButton = QPushButton(text='>>')
        self.prevPostButton.clicked.connect(self.next_post)
        buttonLayout.addWidget(self.prevPostButton, 0, 19, 1, 1)
        QShortcut(QKeySequence(Qt.Key_J), self, self.next_post)

        layout.addLayout(buttonLayout)

        # Pop up dialog prompting to update database
        # dialog = QMessageBox(self)
        # dialog.setWindowTitle('meme-generator')
        # dialog.setText('Update database with new posts?')
        # dialog.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        # button = dialog.exec()
        # if button == QMessageBox.Yes:
        #     self.update_database()

    def _update_database(self):
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

    def _generate_post(self):
        mix = self.mixer.get_random_mix(
            exclude_publics=['degroklassniki'],
            exact_pics=2,
            max_crops=3
        )
        mix = self.mixer.pick_crops(*mix, how='firstonly')
        post = self.mixer.compose(*mix)
        pixmaps = []
        for m in post:
            buff = BytesIO()
            m.thumbnail((600, 600))
            m.save(buff, format='JPEG')
            picture_bytes = buff.getvalue()
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(picture_bytes), 'JPEG')
            pixmaps.append(pixmap)
        self.pixmaps.append(pixmaps)
        self.posts.append(post)
        print(len(self.posts))

    def _set_pixmaps(self):
        self.imageLabel.setPixmap(self.pixmaps[self.posts_idx][self.pixmaps_idx])

    def _update_nav_buttons(self):
        if self.pixmaps_idx == 0:
            self.prevPixmapButton.setEnabled(False)
            self.nextPixmapButton.setEnabled(True)
        elif self.pixmaps_idx == len(self.pixmaps) - 1:
            self.prevPixmapButton.setEnabled(True)
            self.nextPixmapButton.setEnabled(False)
        elif len(self.pixmaps) == 1:
            self.prevPixmapButton.setEnabled(False)
            self.nextPixmapButton.setEnabled(False)
        else:
            self.prevPixmapButton.setEnabled(True)
            self.nextPixmapButton.setEnabled(True)

    @Slot()
    def prev_post(self):
        self.post_idx = max(0, self.posts_idx - 1)
        self.pixmaps_idx = 0
        self._set_pixmaps()
        self._update_nav_buttons()

    @Slot()
    def next_post(self):
        self.posts_idx += 1
        self._generate_post()
        self.pixmaps_idx = 0
        self._set_pixmaps()
        self._update_nav_buttons()

    @Slot()
    def prev_image(self):
        self.pixmaps_idx = max(0, self.pixmaps_idx - 1)
        self._set_pixmaps()
        self._update_nav_buttons()

    @Slot()
    def next_image(self):
        self.pixmaps_idx = min(
            len(self.pixmaps) - 1,
            self.pixmaps_idx + 1
        )
        self._set_pixmaps()
        self._update_nav_buttons()
