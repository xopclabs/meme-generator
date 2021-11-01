from PySide6.QtWidgets import (QMainWindow, QWidget, QMessageBox, QVBoxLayout,
                               QGridLayout, QPushButton, QLabel, QDialog)

from PySide6.QtCore import Qt, QThread, Slot, Signal, QByteArray
from PySide6.QtGui import QPixmap, QKeySequence, QShortcut
from io import BytesIO
from typing import List, Dict, Union
from .workers import Updater, QtMixer
from .mixing_settings import MixingSettings
from .utils.config import import_config, export_config
from mixer.mixer import Mixer


class MainWidget(QMainWindow):
    """Main window"""

    def __init__(self):
        super().__init__()
        # Meme mixer instance
        self.mixer = Mixer()
        self.mixer_params = import_config() or {}
        print(f'mixer: {self.mixer_params}')
        # Initializing all of gui
        self.init_ui()
        # Pregenerating posts list for snappy UX
        self.post_idx = 3
        self.posts = []
        for _ in range(6):
            self._generate_post(parallel=False)
        print(self.posts)
        # Preload first post
        self.pixmaps_idx = 0
        self._set_pixmap()

    def init_ui(self):
        layout = QVBoxLayout(self)
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.mixingSettings = MixingSettings(self)
        self.mixingSettings.changed_params.connect(self.set_mixing_params)

        self.imageLabel = QLabel(self, alignment=Qt.AlignCenter)
        layout.addWidget(self.imageLabel)

        self.changeMixingButton = QPushButton(text='Change mixing parameters')
        self.changeMixingButton.clicked.connect(self.mixingSettings.exec)
        layout.addWidget(self.changeMixingButton)

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
        button.clicked.connect(self.next_post)
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
        self.setCentralWidget(centralWidget)
        # Pop up dialog prompting to update database
        # dialog = QMessageBox(self)
        # dialog.setWindowTitle('meme-generator')
        # dialog.setText('Update database with new posts?')
        # dialog.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        # button = dialog.exec()
        # if button == QMessageBox.Yes:
        #     self._update_database()

    def _update_database(self):
        plan = {
            'memy_pro_kotow': 100,
            'eternalclassic': 100,
            'reddit': 100,
            'dank_memes_ayylmao': 100,
            'poiskmemow': 100,
            'mudakoff': 100,
        }

        self.updateThread = QThread(self)
        self.updateWorker = Updater(plan)
        self.updateWorker.moveToThread(self.updateThread)
        self.updateThread.started.connect(self.updateWorker.run)
        self.updateWorker.finished.connect(self.updateWorker.deleteLater)
        self.updateThread.finished.connect(self.updateThread.deleteLater)
        self.updateThread.start()

    def _generate_post(self, parallel=True):
        if parallel:
            self.mixerThread = QThread(self)
            self.mixerWorker = QtMixer(self.mixer, self.mixer_params)
            self.mixerWorker.moveToThread(self.mixerThread)
            self.mixerThread.started.connect(self.mixerWorker.run)
            self.mixerWorker.post.connect(lambda post: self.posts.append(post))
            self.mixerWorker.finished.connect(self.mixerWorker.deleteLater)
            self.mixerThread.start()
        else:
            mix = self.mixer.get_random_mix(**self.mixer_params)
            mix = self.mixer.pick_crops(*mix)
            post = self.mixer.compose(*mix)
            self.posts.append(post)

    def _set_pixmap(self):
        img = self.posts[self.post_idx][self.pixmaps_idx]
        buff = BytesIO()
        img.thumbnail((600, 600))
        img.save(buff, format='JPEG')
        picture_bytes = buff.getvalue()
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(picture_bytes), 'JPEG')
        self.imageLabel.setPixmap(pixmap)

    def _update_nav_buttons(self):
        if len(self.posts[self.post_idx]) == 1:
            self.prevPixmapButton.setEnabled(False)
            self.nextPixmapButton.setEnabled(False)
        elif self.pixmaps_idx == 0:
            self.prevPixmapButton.setEnabled(False)
            self.nextPixmapButton.setEnabled(True)
        elif self.pixmaps_idx == len(self.posts[self.post_idx]) - 1:
            self.prevPixmapButton.setEnabled(True)
            self.nextPixmapButton.setEnabled(False)
        else:
            self.prevPixmapButton.setEnabled(True)
            self.nextPixmapButton.setEnabled(True)

    @Slot()
    def open_settings(self):
        self.mixingSettings.exec()

    @Slot(dict)
    def set_mixing_params(self, params: Dict[str, Union[str, int]]) -> None:
        self.mixer_params = params
        export_config(self.mixer_params)
        self.posts = []
        self.post_idx = 0
        print('set', self.post_idx, len(self.posts))
        self._generate_post(parallel=False)
        for _ in range(5):
            self._generate_post()

    @Slot()
    def prev_image(self):
        # Update indices
        self.pixmaps_idx = max(0, self.pixmaps_idx - 1)
        # Set new image
        self._set_pixmap()
        # Update buttons
        self._update_nav_buttons()

    @Slot()
    def next_image(self):
        # Update indices
        self.pixmaps_idx = min(
            len(self.posts[self.post_idx]) - 1,
            self.pixmaps_idx + 1
        )
        # Set new image
        self._set_pixmap()
        # Update buttons
        self._update_nav_buttons()

    @Slot()
    def prev_post(self):
        # Update indices
        self.post_idx = max(0, self.post_idx - 1)
        self.pixmaps_idx = 0
        print(self.post_idx)
        # Set new image
        self._set_pixmap()
        # Update buttons
        self._update_nav_buttons()
        print('prev', self.post_idx, len(self.posts))

    @Slot()
    def next_post(self):
        if self.post_idx >= 3:
            self._generate_post()
            self.posts.pop(0)
        else:
            self.post_idx += 1
        self.pixmaps_idx = 0
        # Set new image
        self._set_pixmap()
        # Update buttons
        self._update_nav_buttons()
        print('next', self.post_idx, len(self.posts))
