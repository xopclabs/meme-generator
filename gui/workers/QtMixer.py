from PySide6.QtCore import QObject, Signal
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QPixmap
from io import BytesIO


class QtMixer(QObject):
    finished = Signal()
    post = Signal(list)

    def __init__(self, mixer, mix_params):
        super().__init__()
        self.mixer = mixer
        self.mix_params = mix_params

    def run(self):
        mix = self.mixer.get_random_mix(**self.mix_params)
        mix = self.mixer.pick_crops(*mix, how='firstonly')
        post = self.mixer.compose(*mix)
        self.post.emit(post)
        self.finished.emit()
