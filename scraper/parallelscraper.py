from pathos.multiprocessing import ProcessingPool as Pool
from typing import Dict, List, Tuple
from itertools import repeat
from functools import reduce
from scraper.scraper import Scraper
from database.utils import get_public
from database.engine import Session
from scraper.utils import print_stats, accumulate_stats


def _pool_func(params: Tuple[Scraper, int]):
    scraper, count = params
    return scraper.scrape_return(count=count, print_report=False)


class ParallelScraper:

    def _get_scrapers(self, scrape_plan: Dict[str, int]) -> List[Scraper]:
        publics = [get_public(domain=d) for d in scrape_plan.keys()]
        return [Scraper(p) for p in publics]

    def scrape(self, scrape_plan: Dict[str, int]) -> None:
        # Check if scrape plan post counts does not exceed max API calls
        if sum(scrape_plan.values()) > 50000:
            raise ValueError('Scraping plan exceeds maximum allowed API calls')

        # Get Scraper instance for each public
        scrapers = self._get_scrapers(scrape_plan)
        # Open shared db session
        session = Session()

        # Scrape using multiprocessing
        with Pool(processes=len(scrapers)) as pool:
            map_return = pool.map(
                _pool_func,
                zip(scrapers, scrape_plan.values())
            )
        # Parse map_return List[Tuple[StatDict, List[Post], List[Meme]]]
        stats = [r[0] for r in map_return]
        posts = [r[1] for r in map_return]
        memes = [r[2] for r in map_return]

        # Commit and close session
        for p, m in zip(posts, memes):
            session.add_all(p)
            session.add_all(p)
            session.commit()
        session.close()

        # Print report
        print()
        for domain, stat in zip(scrape_plan.keys(), stats):
            print_stats(domain, stat)
        total_stats = reduce(accumulate_stats, stats)
        print_stats('TOTAL', total_stats)
