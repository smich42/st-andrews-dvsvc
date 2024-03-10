# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class CandidatePage(Item):
    url = Field()
    pscore = Field()
    page_text = Field()
    time_crawled = Field()

    def __repr__(self):
        return f"{self.__class__.__name__}({self['url']}, {self['pscore']})"
