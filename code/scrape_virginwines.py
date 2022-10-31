import json
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from tqdm import tqdm

listing_urls_path = Path('./data/url/virginwines_listings.json')
export_path = './data/scrapped/virginwines_listings.csv'

if not listing_urls_path.exists():
    driver = Chrome()

    listing_urls = []

    pagenum = 1
    while True:
        listing_page_url = f'https://www.virginwines.co.uk/browse?page={pagenum}&pageSize=96'

        driver.get(listing_page_url)

        listings = driver.find_elements(
            By.XPATH,
            '//a[contains(@class, "text-underline") and contains(@data-gacategory, "wine-plp")]',
        )

        if not listings:
            # when there is no element => break while loop
            print(f'Done. Got {len(listing_urls)} bottles.')
            break

        for listing in listings:
            listing_urls.append(listing.get_attribute('href'))

        print(f'Found {len(listings)} listings on page {pagenum}')

        pagenum = pagenum + 1
        time.sleep(1)

    with open(listing_urls_path, 'w') as f:
        json.dump(listing_urls, f, indent=4)
else:
    listing_urls = json.load(open(listing_urls_path))


def clean_text_data(value):
    return value.strip().replace('\n', '').replace('\t', '').replace(':', '')


def get_price(soup):
    price_str = soup.find('p', class_='price h3 m-0 text-sanchez text-lh-1').text
    return float(price_str.replace('£', ''))


def get_bottle_size(li_tags):
    bottle_size_raw = clean_text_data(li_tags[2].find('span').text)

    if 'cl' in bottle_size_raw:
        return float(bottle_size_raw.replace('cl', ''))
    elif bottle_size_raw == 'Magnum 1.5L':
        return 150
    else:
        raise ValueError(f'edge case found {bottle_size_raw}')


wine_info_all = []

for listing_url in tqdm(listing_urls):
    listing_page = requests.get(listing_url)
    soup = BeautifulSoup(listing_page.content, 'html.parser')

    wine_data = {}

    wine_data['name'] = soup.find('h1', class_='h4 mt-3 mt-lg-3 mb-2').text

    li_tags = soup.find_all(
        'li',
        {
            'class': 'd-flex flex-column flex-sm-row justify-content-between justify-content-sm-center align-items-center text-center text-white bg-black p-3 p-sm-2',
        },
    )
    wine_data['abv'] = float(clean_text_data(li_tags[0].find('span').text).replace('%', ''))
    wine_data['year'] = clean_text_data(li_tags[1].find('span').text)
    wine_data['size (cL)'] = get_bottle_size(li_tags)

    bottle_attributes = (
        soup
        .find('ul', {'class': 'bottle-attributes bottle-attributes-list list-unstyled mb-0 text-left'})
    )

    try:
        wine_data['country'] = clean_text_data(
            bottle_attributes.find('a', {'data-gaaction': 'country-link'}).text,
        )
    except AttributeError:
        wine_data['country'] = None

    try:
        wine_data['wine_type'] = bottle_attributes.find(
            'a',
            {'data-gaaction': 'wine-category-link'},
        ).text
    except AttributeError:
        wine_data['wine_type'] = None

    wine_data['price'] = get_price(soup)
    wine_data['num_review'] = (
        soup
        .find('meta', {'itemprop': 'reviewCount'})
        .attrs['content']
    )
    wine_data['rating'] = float(
        soup
        .find('span', id='prod-content-review-count')
        .attrs['data-original-title']
        .split(' ')[0],
    )
    wine_data['url'] = listing_url

    wine_info_all.append(wine_data)

df = pd.DataFrame(wine_info_all)
df.to_csv(export_path, index=False)
