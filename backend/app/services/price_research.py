from typing import Dict, List, Optional
import re
from app.services.web_search import web_search
from app.services.ebay_api import ebay_api

class PriceResearchService:
    def __init__(self):
        self.sources = {
            'ebay': True,
            'web_search': True,
            'forums': True
        }
    
    def research_item_value(self, title: str, description: str = None) -> Dict:
        """
        Comprehensive price research across multiple sources
        """
        research_data = {
            'item_name': title,
            'ebay_data': {},
            'web_results': [],
            'forum_discussions': [],
            'price_summary': {},
            'market_insights': [],
            'recommendations': {}
        }
        
        # Clean up the title for better search results
        search_query = self._clean_search_query(title)
        
        # 1. Get eBay sold listings data
        if self.sources['ebay']:
            ebay_stats = ebay_api.get_sold_prices_stats(search_query)
            research_data['ebay_data'] = ebay_stats
            
            if ebay_stats['num_sold'] > 0:
                research_data['market_insights'].append(
                    f"Found {ebay_stats['num_sold']} sold listings on eBay"
                )
                research_data['market_insights'].append(
                    f"eBay price range: {ebay_stats['price_range']}"
                )
        
        # 2. General web search for pricing
        if self.sources['web_search']:
            # Search for general pricing information
            price_results = web_search.search(f"{search_query} price value worth")
            research_data['web_results'] = price_results[:5]
            
            # Search for specific marketplaces
            marketplace_searches = [
                f"{search_query} site:etsy.com sold",
                f"{search_query} site:mercari.com sold",
                f"{search_query} site:amazon.com price"
            ]
            
            for marketplace_query in marketplace_searches:
                results = web_search.search(marketplace_query, num_results=3)
                research_data['web_results'].extend(results)
        
        # 3. Search forums and collector communities
        if self.sources['forums']:
            forum_searches = [
                f"{search_query} site:reddit.com value price",
                f"{search_query} site:collectorsweekly.com",
                f"{search_query} forum discussion price"
            ]
            
            for forum_query in forum_searches:
                results = web_search.search(forum_query, num_results=3)
                research_data['forum_discussions'].extend(results)
        
        # 4. Extract price mentions from all results
        all_prices = self._extract_prices_from_results(research_data)
        
        # 5. Generate price summary
        research_data['price_summary'] = self._generate_price_summary(all_prices, ebay_stats)
        
        # 6. Generate recommendations
        research_data['recommendations'] = self._generate_recommendations(
            research_data['price_summary'],
            title,
            description
        )
        
        return research_data
    
    def _clean_search_query(self, title: str) -> str:
        """
        Clean up title for better search results
        """
        # Remove common words that might interfere with search
        stop_words = ['lot', 'bundle', 'collection', 'vintage', 'rare', 'new', 'used']
        
        # Extract key terms (brand names, model numbers)
        words = title.split()
        important_words = []
        
        for word in words:
            # Keep brand names, model numbers, and significant words
            if (len(word) > 3 and word.lower() not in stop_words) or \
               any(char.isdigit() for char in word) or \
               word[0].isupper():
                important_words.append(word)
        
        # Limit to most important terms
        return ' '.join(important_words[:5])
    
    def _extract_prices_from_results(self, research_data: Dict) -> List[float]:
        """
        Extract price mentions from all search results
        """
        prices = []
        
        # Extract from eBay data
        if research_data['ebay_data'].get('recent_sales'):
            for sale in research_data['ebay_data']['recent_sales']:
                if sale.get('price'):
                    prices.append(sale['price'])
        
        # Extract from web results and forums
        all_text = []
        for result in research_data['web_results'] + research_data['forum_discussions']:
            all_text.append(result.get('title', ''))
            all_text.append(result.get('snippet', ''))
        
        # Regex to find price patterns
        price_pattern = r'\$([0-9,]+\.?\d*)'
        
        for text in all_text:
            matches = re.findall(price_pattern, text)
            for match in matches:
                try:
                    price = float(match.replace(',', ''))
                    if 1 <= price <= 100000:  # Reasonable price range
                        prices.append(price)
                except:
                    pass
        
        return prices
    
    def _generate_price_summary(self, all_prices: List[float], ebay_stats: Dict) -> Dict:
        """
        Generate comprehensive price summary
        """
        if not all_prices and ebay_stats['num_sold'] == 0:
            return {
                'status': 'limited_data',
                'estimated_value_range': '$25 - $50',
                'confidence': 'low',
                'data_points': 0
            }
        
        # Combine all price data
        if ebay_stats['num_sold'] > 0:
            # Weight eBay data more heavily as it's actual sales
            ebay_weight = min(ebay_stats['num_sold'] * 2, 20)
            weighted_prices = [ebay_stats['average_price']] * ebay_weight
            all_prices.extend(weighted_prices)
        
        if not all_prices:
            return {
                'status': 'no_data',
                'estimated_value_range': 'Unable to determine',
                'confidence': 'none',
                'data_points': 0
            }
        
        # Calculate statistics
        avg_price = sum(all_prices) / len(all_prices)
        min_price = min(all_prices)
        max_price = max(all_prices)
        
        # Calculate reasonable range (remove outliers)
        sorted_prices = sorted(all_prices)
        if len(sorted_prices) > 4:
            # Use 25th to 75th percentile
            lower_quartile = sorted_prices[len(sorted_prices) // 4]
            upper_quartile = sorted_prices[3 * len(sorted_prices) // 4]
        else:
            lower_quartile = min_price
            upper_quartile = max_price
        
        confidence = 'high' if len(all_prices) > 10 else 'medium' if len(all_prices) > 5 else 'low'
        
        return {
            'status': 'success',
            'estimated_value_range': f"${lower_quartile:,.0f} - ${upper_quartile:,.0f}",
            'average_value': round(avg_price, 2),
            'confidence': confidence,
            'data_points': len(set(all_prices)),
            'price_distribution': {
                'min': min_price,
                'max': max_price,
                'average': round(avg_price, 2),
                'lower_quartile': lower_quartile,
                'upper_quartile': upper_quartile
            }
        }
    
    def _generate_recommendations(self, price_summary: Dict, title: str, description: str) -> Dict:
        """
        Generate selling recommendations based on research
        """
        if price_summary['status'] != 'success':
            return {
                'list_price': '$50 - $75',
                'accept_offers_above': '$40',
                'strategy': 'Start with moderate pricing due to limited market data',
                'key_factors': ['Limited comparable sales data', 'Price based on general collectibles market']
            }
        
        avg_value = price_summary['average_value']
        lower_q = price_summary['price_distribution']['lower_quartile']
        upper_q = price_summary['price_distribution']['upper_quartile']
        
        # Determine pricing strategy
        if price_summary['confidence'] == 'high':
            list_price = upper_q * 1.1  # List 10% above upper quartile
            accept_price = avg_value * 0.9  # Accept 90% of average
            strategy = "Price competitively based on strong market data"
        else:
            list_price = upper_q * 1.2  # List 20% above for negotiation room
            accept_price = lower_q * 1.1  # Accept slightly above lower quartile
            strategy = "Allow room for negotiation due to variable market prices"
        
        recommendations = {
            'list_price': f"${list_price:,.0f}",
            'accept_offers_above': f"${accept_price:,.0f}",
            'quick_sale_price': f"${lower_q:,.0f}",
            'strategy': strategy,
            'key_factors': []
        }
        
        # Add relevant factors
        if 'rare' in title.lower() or 'limited' in title.lower():
            recommendations['key_factors'].append("Item appears to be rare/limited edition")
        
        if price_summary['data_points'] > 20:
            recommendations['key_factors'].append(f"Strong market data from {price_summary['data_points']} sales")
        
        if upper_q > lower_q * 2:
            recommendations['key_factors'].append("High price variance - condition is crucial")
        
        return recommendations

# Singleton instance
price_research = PriceResearchService() 