import scrapy
import json
import re
from aidid_house.items import AididHouseItem
import time

class Buy591Spider(scrapy.Spider):
    name = "buy591"
    start_urls = ['https://sale.591.com.tw/']
    region_ids = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 17, 19, 21, 22, 23, 24, 25]
    houses_per_page = 30  # Adjust according to the number of houses per page

    def parse(self, response):
        csrf_token = response.xpath('//meta[@name="csrf-token"]/@content').get()

        if csrf_token:
            self.csrf_token = csrf_token
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


    def parse_list(self, response):
        json_response = json.loads(response.text)

        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            totalRows = data.get('total', 0)
            house_list = data.get('house_list', [])

            for house in house_list:
                if house.get('type') == '2':
                    houseid = house.get('houseid')
                    if houseid:
                        detail_url = f'https://sale.591.com.tw/home/house/detail/2/{houseid}.html'
                        yield scrapy.Request(
                            url=detail_url,
                            callback=self.parse_detail,
                            headers=response.request.headers,
                            meta={'csrf_token': response.meta['csrf_token'], 'houseid': houseid}
                        )

            firstRow = response.meta['firstRow'] + self.houses_per_page
            if firstRow < int(totalRows):
                next_page_url = f"https://sale.591.com.tw/home/search/list-v2?type=2&category=1&shType=list&regionid={response.meta['region_id']}&firstRow={firstRow}&totalRows={totalRows}"
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_list,
                    headers=response.request.headers,
                    meta={'csrf_token': response.meta['csrf_token'], 'region_id': response.meta['region_id'], 'firstRow': firstRow, 'totalRows': totalRows, }
                )

    def parse_detail(self, response):
        name_list = response.xpath('//h1[@class="detail-title-content"]/text()').getall()
        name = ''.join([name.strip() for name in name_list if name.strip()])

        price = response.xpath('//div[@class="info-price-left"]/span/text()').get().strip()

        layout = ''.join(response.xpath(
            ".//div[@class='info-floor-left']/div[contains(@class, 'info-floor-value') and contains(text(), '格')]/preceding-sibling::div[@class='info-floor-key']/text()").getall()).strip()
        house_type = ''.join(response.xpath(
            ".//div[@class='info-floor-left']/div[contains(@class, 'info-floor-value') and contains(text(), '屋')]/preceding-sibling::div[@class='info-floor-key']/text()").getall()).strip()
        space = ''.join(response.xpath(
            ".//div[@class='info-floor-left']/div[contains(@class, 'info-floor-value') and contains(text(), '權')]/preceding-sibling::div[@class='info-floor-key']//text()").getall()).strip()

        floors = ''.join(response.xpath(
            ".//div[@class='info-addr-content']/span[contains(@class, 'info-addr-key') and contains(text(), '樓')]/following-sibling::span[contains(@class, 'info-addr-value')]//text()").getall()).strip()
        community = ''.join(response.xpath(
            ".//div[@class='info-addr-content']/span[contains(text(), '社')]/following-sibling::span//text()").getall()).strip()
        address = ''.join(response.xpath(
            ".//div[@class='info-addr-content']/span[contains(text(), '地')]/following-sibling::span//text()").getall()).strip()

        # Remove city names from name
        cities = ['台北', '台中', '台南', '新北', '桃園', '高雄', '基隆', '新竹', '嘉義', '宜蘭', '苗栗', '彰化',
                  '南投', '雲林', '屏東', '花蓮', '台東', '澎湖', '金門', '連江']
        for city in cities:
            name = name.replace(city, '')

        review_element = response.xpath('//div[@id="detail-feature-text"]')
        review = ' '.join(review_element.xpath('.//text()').getall()).replace('\u00a0', '').strip()

        direction = ''.join(response.xpath(
            ".//div[@class='info-addr-content']/span[contains(text(), '朝')]/following-sibling::span//text()").getall()).strip()

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

        houseid = response.meta['houseid']
        # Extract the script content
        script_content = response.xpath('//script[@id="payMap"]/text()').get()

        # Extract collect_id, latitude, and longitude using regex
        collect_id_match = re.search(r'collect_id=(\d+)', script_content)
        collect_id = collect_id_match.group(1) if collect_id_match else None

        lat_lng_match = re.search(r'lat=([\d\.]+)&lng=([\d\.]+)', script_content)
        lat, lng = lat_lng_match.groups() if lat_lng_match else (None, None)

        full_address_url = f'https://bff-house.591.com.tw/v1/community/sale/detail?id={houseid}&device=pc'
        utility_life_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=1000&types=bus_station&types=subway_station'
        school_info_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=2000&types=primary_school&types=secondary_school&types=university&types=school'
        life_info_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=1000&types[]=shopping_mall'
        restaurant_info_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=1000&types[]=restaurant'
        hospital_info_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=1000&types[]=hospital'
        park_info_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=1000&types[]=park'
        bank_info_url = f'https://bff-business.591.com.tw/v1/ware/surrounding?collect_id={collect_id}&distance=1000&types[]=bank'

        meta_data = {
            'url': response.url,
            'name': name,
            'address': address,
            'latitude': lat,
            'longitude': lng,
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
            'utility_life_url': utility_life_url,
            'school_info_url': school_info_url,
            'life_info_url': life_info_url,
            'restaurant_info_url': restaurant_info_url,
            'hospital_info_url': hospital_info_url,
            'park_info_url': park_info_url,
            'bank_info_url': bank_info_url
        }

        yield scrapy.Request(
            url=full_address_url,
            callback=self.parse_full_address_and_utility,
            headers=response.request.headers,
            meta=meta_data
        )

    def parse_full_address_and_utility(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        full_address = None
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            if 'keyword' in data['bar']['condition']:
                full_address = data['bar']['condition']['keyword']
            elif 'info' in data and 'address' in data['info']:
                full_address = data['info']['address']

        yield scrapy.Request(
            url=meta['utility_life_url'],
            callback=self.parse_utility_info,
            headers=response.request.headers,
            meta={**meta, 'address': full_address or meta['address']}
        )

    def parse_utility_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        utility_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    utility_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        yield scrapy.Request(
            url=meta['school_info_url'],
            callback=self.parse_school_info,
            headers=response.request.headers,
            meta={**meta, 'utility_info': utility_info}
        )

    def parse_school_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        school_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    school_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        utility_info = meta['utility_info'] + school_info

        yield scrapy.Request(
            url=meta['life_info_url'],
            callback=self.parse_life_info,
            headers=response.request.headers,
            meta={**meta, 'utility_info': utility_info}
        )

    def parse_life_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        life_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    life_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        yield scrapy.Request(
            url=meta['restaurant_info_url'],
            callback=self.parse_restaurant_info,
            headers=response.request.headers,
            meta={**meta, 'life_info': life_info}
        )

    def parse_restaurant_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        restaurant_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    restaurant_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        life_info = meta['life_info'] + restaurant_info

        yield scrapy.Request(
            url=meta['hospital_info_url'],
            callback=self.parse_hospital_info,
            headers=response.request.headers,
            meta={**meta, 'life_info': life_info}
        )

    def parse_hospital_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        hospital_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    hospital_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        life_info = meta['life_info'] + hospital_info

        yield scrapy.Request(
            url=meta['park_info_url'],
            callback=self.parse_park_info,
            headers=response.request.headers,
            meta={**meta, 'life_info': life_info}
        )

    def parse_park_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        park_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    park_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        life_info = meta['life_info'] + park_info

        yield scrapy.Request(
            url=meta['bank_info_url'],
            callback=self.parse_bank_info,
            headers=response.request.headers,
            meta={**meta, 'life_info': life_info}
        )

    def parse_bank_info(self, response):
        meta = response.meta
        json_response = json.loads(response.text)

        bank_info = ''
        if json_response.get('status') == 1:
            data = json_response.get('data', {})
            for key, value in data.items():
                for item in value:
                    bank_info += f"{key}: {item['place_name']} (距離: {item['distance']} 公尺) || "

        utility_info = meta['utility_info'] + bank_info

        item = AididHouseItem(
            url=meta['url'],
            site='591房屋',
            name=meta['name'],
            address=meta['address'],
            longitude=float(meta['longitude']),
            latitude=float(meta['latitude']),
            city=meta['city'],
            district=meta['district'],
            price=meta['price'],
            space=meta['space'],
            layout=meta['layout'],
            house_type=meta['house_type'],
            floors=meta['floors'],
            community=meta['community'],
            basic_info=' | '.join(meta['basic_info']),
            features=' | '.join(meta['features']),
            utility_info=utility_info,
            life_info=meta['life_info'],
            review=meta['review'],
            images=meta['images'],
        )
        yield item
