from scraper.scraper import Scraper
from database.utils import add_public, get_public, filter_posts

if __name__ == '__main__':
    try:
        public = add_public(id='-95648824', domain='memy_pro_kotow')
    except:
        pass
    public = get_public(domain='memy_pro_kotow')

    scraper = Scraper(public)
    scraper.scrape(count=550)
