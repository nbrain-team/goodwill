import pandas as pd
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import time
import re

def get_html(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        
        # Wait for products to load - wait for item containers
        page.wait_for_selector('div[class*="item-col"]', timeout=30000)
        
        # Additional wait to ensure all content is loaded
        page.wait_for_timeout(5000)
        
        html = page.content()
        browser.close()
        return html

def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Updated selectors based on the actual website structure
    products = soup.find_all('div', class_=re.compile(r'item-col'))
    
    scraped_data = []
    for product in products:
        try:
            # Find the link element
            link_elem = product.find('a', href=True)
            if not link_elem:
                continue
                
            # Extract URL
            auction_url = link_elem.get('href', '')
            if not auction_url.startswith('http'):
                auction_url = f"https://shopgoodwill.com{auction_url}"
            
            # Extract title - look for various possible locations
            title = ''
            title_elem = product.find(class_=re.compile(r'title|name|feat-item_name'))
            if title_elem:
                title = title_elem.text.strip()
            else:
                # Try to get title from image alt text
                img_elem = product.find('img')
                if img_elem and img_elem.get('alt'):
                    title = img_elem.get('alt', '').strip()
            
            if not title:
                continue
                
            # Extract price
            price = ''
            price_elem = product.find(class_=re.compile(r'price|feat-item_price'))
            if price_elem:
                price = price_elem.text.strip()
            else:
                # Look for any text containing $
                price_text = product.find(text=re.compile(r'\$[\d,]+\.?\d*'))
                if price_text:
                    price = price_text.strip()
            
            # Extract image URL
            image_url = ''
            img_elem = product.find('img')
            if img_elem:
                image_url = img_elem.get('src', '')
                if not image_url.startswith('http'):
                    image_url = f"https://shopgoodwill.com{image_url}"
            
            # Only add if we have at least title and URL
            if title and auction_url:
                scraped_data.append({
                    'title': title,
                    'price': price or '$0.00',
                    'image_url': image_url,
                    'auction_url': auction_url
                })
                
        except Exception as e:
            print(f"Error parsing product: {e}")
            continue
            
    return scraped_data

def save_to_csv(data, filename='goodwill_auctions.csv'):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

def main():
    url = "https://shopgoodwill.com/categories/collectibles?p=1"
    print(f"Scraping {url}...")
    html = get_html(url)
    data = parse_html(html)
    print(f"Found {len(data)} products")
    return data

if __name__ == "__main__":
    scraped_data = main()
    if scraped_data:
        save_to_csv(scraped_data)
        print("Sample data:")
        for item in scraped_data[:3]:
            print(f"- {item['title']}: {item['price']}") 