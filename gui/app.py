from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout,
                               QPushButton)
from PySide6.QtCore import QThread
from .workers.scraper_worker import ScraperWorker


class MainWidget(QWidget):
    """Main window"""

    def __init__(self):
        super().__init__()

        self.button = QPushButton('Scrape')
        self.button.pressed.connect(self.scrape)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)

    def scrape(self):
        plan = {
            'memy_pro_kotow': 100,
            'eternalclassic': 100,
            'reddit': 100,
            'dank_memes_ayylmao': 100,
            'poiskmemow': 100,
            'mudakoff': 100,
        }

        self.thread = QThread()
        self.worker = ScraperWorker(plan)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        # Button enabling
        self.button.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.button.setEnabled(True)
        )
