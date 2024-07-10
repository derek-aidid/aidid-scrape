import scrapy
import json
import re
from aidid_house.items import AididHouseItem


class Buy591Spider(scrapy.Spider):
    name = "buy591"
    start_urls = ['https://sale.591.com.tw/']

    region_ids = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 19, 21, 22, 23, 24, 25]
    # region_ids = [1]
    houses_per_page = 30  # Adjust according to the number of houses per page

    def parse(self, response):
        # Extract CSRF token
        csrf_token = response.xpath('//meta[@name="csrf-token"]/@content').get()

        if csrf_token:
            headers = {
                'X-CSRF-TOKEN': csrf_token,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
            }

            for region_id in self.region_ids:
                url = f'https://sale.591.com.tw/home/search/list-v2?type=2&category=1&shType=list&regionid={region_id}&firstRow=0'
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_list,
                    headers=headers,
                    meta={'csrf_token': csrf_token, 'region_id': region_id, 'firstRow': 0}
                )
        else:
            self.logger.error('CSRF token not found')

    def parse_list(self, response):
        json_response = json.loads(response.text)

        # Check if status is 1 indicating success
        if json_response.get('status') == 1:
            timestamp = json_response.get('timestamp')
            data = json_response.get('data', {})
            totalRows = data.get('total', 0)
            house_list = data.get('house_list', [])

            for house in house_list:
                if house.get('type') == '2':  # Ensure house type is 2
                    houseid = house.get('houseid')
                    if houseid:
                        detail_url = f'https://sale.591.com.tw/home/house/detail/2/{houseid}.html'
                        yield scrapy.Request(
                            url=detail_url,
                            callback=self.parse_detail,
                            headers=response.request.headers,
                            meta={'csrf_token': response.meta['csrf_token']}
                        )

            # Pagination
            firstRow = response.meta['firstRow'] + self.houses_per_page
            if firstRow < int(totalRows):
                next_page_url = f"https://sale.591.com.tw/home/search/list-v2?type=2&category=1&shType=list&regionid={response.meta['region_id']}&firstRow={firstRow}&totalRows={totalRows}"
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_list,
                    headers=response.request.headers,
                    meta={'csrf_token': response.meta['csrf_token'], 'region_id': response.meta['region_id'], 'firstRow': firstRow, 'totalRows': totalRows,}
                )
        else:
            self.logger.error('Failed to fetch data')

    def parse_detail(self, response):
        name_list = response.xpath('//h1[@class="detail-title-content"]/text()').getall()
        name = ''.join([name.strip() for name in name_list if name.strip()])

        price = response.xpath('//div[@class="info-price-left"]/span/text()').get().strip()

        layout = ''.join(response.xpath(".//div[@class='info-floor-left']/div[contains(@class, 'info-floor-value') and contains(text(), '格')]/preceding-sibling::div[@class='info-floor-key']/text()").getall()).strip()
        house_type = ''.join(response.xpath(".//div[@class='info-floor-left']/div[contains(@class, 'info-floor-value') and contains(text(), '屋')]/preceding-sibling::div[@class='info-floor-key']/text()").getall()).strip()
        space = ''.join(response.xpath(".//div[@class='info-floor-left']/div[contains(@class, 'info-floor-value') and contains(text(), '權')]/preceding-sibling::div[@class='info-floor-key']//text()").getall()).strip()

        floors = ''.join(response.xpath(
            ".//div[@class='info-addr-content']/span[contains(@class, 'info-addr-key') and contains(text(), '樓')]/following-sibling::span[contains(@class, 'info-addr-value')]//text()").getall()).strip()
        community = ''.join(response.xpath(".//div[@class='info-addr-content']/span[contains(text(), '社')]/following-sibling::span//text()").getall()).strip()
        address = ''.join(response.xpath(".//div[@class='info-addr-content']/span[contains(text(), '地')]/following-sibling::span//text()").getall()).strip()
        # Extract review
        review_element = response.xpath('//div[@id="detail-feature-text"]')
        review = ' '.join(review_element.xpath('.//text()').getall()).replace('\u00a0', '').strip()

        direction = ''.join(response.xpath(".//div[@class='info-addr-content']/span[contains(text(), '朝')]/following-sibling::span//text()").getall()).strip()

        # Extract city and district from address
        city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市|鄉))', address)
        city = city_district_match.group(1) if city_district_match else '無'
        district = city_district_match.group(2) if city_district_match else '無'

        basic_info = []
        features = []

        detail_house_boxes = response.xpath('//div[@class="detail-house-box"]')
        for box in detail_house_boxes:
            items = box.xpath('.//div[@class="detail-house-item"]')
            for item in items:
                key = item.xpath('.//div[@class="detail-house-key"]/text()').get()
                value = item.xpath('.//div[@class="detail-house-value"]/text()').get()
                if key and value:
                    basic_info.append(f'{key}: {value}')
                else:
                    feature = item.xpath('.//div[@class="detail-house-value"]/text()').get()
                    if feature:
                        features.append(feature)

            life_items = box.xpath('.//div[@class="detail-house-life"]')
            for life_item in life_items:
                feature = life_item.xpath('text()').get()
                if feature:
                    features.append(feature)

        images = response.xpath('//div[@id="img_list"]//img/@src').getall()
        basic_info.append(direction)
        # Extract community history
        community_history = []
        onsale_list_items = response.xpath('//div[@class="onsale-list-item"]').getall()
        for item in onsale_list_items:
            history = ''.join(item.xpath('.//span/text()').getall()).strip()
            community_history.append(history)

        yield {
            'url': response.url,
            'name': name,
            'address': address,
            'city': city,
            'district': district,
            'price': price,
            'layout': layout,
            'house_type': house_type,
            'space': space,
            'floors': floors,
            'community': community,
            'basic_info': basic_info,
            'features': features,
            'review': review,
            'images': images,
        }
        item = AididHouseItem(
            url=response.url,
            name=name,
            address=address,
            city=city,
            district=district,
            price=price,
            layout=layout,
            house_type=house_type,
            space=space,
            floors=floors,
            community=community,
            basic_info=basic_info,
            features=features,
            review=review,
            images=images,
        )
