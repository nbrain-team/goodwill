import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
import base64
from datetime import datetime, timedelta

load_dotenv()

class eBayAPI:
    def __init__(self):
        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")
        self.base_url = "https://api.ebay.com"
        self.token = None
        self.token_expiry = None
        
    def _get_access_token(self):
        """
        Get OAuth token for eBay API
        """
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
            
        if not self.client_id or not self.client_secret:
            print("Warning: eBay API credentials not set")
            return None
            
        # Create base64 encoded credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_credentials}'
        }
        
        data = {
            'grant_type': 'client_credentials',
            'scope': 'https://api.ebay.com/oauth/api_scope'
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/identity/v1/oauth2/token",
                headers=headers,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data['access_token']
            # Set expiry 5 minutes before actual expiry
            expires_in = token_data.get('expires_in', 7200)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            
            return self.token
            
        except Exception as e:
            print(f"Error getting eBay access token: {e}")
            return None
    
    def search_completed_items(self, query: str, category_id: Optional[str] = None) -> List[Dict]:
        """
        Search for completed/sold items on eBay
        """
        token = self._get_access_token()
        if not token:
            return []
            
        headers = {
            'Authorization': f'Bearer {token}',
            'X-EBAY-C-MARKETPLACE-ID': 'EBAY_US'
        }
        
        # Build query parameters
        params = {
            'q': query,
            'limit': 50,
            'filter': 'buyingOptions:{FIXED_PRICE|AUCTION},conditions:{NEW|USED|UNSPECIFIED}',
            'sort': 'endDate'
        }
        
        if category_id:
            params['category_ids'] = category_id
            
        try:
            # Search completed items
            response = requests.get(
                f"{self.base_url}/buy/browse/v1/item_summary/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('itemSummaries', []):
                # Only include sold items
                if item.get('itemEndDate'):
                    results.append({
                        'title': item.get('title'),
                        'price': float(item.get('price', {}).get('value', 0)),
                        'currency': item.get('price', {}).get('currency', 'USD'),
                        'condition': item.get('condition'),
                        'sold_date': item.get('itemEndDate'),
                        'link': item.get('itemWebUrl'),
                        'image': item.get('image', {}).get('imageUrl'),
                        'seller': item.get('seller', {}).get('username'),
                        'location': item.get('itemLocation', {}).get('country')
                    })
                    
            return results
            
        except Exception as e:
            print(f"Error searching eBay completed items: {e}")
            return []
    
    def get_sold_prices_stats(self, query: str) -> Dict:
        """
        Get statistics on sold prices for an item
        """
        sold_items = self.search_completed_items(query)
        
        if not sold_items:
            return {
                'average_price': 0,
                'min_price': 0,
                'max_price': 0,
                'num_sold': 0,
                'price_range': "No data available"
            }
            
        prices = [item['price'] for item in sold_items if item['price'] > 0]
        
        if not prices:
            return {
                'average_price': 0,
                'min_price': 0,
                'max_price': 0,
                'num_sold': 0,
                'price_range': "No price data"
            }
            
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        return {
            'average_price': round(avg_price, 2),
            'min_price': min_price,
            'max_price': max_price,
            'num_sold': len(prices),
            'price_range': f"${min_price:,.2f} - ${max_price:,.2f}",
            'recent_sales': sold_items[:10]  # Last 10 sales
        }

# Singleton instance
ebay_api = eBayAPI() 