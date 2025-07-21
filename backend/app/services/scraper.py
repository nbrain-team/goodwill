import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import time

def get_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        # Scroll to load all items
        for _ in range(5): # Adjust scroll count as needed
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
        html = page.content()
        browser.close()
        return html

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    products = soup.find_all('div', class_='product')
    
    scraped_data = []
    for product in products:
        try:
            title = product.find('a', class_='product-name').text.strip()
            price = product.find('span', class_='product-price').text.strip()
            image_url = product.find('img')['src']
            auction_url = "https://shopgoodwill.com" + product.find('a', class_='product-name')['href']
            
            scraped_data.append({
                'title': title,
                'price': price,
                'image_url': image_url,
                'auction_url': auction_url
            })
        except AttributeError:
            # Skip product if any attribute is not found
            continue
            
    return scraped_data

def save_to_csv(data, filename='goodwill_auctions.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    url = "https://shopgoodwill.com/categories/collectibles?p=1"
    html = get_html(url)
    data = parse_html(html)
    return data

if __name__ == "__main__":
    scraped_data = main()
    save_to_csv(scraped_data) 