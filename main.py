from scraper.parallelscraper import Scraper, ParallelScraper
from database.utils import add_public, get_public, filter_posts

if __name__ == '__main__':
    try:
        add_public('-95648824', 'memy_pro_kotow')
        add_public('-140764973', 'memory_memes')
    except:
        pass
    plan = {'memy_pro_kotow': 300, 'memory_memes': 300}
    scraper = ParallelScraper()
    scraper.scrape(plan)


    # public = get_public(domain='memy_pro_kotow')
    # scraper = Scraper(public)
    # scraper.scrape(count=1)
