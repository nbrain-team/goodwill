from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re
import json

def scrape_auction_details(auction_url: str) -> dict:
    """
    Scrape detailed information from an individual auction page
    Returns dict with: title, description, all_images, current_price, num_bids, seller, condition, etc.
    """
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            response = page.goto(auction_url, wait_until='domcontentloaded', timeout=60000)
            if response.status != 200:
                return None
                
            # Wait for content to load
            page.wait_for_timeout(5000)
            
            # Get the HTML
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            data = {}
            
            # Title - look for h1 or h2
            title_elem = soup.find('h1')
            if title_elem:
                data['title'] = title_elem.text.strip()
            
            # Current price/bid
            price_elem = soup.find('h2', class_='mb-0')
            if price_elem:
                data['current_price'] = price_elem.text.strip()
            
            # Number of bids
            bid_info = soup.find(text=re.compile(r'Number of Bids:'))
            if bid_info:
                bid_parent = bid_info.parent.parent
                bid_value = bid_parent.find_next('td')
                if bid_value:
                    data['num_bids'] = bid_value.text.strip()
            
            # Extract all images
            images = []
            
            # Main image carousel
            carousel_images = soup.find_all('img', class_='d-block')
            for img in carousel_images:
                src = img.get('src', '')
                if src and 'shopgoodwillimages' in src:
                    images.append(src)
            
            # Thumbnail images
            thumb_images = soup.find_all('img', class_='img-thumbnail')
            for img in thumb_images:
                src = img.get('src', '')
                if src and 'shopgoodwillimages' in src:
                    # Convert thumbnail to full size by removing size parameters
                    full_src = re.sub(r'/w_\d+/', '/', src)
                    images.append(full_src)
            
            # Any other product images
            all_imgs = soup.find_all('img')
            for img in all_imgs:
                src = img.get('src', '')
                if src and 'shopgoodwillimages' in src and 'Items' in src:
                    if not any(src in existing for existing in images):
                        images.append(src)
            
            data['all_images'] = list(set(images))  # Remove duplicates
            
            # Full description - look for the Item Description section
            desc_header = soup.find('h3', text='Item Description')
            if desc_header:
                desc_div = desc_header.find_next_sibling('div')
                if desc_div:
                    # Get all text including HTML structure
                    data['description_html'] = str(desc_div)
                    # Get plain text version
                    data['description_text'] = desc_div.get_text(separator='\n', strip=True)
            
            # Item condition and other details from table
            item_details = {}
            table_rows = soup.find_all('tr')
            for row in table_rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.text.strip().replace(':', '')
                    value = td.text.strip()
                    item_details[key] = value
            
            data['item_details'] = item_details
            
            # Seller information
            seller_elem = soup.find(text='Seller:')
            if seller_elem:
                seller_value = seller_elem.parent.find_next('td')
                if seller_value:
                    data['seller'] = seller_value.text.strip()
            
            browser.close()
            return data
            
        except Exception as e:
            print(f"Error scraping auction details: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    # Test with a sample URL
    test_url = "https://shopgoodwill.com/item/236806396"
    result = scrape_auction_details(test_url)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Failed to scrape auction details") 