import requests
import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


# Path to the text file containing the HTML
html_file_path = 'C:/Users/derek/Downloads/房產資訊.txt'

# Read the HTML content from the file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML to extract URLs
soup = BeautifulSoup(html_content, 'html.parser')
urls = [a['href'] for a in soup.find_all('a', href=True) if a['href'].strip()]
ua = UserAgent()

# Function to fetch and parse each URL
def fetch_and_parse(url):
    headers = {'User-Agent': ua.random}
    response = requests.get(url, headers=headers)
    page_soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the name of the article from the <h1> tag
    article_name = page_soup.find('h1').get_text(strip=True) if page_soup.find('h1') else 'Article Name not found'

    # Extract the date from the <span class="time"> tag
    date_tag = page_soup.find('span', class_='time')
    try:
        date_text = date_tag.get_text(strip=True).split()[0]
    except Exception as e:
        date_text = None

    # Extract the body text from the <div class="text boxTitle" data-desc="內文"> element
    body_div = page_soup.find('div', class_='text boxTitle', attrs={'data-desc': '內文'})
    body_text = ''.join(body_div.stripped_strings) if body_div else 'Body not found'

    return article_name, date_text, body_text


# Initialize a list to store the data
data = []

# Loop through each URL and collect the extracted information
for url in urls:
    print(url)
    article_name, date_text, body_text = fetch_and_parse(url)
    print(article_name, date_text, body_text)
    data.append({
        "Topic": "房產資訊",
        "Title": article_name,
        "Date": date_text,
        "Body": body_text,
        "Website": "自由時報"
    })

# Create a DataFrame from the collected data
df = pd.DataFrame(data)

# Save the DataFrame to a CSV file
csv_file_path = 'C:/Users/derek/Downloads/房產資訊_articles.csv'
df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')

print(f"Data saved to {csv_file_path}")
