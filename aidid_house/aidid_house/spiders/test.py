import time
import random
import requests
from bs4 import BeautifulSoup

headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36 Edg/88.0.705.68',
        }

# 紀錄 Cookie 取得 X-CSRF-TOKEN
s = requests.Session()
url = 'https://sale.591.com.tw/'

r = s.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
token_item = soup.select_one('meta[name="csrf-token"]')

print(token_item)
#
# headers = self.headers.copy()
# headers['X-CSRF-TOKEN'] = token_item.get('content')
#
# # 搜尋房屋
url = 'https://sale.591.com.tw/home/search/rsList'
params = 'category=1&shType=list'
# if filter_params:
#     # 加上篩選參數，要先轉換為 URL 參數字串格式
#     params += ''.join([f'&{key}={value}' for key, value, in filter_params.items()])
# else:
#     params += '&region=1&kind=0'
# # 在 cookie 設定地區縣市，避免某些條件無法取得資料
# s.cookies.set('urlJumpIp', filter_params.get('region', '1') if filter_params else '1', domain='.591.com.tw')