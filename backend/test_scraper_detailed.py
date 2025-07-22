from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json

def test_scraper_detailed():
    url = "https://shopgoodwill.com/categories/collectibles?p=1"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = context.new_page()
        
        print(f"Navigating to: {url}")
        response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
        print(f"Response status: {response.status}")
        
        # Wait for content to load
        page.wait_for_timeout(5000)
        
        # Try to extract product data using Playwright
        print("\nExtracting product information...")
        
        products = []
        
        # Find all item links
        item_links = page.query_selector_all('a[href*="/item/"]')
        print(f"Found {len(item_links)} item links")
        
        # For each link, try to find its parent container and extract data
        for i, link in enumerate(item_links[:5]):  # Just check first 5
            try:
                href = link.get_attribute('href')
                parent = link.evaluate('el => el.closest("div")')
                
                # Try to extract data from the parent container
                product_data = link.evaluate('''el => {
                    const container = el.closest('div[class*="item"]') || el.parentElement;
                    
                    // Try to find price
                    const priceEl = container.querySelector('[class*="price"], .price, span:has-text("$")');
                    const price = priceEl ? priceEl.textContent.trim() : 'No price';
                    
                    // Try to find title
                    const titleEl = container.querySelector('h3, h4, [class*="title"], [class*="name"]');
                    const title = titleEl ? titleEl.textContent.trim() : el.textContent.trim();
                    
                    // Try to find image
                    const imgEl = container.querySelector('img');
                    const imgSrc = imgEl ? imgEl.src : 'No image';
                    
                    return {
                        title: title,
                        price: price,
                        image: imgSrc,
                        href: el.href
                    };
                }''')
                
                if product_data:
                    products.append(product_data)
                    print(f"\nProduct {i+1}:")
                    print(f"  Title: {product_data.get('title', 'N/A')[:50]}...")
                    print(f"  Price: {product_data.get('price', 'N/A')}")
                    print(f"  Link: {product_data.get('href', 'N/A')}")
                    
            except Exception as e:
                print(f"Error extracting product {i+1}: {e}")
        
        # Also get raw HTML for analysis
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for any element containing price
        price_elements = soup.find_all(text=lambda text: text and '$' in text)
        print(f"\nFound {len(price_elements)} elements with '$' in text")
        if price_elements:
            print("Sample prices:", [p.strip() for p in price_elements[:5] if p.strip()])
        
        browser.close()
        
        return products

if __name__ == "__main__":
    products = test_scraper_detailed()
    print(f"\nTotal products extracted: {len(products)}") 