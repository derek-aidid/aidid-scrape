# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AididHouseItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    name = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    district = scrapy.Field()
    price = scrapy.Field()
    space = scrapy.Field()
    layout = scrapy.Field()
    house_type = scrapy.Field()
    floors = scrapy.Field()
    community = scrapy.Field()
    basic_info = scrapy.Field()
    features = scrapy.Field()
    review = scrapy.Field()
    images = scrapy.Field()