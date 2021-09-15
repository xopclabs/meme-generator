from sqlalchemy import func
from scraper.parallelscraper import Scraper, ParallelScraper
from ocr.cropper import Cropper
from database.utils import add_public, get_public
from database.models import Post, Meme, Crop
from database.engine import Session


if __name__ == '__main__':
    try:
        add_public('-166124324', 'poiskmemow')
        add_public('-95648824', 'memy_pro_kotow')
        add_public('-129440544', 'eternalclassic')
        add_public('-150550417', 'reddit')
        add_public('-120254617', 'dank_memes_ayylmao')
        add_public('-160814627', 'electromeme')
        add_public('-140295869', 'degroklassniki')
        add_public('-67580761', 'countryballs_re')
        add_public('-57846937', 'mudakoff')
    except:
        pass
    plan = {
        'memy_pro_kotow': 500,
        'eternalclassic': 500,
        'reddit': 500,
        'dank_memes_ayylmao': 500,
        'poiskmemow': 500,
        'electromeme': 500,
        'degroklassniki': 500,
        'countryballs_re': 500,
        'mudakoff': 500,
    }
    # scraper = ParallelScraper()
    # scraper.scrape(plan)

    cropper = Cropper()
    # cropper.crop()
    with Session() as s:
        cropper.process_meme(s.query(Meme).filter(Meme.id == 1).one())


    # s = Session()
    # memes = s.query(Meme).filter(Meme.index != None).limit(5).all()
    # for m in memes:
    #     print(m)
    #     s.delete(m.post)
    # s.commit()
    # print()
    # print(*memes, sep='\n')
