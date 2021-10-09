# from pathos.multiprocessing import ProcessingPool as Pool
from PySide6.QtCore import QObject, QThread, Signal
from multiprocessing import Pool
from typing import Dict, List, Tuple, Union
from itertools import repeat
from functools import reduce
from scraper.scraper import Scraper
from database.utils import get_public
from database.engine import Session
from scraper.utils import print_stats, accumulate_stats


ScrapePlan = Union[Dict[str, Tuple[int, int]], Dict[str, int]]


class ParallelScraper:

    def _get_scrapers(self, scrape_plan: Dict[str, int]) -> List[Scraper]:
        publics = [get_public(domain=d) for d in scrape_plan.keys()]
        return [Scraper(p) for p in publics]

    def _pool_func(self, params: Tuple[Scraper, int, int]):
        scraper, count, offset = params
        return scraper.scrape_return(offset=offset, count=count, print_report=False)

    def _update_scrape_plan(self, scrape_plan: ScrapePlan, batch: int = 100) -> ScrapePlan:
        # Add counts as offsets to scrape plan
        if type(next(iter(scrape_plan.values()))) is not tuple:
            scrape_plan = dict(zip(
                    scrape_plan.keys(),
                    zip(scrape_plan.values(), scrape_plan.values())
            ))
        # Update scrape_plans
        for k, (c, o) in scrape_plan.items():
            if o - batch > 0:
                scrape_plan[k] = (batch, o - batch)
            else:
                scrape_plan[k] = (o, 0)

        return scrape_plan

    def scrape(self, scrape_plan: Dict[str, int], batch_size: int = 100) -> None:
        # Check if scrape plan post counts does not exceed max API calls
        if sum(scrape_plan.values()) > 50000:
            raise ValueError('Scraping plan exceeds maximum allowed API calls')

        # Get Scraper instance for each public
        scrapers = self._get_scrapers(scrape_plan)

        stats = []
        # "Batch-process" data so that we can commit every n posts
        while any(map(lambda x: type(x) is int or x[1] != 0, scrape_plan.values())):
            # Update scrape_plan
            scrape_plan = self._update_scrape_plan(scrape_plan, batch=batch_size)
            # Scrape using multiprocessing
            with Pool(processes=len(scrapers)) as pool:
                map_return = pool.map(
                    self._pool_func,
                    zip(
                        scrapers,
                        [v[0] for v in scrape_plan.values()],
                        [v[1] for v in scrape_plan.values()]
                    )
                )
            # Parse map_return List[Tuple[StatDict, List[Post], List[Meme]]]
            # Parse stats
            batch_stats = [r[0] for r in map_return]
            if not stats:
                stats = batch_stats
            else:
                stats = list(map(lambda x: accumulate_stats(*x),
                                 zip(stats, batch_stats)))
            # Parse posts and memes
            posts = [r[1] for r in map_return]
            memes = [r[2] for r in map_return]
            # Commit data
            with Session() as session:
                for p, m in zip(posts, memes):
                    session.add_all(p)
                    session.add_all(m)
                    session.commit()
        # Print report
        print()
        for domain, stat in zip(scrape_plan.keys(), stats):
            print_stats(domain, stat)
        total_stats = reduce(accumulate_stats, stats)
        print_stats('TOTAL', total_stats)
