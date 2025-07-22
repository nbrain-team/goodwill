import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv
import json

load_dotenv()

class WebSearchService:
    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.base_url = "https://google.serper.dev"
        
    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform a web search using Serper API
        """
        if not self.serper_api_key:
            print("Warning: SERPER_API_KEY not set")
            return []
            
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': query,
            'num': num_results
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract organic search results
            for result in data.get('organic', []):
                results.append({
                    'title': result.get('title'),
                    'link': result.get('link'),
                    'snippet': result.get('snippet'),
                    'position': result.get('position')
                })
                
            return results
            
        except Exception as e:
            print(f"Error performing web search: {e}")
            return []
    
    def search_shopping(self, query: str) -> List[Dict]:
        """
        Search for shopping/price information
        """
        if not self.serper_api_key:
            return []
            
        headers = {
            'X-API-KEY': self.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': f"{query} price sold",
            'num': 20,
            'shopping': True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/shopping",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract shopping results
            for result in data.get('shopping', []):
                results.append({
                    'title': result.get('title'),
                    'price': result.get('price'),
                    'source': result.get('source'),
                    'link': result.get('link'),
                    'rating': result.get('rating'),
                    'reviews': result.get('reviews')
                })
                
            return results
            
        except Exception as e:
            print(f"Error performing shopping search: {e}")
            return []
    
    def search_ebay_sold(self, query: str) -> List[Dict]:
        """
        Search specifically for eBay sold listings
        """
        # Add "site:ebay.com sold" to get eBay results
        ebay_query = f"site:ebay.com {query} sold completed"
        results = self.search(ebay_query, num_results=20)
        
        # Filter for sold listings
        sold_results = []
        for result in results:
            if 'sold' in result.get('title', '').lower() or 'sold' in result.get('snippet', '').lower():
                sold_results.append(result)
                
        return sold_results

# Singleton instance
web_search = WebSearchService() 