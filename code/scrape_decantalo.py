import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from tqdm import tqdm

listing_urls_path = Path('./data/url/decantalo_listings.json')
export_path = './data/scrapped/decantalo_listings_abv.csv'

if not listing_urls_path.exists():
    driver = webdriver.Chrome()

    wine_type_urls = {
        'white': 'https://www.decantalo.com/uk/en/wine/white/',
        'rose': 'https://www.decantalo.com/uk/en/wine/rose/',
        'fortified and sherry': 'https://www.decantalo.com/uk/en/wine/fortified/',
        'red': 'https://www.decantalo.com/uk/en/wine/red/',
        'sweet': 'https://www.decantalo.com/uk/en/wine/sweet/',
        'orange': 'https://www.decantalo.com/uk/en/wine/orange-wine/',
        'vermouth': 'https://www.decantalo.com/uk/en/wine/vermouth/'
    }

    for wine_type, wine_type_url in wine_type_urls.items():
        driver.get(wine_type_url)

        listing_urls = []
        while True:
            listings = driver.find_elements(
                By.XPATH,
                '//h3[contains(@class,"h3 mb-0 product-title MerriweatherBold")]'
            )
            print(
                "Found " + str(len(listings)) + " wine advs")

            for listing in listings:
                listing_url = listing.find_element(By.XPATH, './/a').get_attribute('href')
                listing_urls.append([wine_type, listing_url])

            next_arrows = driver.find_elements(By.XPATH, '//a[contains(@rel,"next")]')
            if len(next_arrows):
                next_arrow = next_arrows[0]
                if next_arrow.is_enabled():
                    # We need to wait a little, as the page takes time to load (try setting the wait to 0 and see what happens!)
                    time.sleep(3)
                    next_arrow.click()
                else:
                    break

    with open(listing_urls_path, 'w') as f:
        json.dump(listing_urls, f, indent=4)
else:
    listing_urls = json.load(
        open(listing_urls_path))


def get_name(soup):
    title = soup.find(
        "h1",
        class_="h1 color-title text-center text-md-left MerriweatherBold text-capitalize title-product"
    ).text

    title = re.sub('\s+', ' ', title)
    return title


def get_volume(soup):
    try:
        for elem in soup.findAll('span', class_='value data_features SourceSansProSemiBold d-flex align-items-center pl-1'):
            elem_text = elem.text
            if 'cl' in elem_text:
                return float(elem_text.split(' ')[0])
        return None
    except AttributeError:
        return None


def get_year(soup):
    try:
        year = soup.find(
            "span",
            class_="px-1 choose_comb selector-combinaciones SourceSansProRegular--mobile SourceSansProBold--desktop"
        ).text
        year = re.sub('\n', '', year)
        return year
    except (AttributeError, ValueError):
        # Some listings don't specify the year
        return None


def get_price(soup):
    try:
        price_per_bottle = soup.find(
            "span",
            class_="d-block text-right col-6 col-md-8 p-md-0 pr-md-2 SourceSansProBold color-normal-b current-price-display price format-decimal"
        ).text.split('\n')[0].replace('£', '').replace(',', '')
        return float(price_per_bottle)
    except AttributeError:
        return 'out of stock'


def get_abv(soup):
    try:
        abv = (
            soup
            .find("span", class_="value data_features SourceSansProSemiBold d-flex align-items-center pl-1")
            .text
            .strip().replace('%', '')
        )
        return float(abv)
    except (ValueError, AttributeError):
        return None


def get_size(soup):
    for elem in soup.findAll('span', class_='value data_features SourceSansProSemiBold d-flex align-items-center pl-1'):
        elem_text = elem.text
        if 'cl' in elem_text:
            try:
                return float(elem_text.split(' ')[0])
            except ValueError:
                continue


def get_country(soup):
    try:
        country = soup.find('span', class_="image_do mr-1").find('img')['alt']
        return country
    except:
        return None


def get_reviews(driver, listing_url):
    # Reviews from the page are displayed using JS. We need to use selenium to run the script to get the reviews
    driver.get(listing_url)

    while True:
        try:
            reviews = driver.find_element(
                By.XPATH,
                '//span[contains(@class,"total_reviews")]',
            ).text
            break
        except NoSuchElementException:
            # wait for the reviews to show up
            time.sleep(0.2)

    rating = float(reviews.split('/')[0].replace('(', ''))
    num_reviews = int(reviews.split(' ')[-2])

    return rating, num_reviews


# driver = webdriver.Chrome()

wine_info_all = []
for wine_type, listing_url in tqdm(listing_urls[3225:]):
    listing_page = requests.get(listing_url)
    soup = BeautifulSoup(listing_page.content, 'html.parser')

    wine_info = {}
    try:
        wine_info['name'] = get_name(soup)
    except:
        # There are pages that are not wine listings, e.g:
        # https://www.decantalo.com/uk/en/world-of-wine.html#/1-volume-75_cl/111-year-2018
        continue

    # rating, num_reviews = get_reviews(driver, listing_url)
    # wine_info['rating'] = rating
    # wine_info['num_review'] = num_reviews

    wine_info['wine_type'] = wine_type
    # wine_info['size (cL)'] = get_size(soup)
    # wine_info['price'] = get_price(soup)
    # wine_info['country'] = get_country(soup)
    # wine_info['abv'] = get_abv(soup)
    # wine_info['year'] = get_year(soup)
    wine_info['url'] = listing_url

    wine_info_all.append(wine_info)

wine_info_df = pd.DataFrame(wine_info_all).to_clipboard()
wine_info_df.to_csv(export_path, index=False)
