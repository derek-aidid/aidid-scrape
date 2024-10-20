import scrapy
import requests
from aidid_house.items import AididHouseItem
import json
import re
class BuyHBSpider(scrapy.Spider):
    name = 'buyHB'
    allowed_domains = ['hbhousing.com.tw']
    start_urls = ["https://www.hbhousing.com.tw/BuyHouse/"]

    def parse(self, response):
        url = 'https://www.hbhousing.com.tw/ajax/dataService.aspx?job=search&path=house&kv=false'

        for page_number in range(1, 6000):
            try:
                payload = {
                    'job': 'search',
                    'path': 'house',
                    'kv': 'false',
                    'q': f'2^1^^^^P^1_9^^^^^^^^^^^^9^^{page_number}^0',
                    'rlg': '0'
                }

                yield scrapy.FormRequest(
                    url=url,
                    method='POST',
                    formdata=payload,
                    callback=self.parse_page,
                    meta={'page_number': page_number}
                )
                
            except Exception as e:
                self.logger.error(f"An error occurred: {e}")
                break

    def parse_page(self, response):
        # Check if the request was successful
        if response.status == 200:
            # Assuming the response is JSON-like, parse it
            data = json.loads(response.text)

            # Extract specific fields
            houses = data.get('data')  # Adjust this line based on actual response structure
            if houses:
                for house in houses:
                    case_id = house.get('s')
                    case_url = f'https://www.hbhousing.com.tw/detail/?sn={case_id}'
                    images = [f'https:{img}' for img in house.get('i', [])]
                    self.logger.info(f'Parsing {case_id}')
                    yield scrapy.Request(
                        url=case_url,
                        callback=self.parse_case_page,
                        meta={'images': images, 'case_id': case_id},
                    )

    def parse_case_page(self, response):
        self.logger.info(f'Parsing {response.url}')
        name = response.xpath('//div[@class="item-info"]/p[@class="item_name"]/text()').get()

        city_names = [
            "臺北市", "台北市", "新北市", "桃園市", "臺中市", "台中市", "臺南市", "台南市", "高雄市",
            "基隆市", "新竹市", "嘉義市", "宜蘭縣", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣",
            "嘉義縣", "屏東縣", "花蓮縣", "臺東縣", "澎湖縣"
        ]

        # Create a set of the first two characters of each city name
        city_substrings = {city[:2] for city in city_names}

        # Remove any city substrings from the name
        for substring in city_substrings:
            if substring in name:
                name = name.replace(substring, '').strip()
        address = response.xpath('//div[@class="item-info"]/p[@class="item_add"]/text()').get()

        city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市|鄉))', address)
        city = city_district_match.group(1) if city_district_match else '無'
        district = city_district_match.group(2) if city_district_match else '無'

        price = response.xpath('//div[@class="item_price"]/span[@class="hightlightprice"]/text()').get()
        space = response.xpath('//ul[@class="item_other"]/li[@class="icon_space"]/text()').get()
        layout = response.xpath('//ul[@class="item_other"]/li[@class="icon_room"]/text()').get()
        house_type = response.xpath('//ul[@class="item_other"]/li[@class="icon_age"]/text()').get()
        floors = response.xpath('//ul[@class="item_other"]/li[@class="icon_floor"]/text()').get()
        community = response.xpath('//tr[td[text()="社區"]]/td[2]/text()').get().strip()
        images = response.meta.get('images', [])
        case_id = response.meta.get('case_id')

        lon, lat = self.get_lat_lon(case_id)
        self.logger.info(f"Longitude: {lon} | Latitude: {lat}")

        basic_info_box = response.xpath('//div[contains(@class, "basicinfo-box")]')

        basic_info_elements = basic_info_box.xpath('.//table//tr')
        basic_info = []
        for element in basic_info_elements:
            first_td = element.xpath('.//td[1]/text()').get()
            second_td = ''.join([t for t in element.xpath('.//td[2]//text()').getall() if
                                 element.xpath('./td[2]/button').get() is None]).strip()
            if first_td and second_td:
                first_td = first_td.strip()
                basic_info.append(f"{first_td}: {second_td}")
        basic_info_str = ' | '.join(basic_info)

        features_elements = response.xpath('//ul[@class="features-other"]/li/text()').getall()
        features_str = ' | '.join([feature.strip() for feature in features_elements])

        life_info_elements = response.xpath('//ul[@class="house__features"]/li')
        life_info = []
        for element in life_info_elements:
            title = element.xpath('.//p[@class="features__tit"]/text()').get()
            detail = element.xpath('.//p[@class="features__tit02"]/text()').get()
            distance = element.xpath('.//p[@class="features__info"]/span/text()').get()
            if title and detail:
                info = f"{title}: {detail}"
                if distance:
                    info += f" ({distance}公尺)"
                life_info.append(info)
        life_info_str = ' | '.join(life_info)

        item = AididHouseItem(
            url=response.url,
            site='住商',
            name=name,
            address=address,
            longitude=lon,
            latitude=lat,
            city=city,
            district=district,
            price=price,
            layout=layout,
            house_type=house_type,
            space=space,
            floors=floors,
            community=community,
            basic_info=basic_info_str,
            features=features_str,
            life_info=life_info_str,
            utility_info=life_info_str,
            review='',
            images=images,
        )

        yield item

    def get_lat_lon(self, case_id):
        # Set the URL for the API call
        url = f'https://www.hbhousing.com.tw/Detail/map.aspx?sn={case_id}'

        # Set headers to mimic browser request
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Referer': f'https://www.hbhousing.com.tw/detail/?sn={case_id}',
        }

        # Make the GET request
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Extract the longitude and latitude from the JavaScript on the page
            script_text = response.text
            lon, lat = None, None
            match = re.search(r'lon=([\d.]+),lat=([\d.]+);', script_text)
            if match:
                lon = float(match.group(1))
                lat = float(match.group(2))
            return lon, lat
        else:
            self.logger.error(f"Request for map API failed with status code: {response.status_code}")
            return None, None

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))