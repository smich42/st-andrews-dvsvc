# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class DVSVCPage(Item):
    link = Field()
    pscore = Field()
    time_crawled = Field()

    def __str__(self):
        return f"{self.__class__.__name__}({self['link']}, {self['pscore']})"


class DVSVCPageSet(Item):
    pages = Field()

    def __str__(self):
        return f"{self.__class__.__name__}({self['pages']})"
