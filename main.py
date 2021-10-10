from mixer.mixer import Mixer
from scraper.parallelscraper import ParallelScraper
from ocr.cropper import Cropper
from database.utils import add_public
from database.models import *
from database.engine import Session


if __name__ == '__main__':
    ids = ['-166124324', '-95648824', '-129440544', '-150550417',
           '-120254617', '-160814627', '-140295869', '-67580761',
           '-57846937']
    domains = ['poiskmemow', 'memy_pro_kotow', 'eternalclassic',
               'reddit', 'dank_memes_ayylmao', 'electromeme',
               'degroklassniki', 'countryballs_re', 'mudakoff']
    for i, d in zip(ids, domains):
        try:
            add_public(id=i, domain=d)
        except:
            pass

    plan = {
        'memy_pro_kotow': 300,
        'eternalclassic': 300,
        'reddit': 300,
        'dank_memes_ayylmao': 300,
        'poiskmemow': 300,
        'electromeme': 300,
        'degroklassniki': 300,
        'countryballs_re': 300,
        'mudakoff': 300,
    }

    # scraper = ParallelScraper()
    # scraper.scrape(plan)

    # cropper = Cropper()
    # cropper.crop()

    for i in range(100):
        print(f'Mixing {i+1}')
        mixer = Mixer()
        base_post, posts = mixer.get_random_mix(
            include_publics=['memy_pro_kotow'],
            exact_pics=1,
            max_crops=3
        )
        base_post, crops = mixer.pick_crops(base_post, posts, how='firstonly')
        memes = mixer.compose(base_post, crops)
        mixer.save_to_database(base_post, crops, memes)
        # mixer.save_to_file(memes, f'{i}_test.jpg')
