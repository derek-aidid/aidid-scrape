import scrapy
import re

class HousefunSpider(scrapy.Spider):
    name = "houseFun"
    allowed_domains = ["news.housefun.com.tw"]
    start_urls = [f"https://news.housefun.com.tw/news/%E5%85%A8%E5%9C%8B/{i}" for i in range(12001, 20001)]

    def parse(self, response):
        urls = response.xpath('//article[@class="news-list-item"]/a/@href').getall()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(full_url, callback=self.parse_case_page)

    def parse_case_page(self, response):
        topic = ''.join(response.css('div.breadcrumb-wrap div.breadcrumb a::text, div.breadcrumb-wrap div.breadcrumb span::text').getall())
        title = response.xpath('//h1[@class="main-heading"]/text()').get()

        body_divs = response.css('div.section-body div::text').getall()

        # Join all the text into a single string
        body_text = ' '.join(body_divs).strip()

        # Clean the text: remove excess whitespace, non-breaking spaces, and newline characters
        body_text = re.sub(r'\s+', ' ', body_text)
        body = body_text.replace('\xa0', ' ')

        # Clean the text: remove whitespace, non-breaking spaces, newline characters, and emojis
        body = re.sub(r'\s+', ' ', body)

        date = response.xpath('//time/text()').get().split()[0]

        yield {
            'Website': '好房網',
            'Topic': topic,
            'Title': title,
            'Body': body,
            'Date': date,
        }
