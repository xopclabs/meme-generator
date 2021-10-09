from PySide6.QtCore import QObject, Signal
from scraper.parallelscraper import ParallelScraper

class ScraperWorker(QObject):
    finished = Signal()

    def __init__(self, plan):
        super().__init__()
        self.plan = plan
        self.scraper = ParallelScraper()

    def run(self):
        self.scraper.scrape(self.plan)
        self.finished.emit()
