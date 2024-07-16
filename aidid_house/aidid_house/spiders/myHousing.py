import scrapy
import re

class MyhousingSpider(scrapy.Spider):
    name = "myHousing"
    allowed_domains = ["www.myhousing.com.tw"]
    start_urls = [f"https://www.myhousing.com.tw/category/real-estate-news/page/{i}/" for i in range(1, 2000)]

    def parse(self, response):
        urls = response.xpath('//div[@class="td-module-meta-info"]/h3/a/@href').getall()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_case_page)

    def parse_case_page(self, response):

        topic = response.xpath('//a[@class="tdb-entry-category"]/text()').get()
        title = response.xpath('//h1[@class="tdb-title-text"]/text()').get()

        body = ''.join(response.css('div.tdb-block-inner.td-fix-index p ::text').getall())
        if body == '':
            body = ''.join(response.css('div.tdb-block-inner.td-fix-index div ::text').getall()).strip()

        # Clean the text: remove whitespace, non-breaking spaces, newline characters, and emojis
        body = re.sub(r'\s+', ' ', body)

        date = response.xpath('//time[@class="entry-date updated td-module-date"]/text()').get()

        yield {
            'Website': '住展',
            'Topic': topic,
            'Title': title,
            'Body': body,
            'Date': date,
        }
