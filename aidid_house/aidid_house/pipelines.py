import mysql.connector
from itemadapter import ItemAdapter
import re
import os
import json
import configparser
from datetime import datetime

config = configparser.ConfigParser()
config.read('config.ini')

class AididHousePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        def clean_field(value):
            if isinstance(value, str):
                value = re.sub(r'[^\w\s,./|:;?!-]', '', value)
                value = re.sub(r'(\W)\1{2,}', r'\1', value)
            return value

        for field_name, value in adapter.items():
            if field_name != 'url':
                adapter[field_name] = clean_field(value)

        if adapter.get('price'):
            price = adapter['price']
            price = re.sub(r'\D', '', price)
            adapter['price'] = int(price) if price else None

        if adapter.get('house_type'):
            type_info = adapter['house_type']
            years_match = re.search(r'(\d+\.?\d*)年|(\d+)個月', type_info)
            if years_match:
                if years_match.group(2):
                    years = round(int(years_match.group(2)) / 12, 1)
                else:
                    years = float(years_match.group(1))
            else:
                years = 0
            house_type = re.sub(r'(\d+\.?\d*年|(\d+)個月)', '', type_info).strip()
            adapter['house_type'] = years
            adapter['basic_info'] += house_type

        if adapter.get('space'):
            space = adapter['space']
            main_space_match = re.search(r'主\s*(\d+\.\d+|\d+)', space)
            if main_space_match:
                main_space = float(main_space_match.group(1))
            else:
                single_space_match = re.search(r'(\d+\.\d+|\d+)', space)
                if single_space_match:
                    main_space = float(single_space_match.group(1))
                else:
                    main_space = 0
            adapter['space'] = main_space

        if adapter.get('review'):
            review = adapter['review']
            adapter['review'] = review.replace('\u00a0', ' ').strip()

        return item


class SaveToMySQLPipeline:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host='aidid-db-mysql-do-user-17150710-0.b.db.ondigitalocean.com',
            user='doadmin',
            password='AVNS_ud7zyZ3uVcDGyuLNRmz',
            database='defaultdb',
            port=25060
        )
        self.cur = self.conn.cursor()

        # Generate table name based on the current date
        self.table_name = f"houses_{datetime.now().strftime('%m_%d_%Y')}"

        # Create the table if it does not exist
        self.cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INT NOT NULL AUTO_INCREMENT,
            site VARCHAR(255),
            url VARCHAR(255),
            name TEXT,
            address VARCHAR(255),
            longitude DOUBLE,
            latitude DOUBLE,
            city VARCHAR(255),
            district VARCHAR(255),
            price INT,
            space FLOAT,
            layout VARCHAR(255),
            house_type FLOAT,
            floors VARCHAR(255),
            community VARCHAR(255),
            basic_info TEXT,
            features TEXT,
            life_info TEXT,
            utility_info TEXT,
            review TEXT,
            images JSON,
            PRIMARY KEY (id)
        )
        """)
        # List of indexes to create
        indexes = [
            ('idx_city_district', ['city', 'district']),
            ('idx_price', ['price']),
            ('idx_space', ['space']),
            ('idx_layout', ['layout']),
            ('idx_house_type', ['house_type']),
            ('idx_community', ['community'])
        ]

# Create indexes if they don't exist
        for index_name, columns in indexes:
            check_index_query = f"""
            SELECT COUNT(1) 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE table_schema = DATABASE() 
              AND table_name = '{self.table_name}' 
              AND index_name = '{index_name}';
            """
            self.cur.execute(check_index_query)
            index_exists = self.cur.fetchone()[0]
            if not index_exists:
                columns_str = ', '.join(columns)
                create_index_query = f"CREATE INDEX {index_name} ON {self.table_name} ({columns_str});"
                self.cur.execute(create_index_query)

        # Commit the changes
        self.conn.commit()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Verify all parameters are present
        params = (
            adapter.get('url'),
            adapter.get('site'),
            adapter.get('name'),
            adapter.get('address'),
            adapter.get('longitude'),
            adapter.get('latitude'),
            adapter.get('city'),
            adapter.get('district'),
            adapter.get('price'),
            adapter.get('space'),
            adapter.get('layout'),
            adapter.get('house_type'),
            adapter.get('floors'),
            adapter.get('community'),
            json.dumps(adapter.get('basic_info')),
            json.dumps(adapter.get('features')),
            adapter.get('life_info'),
            adapter.get('utility_info'),
            adapter.get('review'),
            json.dumps(adapter.get('images'))
        )

        self.cur.execute(f"""
        INSERT INTO {self.table_name} (
            url, 
            site,
            name, 
            address,
            longitude,
            latitude,
            city, 
            district, 
            price, 
            space,
            layout, 
            house_type,
            floors,
            community,
            basic_info,
            features,
            life_info,
            utility_info,
            review,
            images
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """, params)

        self.conn.commit()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
