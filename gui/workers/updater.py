from PySide6.QtCore import QObject, Signal
from scraper.parallelscraper import ParallelScraper
from ocr.cropper import Cropper

class Updater(QObject):
    finished = Signal()

    def __init__(self, plan):
        super().__init__()
        self.plan = plan
        self.scraper = ParallelScraper()
        self.cropper = Cropper()

    def run(self):
        self.scraper.scrape(self.plan)
        self.cropper.crop()
        self.finished.emit()
