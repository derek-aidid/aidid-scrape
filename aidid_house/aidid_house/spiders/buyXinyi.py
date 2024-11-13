import scrapy
from aidid_house.items import AididHouseItem
import re
import json

class BuyxinyiSpider(scrapy.Spider):
    name = "buyXinyi"
    allowed_domains = ["www.sinyi.com.tw"]
    taipei_city = [f"https://www.sinyi.com.tw/buy/list/Taipei-city/default-desc/{i}" for i in range(1, 307)]
    new_taipei_city = [f"https://www.sinyi.com.tw/buy/list/NewTaipei-city/default-desc/{i}" for i in range(1, 247)]
    keelong = [f"https://www.sinyi.com.tw/buy/list/Keelung-city/default-desc/{i}" for i in range(1, 96)]
    yilan_county = [f"https://www.sinyi.com.tw/buy/list/Yilan-county/default-desc/{i}" for i in range(1, 135)]
    hsinchu_city = [f"https://www.sinyi.com.tw/buy/list/Hsinchu-city/default-desc/{i}" for i in range(1, 40)]
    hsinchu_county = [f"https://www.sinyi.com.tw/buy/list/Hsinchu-county/default-desc/{i}" for i in range(1, 95)]
    taoyuan_city = [f"https://www.sinyi.com.tw/buy/list/Taoyuan-city/default-desc/{i}" for i in range(1, 615)]
    miaoli_county = [f"https://www.sinyi.com.tw/buy/list/Miaoli-county/default-desc/{i}" for i in range(1, 133)]
    taichung_city = [f"https://www.sinyi.com.tw/buy/list/Taichung-city/default-desc/{i}" for i in range(1, 687)]
    changhua_county = [f"https://www.sinyi.com.tw/buy/list/Changhua-county/default-desc/{i}" for i in range(1, 338)]
    nantou_county = [f"https://www.sinyi.com.tw/buy/list/Nantou-county/default-desc/{i}" for i in range(1, 60)]
    yunlin_county = [f"https://www.sinyi.com.tw/buy/list/Yunlin-county/default-desc/{i}" for i in range(1, 82)]
    chiayi_city = [f"https://www.sinyi.com.tw/buy/list/Chiayi-city/default-desc/{i}" for i in range(1, 51)]
    chiayi_county = [f"https://www.sinyi.com.tw/buy/list/Chiayi-county/default-desc/{i}" for i in range(1, 72)]
    tainan_city = [f"https://www.sinyi.com.tw/buy/list/Tainan-city/default-desc/{i}" for i in range(1, 574)]
    kaohsiung_city = [f"https://www.sinyi.com.tw/buy/list/Kaohsiung-city/default-desc/{i}" for i in range(1, 363)]
    pingtung_county = [f"https://www.sinyi.com.tw/buy/list/Pingtung-county/default-desc/{i}" for i in range(1, 177)]
    penghu_county = [f"https://www.sinyi.com.tw/buy/list/Penghu-county/default-desc/{i}" for i in range(1, 10)]
    taitung_county = [f"https://www.sinyi.com.tw/buy/list/Taitung-county/default-desc/{i}" for i in range(1, 57)]
    hualien_county = [f"https://www.sinyi.com.tw/buy/list/Hualien-county/default-desc/{i}" for i in range(1, 74)]
    kinmen_county = [f"https://www.sinyi.com.tw/buy/list/Kinmen-county/default-desc/{i}" for i in range(1, 7)]

    start_urls = taipei_city + new_taipei_city + keelong + yilan_county + hsinchu_city + hsinchu_county + taoyuan_city + miaoli_county + taichung_city + changhua_county + nantou_county + yunlin_county + chiayi_city + chiayi_county + tainan_city + kaohsiung_city + pingtung_county + penghu_county + taitung_county + hualien_county + kinmen_county

    def parse(self, response):
        urls = response.xpath('//div[@class="buy-list-item "]/a/@href').getall()
        for url in urls:
            full_url = f'https://www.sinyi.com.tw{url}'
            yield scrapy.Request(full_url, callback=self.parse_case_page)

    def parse_case_page(self, response):
        name = response.xpath('//span[@class="buy-content-title-name"]/text()').get()
        city_names = [
            "臺北市", "台北市", "新北市", "桃園市", "臺中市", "台中市", "臺南市", "台南市", "高雄市",
            "基隆市", "新竹市", "嘉義市", "宜蘭縣", "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣",
            "嘉義縣", "屏東縣", "花蓮縣", "臺東縣", "澎湖縣"
        ]

        # Create a set of the first two characters of each city name
        city_substrings = {city[:2] for city in city_names}

        # Remove any city substrings from the name0
        for substring in city_substrings:
            if substring in name:
                name = name.replace(substring, '').strip()

        address = response.xpath('//span[@class="buy-content-title-address"]/text()').get()

        city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市|鄉))', address)
        city = city_district_match.group(1) if city_district_match else '無'
        district = city_district_match.group(2) if city_district_match else '無'

        price = ''.join(response.xpath('//div[@class="buy-content-title-total-price"]/text()').getall())
        space = ' '.join(response.xpath('//div[@class="buy-content-detail-area"]/div/div/span/text()').getall())
        layout = response.xpath('//div[@class="buy-content-detail-layout"]/div/text()').get()
        house_type = ''.join(response.xpath('//div[@class="buy-content-detail-type"]/div/div/span/text()').getall())
        floors = response.xpath('//div[@class="buy-content-detail-floor"]/text()').get()
        community = ''.join(response.xpath('//div[@class="communityButton"]/span/text()').getall()).replace('社區','').strip()
        basic_infos = response.xpath('//div[@class="buy-content-basic-cell"]')
        basic_info_dict = {}
        for basic_info in basic_infos:
            try:
                title = basic_info.xpath('.//div[@class="basic-title"]/text()').get().strip()
                value = basic_info.xpath('.//div[@class="basic-value"]/text()').get().strip()
                basic_info_dict[title] = value
            except Exception as e:
                try:
                    title = basic_info.xpath('.//div[@class="basic-title"]/text()').get().strip()
                    value = basic_info.xpath('.//div[@class="basic-value"]/span/text()').get().strip()
                    basic_info_dict[title] = value
                except Exception as e:
                    continue
        basic_info_list = [f"{key}: {value}" for key, value in basic_info_dict.items()]
        basic_info_str = ' | '.join(basic_info_list)

        features = response.xpath('//div[@class="buy-content-obj-feature"]//div[@class="description-cell-text"]/text()').getall()
        tags = ' | '.join(response.xpath('//div[@class="tags-cell"]/text()').getall()).strip()
        features_str = ' | '.join(features)
        neighbor_history = []
        neighbor_history_rows = response.xpath(
            '//div[@id="trade-table-list-buyTradeBodyLg"]/div/div[contains(@class, "trade-obj-card-web")]')

        images = response.xpath('//div[@class="carousel-thumbnail-img "]/img/@src').getall()

        script_text = response.xpath('//script[contains(text(), "__NEXT_DATA__")]/text()').get()
        json_data = json.loads(re.search(r'__NEXT_DATA__\s*=\s*({.*?});', script_text).group(1))
        lat = json_data['props']['initialReduxState']['buyReducer']['contentData']['latitude']
        lon = json_data['props']['initialReduxState']['buyReducer']['contentData']['longitude']

        # Extract lifeInfo data
        life_info = json_data['props']['initialReduxState']['buyReducer']['detailData']['lifeInfo']

        # Format lifeInfo data
        life_info_str = ' || '.join(
            f"{info['type']}: " + ' | '.join(
                f"{i['title']} (距離: {i['distance']} 公尺, 時間: {i['time']} 秒, lat: {i['lifeLatitude']}, lng: {i['lifeLongitude']})"
                for i in info['info']
            )
            for info in life_info
        )

        # Extract utilitylifeInfo data
        utility_life_info = json_data['props']['initialReduxState']['buyReducer']['detailData']['utilitylifeInfo']

        # Format utilitylifeInfo data
        utility_life_info_str = ' || '.join(
            f"{info['utilityType']}: " + ' | '.join(
                f"{poi['utilitySubType']} - " + ' | '.join(
                    f"{p['title']} (距離: {p['distance']} 公尺, 時間: {p['time']} 秒, lat: {p['poiLatitude']}, lng: {p['poiLongitude']})"
                    for p in poi['pois']
                )
                for poi in info['poiList']
            )
            for info in utility_life_info
        )

        site = '信義房屋'

        if response.xpath('//span[@class="buy-content-sameTrade"]/text()').get() == '非信義物件':
            source = response.xpath('//div[@class="buy-content-store-title"]/text()').get()
            site = '信義房屋' + '(' + source + ')'

        item = AididHouseItem(
            url=response.url,
            site=site,
            name=name,
            address=address,
            latitude=lat,
            longitude=lon,
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
            utility_info=utility_life_info_str,
            review=tags,
            images=images,
        )

        yield item
