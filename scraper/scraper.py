from os import environ
import vk


class Scraper:

    def __init__(self, token=None):
        if token is None:
            token = environ['VKAPI_TOKEN']
        self.session = vk.Session(access_token=token)
        self.api = vk.API(self.session, v='5.131', lang='ru', timeout=10)
