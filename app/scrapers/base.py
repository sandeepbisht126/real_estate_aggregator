from abc import ABC, abstractmethod


class BaseScraper(ABC):

    @abstractmethod
    async def search(self, filters):
        pass

    @abstractmethod
    async def parse_listing(self, page, url):
        pass
