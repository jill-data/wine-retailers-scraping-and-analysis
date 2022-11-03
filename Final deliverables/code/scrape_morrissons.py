import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm

listing_urls_path = Path('./data/url/morrissons_listings.json')
export_path = './data/scraped/morrissons_listings.csv'

if not listing_urls_path.exists():
    driver = Chrome()
    listing_urls = []

    wine_type_urls = {
        'white': 'https://groceries.morrisons.com/browse/beer-wines-spirits-103120/wine-champagne-176432/white-wine-176434',
        'rose': 'https://groceries.morrisons.com/browse/beer-wines-spirits-103120/wine-champagne-176432/rose-wine-176435',
        'sparkling': 'https://groceries.morrisons.com/browse/beer-wines-spirits-103120/wine-champagne-176432/champagne-sparkling-wine-176436',
        'red': 'https://groceries.morrisons.com/browse/beer-wines-spirits-103120/wine-champagne-176432/red-wine-176433',
        'fortified_and_other': 'https://groceries.morrisons.com/browse/beer-wines-spirits-103120/wine-champagne-176432/fortified-wines-miscellaneous-176441',
    }

    for wine_type, wine_type_url in wine_type_urls.items():
        driver.get(wine_type_url)

        driver.maximize_window()

        time.sleep(2)

        # Accept cookies
        try:
            cookie_button = driver.find_element(
                By.XPATH,
                '//button[@id="onetrust-accept-btn-handler"]'
            )
            cookie_button.click()
        except NoSuchElementException:
            pass

        # Show all listings
        while True:
            banner = driver.find_element(
                By.XPATH,
                '//body[@class="app-page"]'
            )
            for _ in range(10):
                banner.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.2)
            try:
                show_more_button = driver.find_element(
                    By.XPATH,
                    '//button[@class="btn-primary show-more"]'
                )

                show_more_button.click()
                time.sleep(3)
            except NoSuchElementException:
                break

        # Shop section
        shop_section = driver.find_element(
            By.XPATH,
            '//ul[contains(@class, "fops fops-regular fops-shelf")]'
        )

        # Find listings
        listings = shop_section.find_elements(
            By.XPATH,
            '//div[contains(@class,"fop-contentWrapper")]'
        )

        print(f'Found {len(listings)} {wine_type} listings')

        for listing in listings:
            listing_urls.append(
                [
                    wine_type,
                    listing.find_element(
                        By.XPATH,
                        './/a',
                    ).get_attribute('href'),
                ]
            )

    print(f'Found {len(listing_urls)} listings in total')

    with open(listing_urls_path, 'w') as f:
        json.dump(listing_urls, f, indent=4)
else:
    listing_urls = json.load(open(listing_urls_path))


def get_bottle_size(soup):
    size_str = soup.find(class_='bop-catchWeight').text
    size_numeric = float(re.sub('[a-zA-Z]', '', size_str))

    # If size is denoted in L
    if size_numeric < 10:
        return size_numeric * 100
    elif size_numeric > 100:
        # If size is denoted in mL
        return size_numeric / 10

    # If size is denoted in cL
    return size_numeric


def get_name(soup):
    title_tag = soup.find(class_='bop-title').find('h1')

    # remove the bottle size from the title
    _ = title_tag.span.extract()

    return title_tag.text.strip()


def get_price(soup):
    return float(soup.find(class_='bop-price__current').text.replace('£', ''))


def get_bop_info_content(info_tag):
    return info_tag.find(class_='bop-info__content').text


def get_rating(soup):
    return float(
        soup
        .find(class_='bop-titleInfoWrapper')
        .find(class_='gn-rating__inactiveLayer')
        .find(itemprop='ratingValue')
        ['content']
    )


def get_num_reviews(soup):
    return int(re.sub(
        r'\W+',
        '',
        soup.find(class_='gn-rating__voteCount gn-content__paragraph--small').text
    ))


def get_origin_from_description(soup):
    product_description = soup.find(
        class_='bop-section bop-productDetails gn-accordion')
    product_description_splitted = re.split('[,.!?<>\']', str(product_description))

    # Country of origin is usually specified near the bottom
    for chunk in product_description_splitted[::-1]:
        for keyword in ['Product of', 'Wine of']:
            if keyword in chunk:
                return chunk.replace(keyword, '').strip()


wine_info_all = []

for wine_type, listing_url in tqdm(listing_urls):
    listing_page = requests.get(listing_url)
    soup = BeautifulSoup(listing_page.content, 'html.parser')

    wine_info = {}

    wine_info['wine_type'] = wine_type
    try:
        wine_info['size (cL)'] = get_bottle_size(soup)
    except AttributeError:
        # Skip non-wine listings, e.g., https://groceries.morrisons.com/products/freixenet-prosecco-20cl-luxury-scented-candle-gift-set-566440011
        continue
    wine_info['name'] = get_name(soup)
    wine_info['price'] = get_price(soup)
    wine_info['rating'] = get_rating(soup)
    wine_info['num_review'] = get_num_reviews(soup)

    info_tags = soup.findAll(class_='gn-content bop-info__field')
    for info_tag in info_tags:
        try:
            info_type = info_tag.find('h6').text
        except AttributeError:
            # skip fields without any title
            continue

        if info_type == 'Country of Origin':
            wine_info['country'] = get_bop_info_content(info_tag)
        elif info_type == 'ABV (%)':
            wine_info['abv'] = float(get_bop_info_content(info_tag))
        elif info_type == 'Current Vintage':
            # Can't convert to int as some listings don't specify the year
            wine_info['year'] = get_bop_info_content(info_tag)

    if not wine_info.get('country'):
        wine_info['country'] = get_origin_from_description(soup)
    wine_info['url'] = listing_url

    wine_info_all.append(wine_info)

wine_info_df = pd.DataFrame(wine_info_all)
wine_info_df.to_csv(export_path, index=False)
