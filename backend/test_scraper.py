from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def test_scraper():
    url = "https://shopgoodwill.com/categories/collectibles?p=1"
    
    with sync_playwright() as p:
        # Try with different browser settings
        browser = p.chromium.launch(
            headless=True,  # Run headless
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = context.new_page()
        
        print(f"Navigating to: {url}")
        try:
            # Don't wait for networkidle, just load
            response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
            print(f"Response status: {response.status if response else 'No response'}")
            
            # Wait a bit for JavaScript to render
            print("Waiting for page to render...")
            time.sleep(10)
            
            # Try to find products directly in the page
            print("\nTrying to find products using Playwright selectors:")
            
            # Common product selectors
            selectors_to_try = [
                'div.product',
                'div.product-item',
                'div.item',
                'article.product',
                'div[class*="product"]',
                'div[class*="item"]',
                'a[href*="/item/"]'
            ]
            
            for selector in selectors_to_try:
                elements = page.query_selector_all(selector)
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    
                    # Get details from first element
                    if elements and selector == 'a[href*="/item/"]':
                        first_link = elements[0]
                        href = first_link.get_attribute('href')
                        text = first_link.text_content()
                        print(f"  Sample link href: {href}")
                        print(f"  Sample link text: {text[:100]}")
            
            # Get the HTML for BeautifulSoup parsing
            html = page.content()
            
            # Save HTML to file for inspection
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("\nSaved page content to page_content.html for inspection")
            
        except Exception as e:
            print(f"Error loading page: {e}")
            
        browser.close()

if __name__ == "__main__":
    test_scraper() 