import os
from openai import OpenAI
from dotenv import load_dotenv
import re
from app.services.price_research import price_research

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_auction_item(title: str, image_url: str, description: str = None, all_images: list = None) -> tuple[float, str]:
    """
    Analyze an auction item using GPT-4o with all available information and market research
    """
    try:
        # First, conduct market research
        print(f"Conducting market research for: {title}")
        market_data = price_research.research_item_value(title, description)
        
        # Build the content for analysis
        content_parts = [
            {
                "type": "text", 
                "text": f"""Analyze this auction item and provide:
1. FIRST LINE: A single number representing the estimated fair market value in USD (e.g., 125.50)
2. SUBSEQUENT LINES: A detailed analysis including:
   - Item identification (what it is, brand/manufacturer if applicable)
   - Condition assessment based on the images
   - Key factors affecting value
   - Market demand insights
   - Any hidden value or special features you notice in the images that may not be mentioned in the description
   
Based on my market research:
{_format_market_research(market_data)}

Pay special attention to:
- Details visible in images that might not be in the description
- Markings, signatures, labels, or stamps
- Materials and construction quality
- Any collectible or rare aspects
- Condition issues or positive attributes

Title: {title}"""
            }
        ]
        
        # Add description if available
        if description:
            content_parts[0]["text"] += f"\n\nDescription from seller:\n{description[:1000]}..."  # Limit description length
        
        # Add main image
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })
        
        # Add additional images if available (limit to 5 to avoid token limits)
        if all_images:
            for img_url in all_images[:5]:
                if img_url != image_url:  # Don't duplicate the main image
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": img_url}
                    })
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert appraiser specializing in collectibles and auction items. You have access to current market data and must provide accurate valuations based on actual sales data. Always consider the market research provided when estimating value."
                },
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            max_tokens=1000,
        )
        
        content = response.choices[0].message.content.strip()
        lines = content.split('\n')
        
        # Extract the numeric value from the first line
        estimated_value = None
        value_line = lines[0] if lines else ""
        
        # Try to find a number in the first line
        number_match = re.search(r'(\d+\.?\d*)', value_line)
        if number_match:
            try:
                estimated_value = float(number_match.group(1))
            except ValueError:
                pass
        
        # If we couldn't find a value, use market research average
        if estimated_value is None and market_data['price_summary'].get('average_value'):
            estimated_value = market_data['price_summary']['average_value']
        
        # If still no value, use a default
        if estimated_value is None:
            estimated_value = 25.0  # Default fallback value
            
        # Get the analysis (everything after the first line, or the entire content if no clear separation)
        if len(lines) > 1:
            analysis = "\n".join(lines[1:]).strip()
        else:
            analysis = content
            
        # Append market insights to analysis
        if market_data['market_insights']:
            analysis += "\n\n📊 Market Research Insights:\n" + "\n".join(f"• {insight}" for insight in market_data['market_insights'])
        
        if market_data['recommendations']:
            analysis += f"\n\n💰 Pricing Recommendations:\n"
            analysis += f"• List Price: {market_data['recommendations']['list_price']}\n"
            analysis += f"• Accept Offers Above: {market_data['recommendations']['accept_offers_above']}\n"
            analysis += f"• Quick Sale Price: {market_data['recommendations']['quick_sale_price']}\n"
            analysis += f"• Strategy: {market_data['recommendations']['strategy']}"
        
        # Ensure we have some analysis text
        if not analysis or analysis == str(estimated_value):
            analysis = f"Collectible item: {title}. Estimated value based on general market conditions."
        
        print(f"Analyzed '{title}': Value=${estimated_value}, Analysis length={len(analysis)}, Images analyzed={1 + len(all_images) if all_images else 1}")
        
        return estimated_value, analysis
        
    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        # Return reasonable defaults
        return 25.0, f"Analysis unavailable. Error: {str(e)}"

def _format_market_research(market_data: dict) -> str:
    """
    Format market research data for the AI prompt
    """
    research_text = []
    
    # eBay data
    if market_data['ebay_data'].get('num_sold', 0) > 0:
        research_text.append(f"- eBay sold listings: {market_data['ebay_data']['num_sold']} items")
        research_text.append(f"- eBay price range: {market_data['ebay_data']['price_range']}")
        research_text.append(f"- eBay average: ${market_data['ebay_data']['average_price']:.2f}")
        
        # Recent sales examples
        if market_data['ebay_data'].get('recent_sales'):
            research_text.append("- Recent eBay sales:")
            for sale in market_data['ebay_data']['recent_sales'][:3]:
                research_text.append(f"  • ${sale['price']:.2f} - {sale['title'][:60]}...")
    
    # Price summary
    if market_data['price_summary'].get('status') == 'success':
        research_text.append(f"- Market value range: {market_data['price_summary']['estimated_value_range']}")
        research_text.append(f"- Confidence level: {market_data['price_summary']['confidence']}")
        research_text.append(f"- Data points analyzed: {market_data['price_summary']['data_points']}")
    
    # Key web results
    if market_data['web_results']:
        research_text.append("- Relevant pricing information found:")
        for result in market_data['web_results'][:3]:
            if '$' in result.get('snippet', ''):
                research_text.append(f"  • {result['snippet'][:100]}...")
    
    return '\n'.join(research_text) if research_text else "No market data available" 