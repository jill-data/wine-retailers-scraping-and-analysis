# Wine retailer data scraping and analysis

Scrape data from wine retailers' websites and analyse their offerings

## Contributions

- [@FanXia1227](https://github.com/FanXia1227): Market research, report writing.
- [@jill-data](https://github.com/jill-data): Web scraping (3 retailers), analysis and visualisation, code and data merging, writing (final report, README).
- [@SoumyaO](https://github.com/SoumyaO): Data cleaning & EDA (2 retailers), report writing, analysis and visualisation.
- [@Wayne599](https://github.com/Wayne599): Web scraping (1 retailer) and EDA (1 retailer), data cleaning.

## Summary

To establish a preliminary understanding of the wine market, the analytics team
investigated online wine consumer purchasing behaviour through the operations of current
competitors in the market. The reasons for online wine shopping can be categorised into
three aspects: cheaper prices, detailed product descriptions, and more options available
in online shops. In this case, we have determined that our analysis of the wine market
would be based on information surrounding wine features (including wine type, country,
year, and ABV), price (for a bottle of 75cL), and reviews (including the number of
reviews and scores) which would be collected from competitors’ websites for analysis.

**Key objectives**:

- (1) identify the most popular wines sold across the companies and the key features of
best-selling wines
- (2) identify the most frequent price ranges for wines in order to learn product
portfolio and business focus

We have utilised the Python libraries BeautifulSoup and Selenium to collect data from
the competitor websites.

**Websites scraped**:

- <https://www.laithwaites.co.uk/wines>
- <https://www.virginwines.co.uk/>
- <https://www.decantalo.com/uk/en/wine/>
- <https://groceries.morrisons.com/browse/beer-wines-spirits-103120/wine-champagne-176432>

## Findings

Findings can be found in this [report](./Final%20deliverables/Group5%20SMM750%20.pdf)

## Summary of web scraping challenges and solutions

### Anti scraping

- Retailers identify and block requests made programatically -> Use the headers obtained
  from a manual browsing session.
- Retailers intentionally include special characters in the names of the class elements.

-> Given the cost-reward trade-off, we chose another retailer.

### Varying web page structures

- Different ways of navigating to the next listing page -> Write custom scrapers.
- Inconsistent layouts of listings -> Keyword matching from bottom of the page.
- The same information is specified in different places -> Very specific text matching.
- Unreliable navigation buttongs -> Navigate using URLs instead.
- Dynamic webpages -> Use Selenium, but this significantly slowed down the process.

### Website crashes

- Sudden website crashes -> Set up checkpoints.

### Poor data quality

- Different spelling of product information: (‘mL’, ‘ml’, ‘cl.’, ‘Magnum’ (which is
1.5L)) -> handle the unit text and convert them to ‘cl’ and converted Magnum to 150cl.
- Wine type not consistent or not listed in the product page -> Started
a browsing session for each wine type, and relied on the product classification
being correct.
- Incorrect product classification (e.g., candles being classified as wine bottles) ->
Keyword-matched the product name to identify such products and excluded them.
- Missing information: Where possible, we tried to look in other parts of the websites
for the information (in the case of Morrisons).
- Unnecessary spaces or special characters in the product attributes -> Applied string
processing methods to address them.

Dealing with the above issues required a significant number of trials and errors due to
the sheer number of edge cases. Overall, we have found that saving the URL with the
listing helped us quickly identify and analyse the anomalies, and we could avoid
rerunning the scrapping from the beginning by setting up checkpoints during the
scrapping run.

## Scripts and notebooks

Scripts and notebooks can be found in this [folder](./Final%20deliverables/code/)
