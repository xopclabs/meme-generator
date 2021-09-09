import vk
import requests
from os import environ
from datetime import datetime
from typing import Tuple, List
from database.models import Session, Public, Post, Meme
from database.utils import filter_posts


class Scraper:

    def __init__(self, public: Public, token: str=None):
        self.public = public
        self._domain = public.domain
        self._owner_id = public.id
        self._token = environ['VKAPI_TOKEN'] if token is None else token

    def _open_session(self) -> None:
        self.api_session = vk.Session(access_token=self._token)
        self.api = vk.API(self.api_session, v='5.131', lang='ru', timeout=10)

    def _request(self, offset: int = 0, count: int = 100) -> dict:
        response = self.api.wall.get(domain=self._domain, count=count,
                                 offset=offset)
        if 'error' in response.keys():
            if response['error']['error_code'] == 29:
                raise ConnectionRefusedError('API calls limit reached')
        return response['items']

    def _to_datetime_string(self, ts: datetime) -> str:
        return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

    def _get_biggest_pic_url(self, photos: dict) -> str:
        sizes = photos['sizes']
        sizes = sorted(sizes, key=lambda x: x['height'], reverse=True)
        return sizes[0]['url']

    def _download_picture(self, url: str) -> bytes:
        img_data = requests.get(url).content
        return img_data

    def _filter_response(self, response: dict, limit: int = 100) -> dict:
        ids = [p['id'] for p in response]
        filtered_ids = filter_posts(ids, self._owner_id, limit=limit)
        filtered = [p for p in response if p['id'] in filtered_ids]
        return filtered

    def _parse_posts(self, response: dict) -> Tuple[List[Post], List[Meme]]:
        posts = []
        memes = []

        for p in response:
            print(f'{p["owner_id"]}_{p["id"]}:', end=' ')
            # Skip sponsored posts
            if p['marked_as_ads'] == 1:
                print('[X]')
                continue
            # Skip posts without attachments
            if 'attachments' not in p.keys():
                print('[X]')
                continue
            # Also skip posts without photos
            if all(map(lambda x: x['type'] != 'photo', p['attachments'])):
                print('[X]')
                continue

            # Create new post
            post = Post(
                public=self.public,
                post_id=p['id'],
                date=self._to_datetime_string(p['date']),
                text=p['text'],
                comments=p['comments']['count'],
                likes=p['likes']['count'],
                reposts=p['reposts']['count'],
                views=p['views']['count']
            )
            posts.append(post)
            print('[POST]', end=' ')

            # Parse and download pictures
            pics_urls = [x['photo'] for x in p['attachments'] if x['type'] == 'photo']
            for i, urls in enumerate(pics_urls):
                biggest_url = self._get_biggest_pic_url(urls)
                meme = Meme(
                    post=post,
                    index=i if len(pics_urls) > 1 else None,
                    picture=self._download_picture(biggest_url)
                )
                memes.append(meme)
                print('[PIC]', end=' ')
            print()
        return posts, memes

    def _save_to_db(self, posts: List[Post], memes: List[Meme]) -> None:
        session = Session()
        session.add_all(posts)
        session.add_all(memes)
        session.commit()
        session.close()

    def _scrape_pipeline(
            self,
            offset: int = 0,
            count: int = 100,
            limit: int = 100
    ) -> dict:
        response = self._request(offset=offset, count=count)
        response = self._filter_response(response, limit=limit)
        posts, memes = self._parse_posts(response)
        # Create report dict
        pic_size = sum(map(lambda x: len(x.picture) / 1e6, memes))
        self._save_to_db(posts, memes)
        return {'n_posts': len(posts), 'n_pics': len(memes), 'size': pic_size}

    def _accumulate_stats(self, stats: dict, report: dict) -> dict:
        for key in stats.keys():
            stats[key] += report[key]
        return stats

    def scrape(self, offset: int = 0, count: int = 100) -> None:
        # Establish session if it hasn't yet
        if not hasattr(self, 'api'):
            self._open_session()

        # Split requests into batches of maximum 100 posts
        offsets = range(count - 100, -100, -100)
        counts = [100 + min(o, 0) for o in offsets]
        offsets = list(map(lambda x: max(x, 0), offsets))

        stats = {'n_posts': 0, 'n_pics': 0, 'size': 0}
        for o, c in zip(offsets, counts):
            report = self._scrape_pipeline(offset=o, count=c, limit=count)
            stats = self._accumulate_stats(stats, report)
        print(f'+{stats["n_posts"]} posts, +{stats["n_pics"]} pics ({stats["size"]:.2f} MB)')
