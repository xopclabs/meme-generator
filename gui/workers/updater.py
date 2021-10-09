from PySide6.QtCore import QObject, Signal
from scraper.parallelscraper import ParallelScraper
from ocr.cropper import Cropper

class Updater(QObject):
    finished = Signal()

    def __init__(self, plan):
        super().__init__()
        self.plan = plan

    def run(self):
        print('Scraping...')
        scraper = ParallelScraper()
        scraper.scrape(self.plan)
        print('Cropping...')
        cropper = Cropper()
        cropper.crop()
        self.finished.emit()
