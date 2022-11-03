# %%
import json
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from tqdm import tqdm


# %%
urls = {
    'Red Wine': 'https://www.laithwaites.co.uk/wines/Red-Wine/_/N-1z141we',
    'White Wine': 'https://www.laithwaites.co.uk/wines/White-Wine/_/N-1z141yb',
    'Sparkling': 'https://www.laithwaites.co.uk/wines/Sparkling/_/N-1z141tg',
    'Rose Wine': 'https://www.laithwaites.co.uk/wines/Ros%C3%A9-Wine/_/N-1z141yi',
    'Fortified': 'https://www.laithwaites.co.uk/wines/Fortified/_/N-1z12ly0',
    'Dessert Wine': 'https://www.laithwaites.co.uk/wines/Dessert-Wine/_/N-1z141jk'
}

# %%
driver = Chrome()
listing_urls = []
for winetype,url in urls.items():
    #url = 'https://www.laithwaites.co.uk/wines/White-Wine/_/N-1z141yb'
    driver.get(url)
    time.sleep(0.5)
    try:
        cookie_button = driver.find_element(By.XPATH,'//button[@id="onetrust-accept-btn-handler"]')
        if cookie_button.is_displayed():
            cookie_check = True
    except:
        cookie_check = False
    
    if cookie_check:
        cookie_button.click()

    
    select = Select(driver.find_element(By.XPATH,'//select[@id="numPerPage"]'))
    select.select_by_value('50')

    while True:
        product_wrappers = driver.find_elements(
                By.XPATH,
                '//div[contains(@class, "product-wrapper")]',
            )
        #print(len(product_wrappers))

        for product_wrapper in product_wrappers:
            listing = product_wrapper.find_element(By.XPATH,'.//a')
            listing_urls.append([winetype, listing.get_attribute('href')])
        print(len(listing_urls))
        
        try:
            next_button = driver.find_element(By.XPATH,'//a[@id="nextPage"]')
            if next_button.is_displayed():
                click_next = True
        except:
            click_next = False
        
        if click_next:
            try:
                next_button.click()
            except:
                break
        else:
            print('End of type' + winetype)
            break

# %%
listing_urls_path = Path('./data/url/laithwaites_listings.json')
export_path = './data/scrapped/virginwines_listings.csv'
with open(listing_urls_path, 'w') as f:
        json.dump(listing_urls, f, indent=4)

# %%
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


# %%
def try_catch(web_element):
    try:
        return web_element.text
    except:
        return '0'

# %%
wine_info_all = []
listing_urls_path = Path('./data/url/laithwaites_listings.json')
listing_urls = json.load(open(listing_urls_path))
for winetype,listing_url in tqdm(listing_urls):
    listing_page = requests.get(listing_url)
    soup = BeautifulSoup(listing_page.content, 'html.parser')
    wine_data = {}
    #name
    wine_data['name'] = clean_text_data(try_catch(soup.find('h1', {'class' : 'prod-name'})))
    if wine_data['name'].split(' ')[-1].lower() == 'mix' or wine_data['name'].split(' ')[0].lower() == 'mystery':
        wine_data['Mix Case?'] = 1
    else:
        wine_data['Mix Case?'] = 0
        wine_infor_left = soup.find('div', {'class' : 'col-lg-6 col-sm-6 col-md-6 no-pad-left'}).find_all('li')
        wine_infor_right = soup.find('div', {'class' : 'col-lg-6 col-sm-6 col-md-6 no-pad'}).find_all('li')
        #abv
        wine_data['abv'] = clean_text_data(try_catch(wine_infor_right[0].find('div', {'class' : 'detail-text'}))).split(' ')[0].replace('%', '')
        #year
        wine_data['year'] = wine_data['name'].split(' ')[-1]
        #size
        wine_data['size'] = float(clean_text_data(try_catch(wine_infor_right[2].find('div', {'class' : 'detail-text'}))).split(' ')[0])
        #country
        #print(wine_infor_left)
        for a in wine_infor_left:
            if a.find('span').attrs['class'] == ['pull-left', 'icons', 'country-icon']:
                wine_data['country'] = clean_text_data(
                    try_catch(
                        a.find('div', {'class' : 'detail-text'}).find('a')
                        )
                    )
        #wine_type
        wine_data['wine_type'] = winetype
        #wine_data['wine_type_detail'] = clean_text_data(wine_infor_left[0].find('div', {'class' : 'detail-text'}).text)
        #price
        try:
            wine_data['price'] = float(soup.find('span', {'class' : 'price-per-bottle'}).text.replace('£', ''))
        except:
            wine_data['price'] = None
        #num_review
        wine_data['num_review'] = try_catch(soup.find('span', {'class' : 'no-reviews'})).replace('(', '').replace(')', '').split(' ')[0]
        #rating
        wine_data['rating'] = try_catch(soup.find('span', {'class' : 'rating-score'})).split(' ')[0]
        wine_data['url'] = listing_url
        #print(wine_data)
    wine_info_all.append(wine_data)


# %%
wine_info_all

# %%
df = pd.DataFrame(wine_info_all)

export_path = './data/scrapped/laithwaites_listings.csv'
df.to_csv(export_path, index=False)


