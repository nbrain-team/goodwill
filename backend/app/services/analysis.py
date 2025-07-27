import os
from openai import OpenAI
from dotenv import load_dotenv
import re
from app.services.price_research import price_research

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_auction_item(title: str, image_url: str, description: str = None, all_images: list = None, current_price: str = None) -> tuple[float, str]:
    """
    Analyze an auction item using GPT-4o with all available information and market research
    """
    try:
        # First, conduct market research
        print(f"Conducting market research for: {title}")
        market_data = price_research.research_item_value(title, description)
        
        # Parse current price if available
        current_price_text = current_price if current_price else "Unknown"
        
        # Build the content for analysis
        content_parts = [
            {
                "type": "text", 
                "text": f"""Analyze this auction item with EXTREME attention to detail:

CRITICAL INSTRUCTIONS FOR VALUATION:
1. FIRST LINE MUST BE: A single number representing what someone should pay for this auction RIGHT NOW (e.g., 125.50)
   - This is the CURRENT AUCTION VALUE, not retail price
   - Current bidding price: {current_price_text}
   - If worth less than current price, suggest lower
   - If worth more than current price, suggest what to pay

2. EXTREMELY DETAILED ANALYSIS WITH CITATIONS:

ITEM-BY-ITEM BREAKDOWN (REQUIRED):
- List EVERY visible item with individual values
- Format: "Item 1: [Description] - Value: $XX (Source: eBay sold listing avg)"
- Include items visible in background/partially shown
- Total lot value = sum of all items
- CITE YOUR SOURCES for each value estimate

ITEM IDENTIFICATION:
- Identify ALL items visible in the images (main item + any bonus/additional items)
- Brand, manufacturer, model numbers, series names
- Year/era of manufacture if determinable
- Authenticity indicators
- Reference similar items from market research

DETAILED VISUAL INSPECTION:
- Examine EVERY visible detail in ALL provided images
- Look for: signatures, stamps, markings, labels, tags, stickers
- Note serial numbers, copyright dates, edition information
- Identify materials (metal type, fabric, plastic quality)
- Check for rare variations, errors, or unique features
- Compare condition to sold listings

CONDITION ASSESSMENT:
- Rate condition on standard scale (Mint/Near Mint/Excellent/Very Good/Good/Fair/Poor)
- List ALL visible flaws: scratches, chips, tears, stains, missing parts
- Note any repairs, restorations, or modifications
- Assess completeness (missing accessories, manuals, boxes?)
- Impact of condition on value vs. market comparables

MARKET RESEARCH ANALYSIS:
{_format_detailed_market_research(market_data)}

PRICING JUSTIFICATION:
- Explain WHY you recommend the specific auction value
- Compare to recent eBay sold prices
- Factor in current market demand
- Consider seasonal trends
- Account for condition relative to comparables

INVESTMENT ANALYSIS:
- Resale potential and timeline
- Best platforms to resell (eBay, Etsy, Mercari, etc.)
- Target buyer demographics
- Expected profit margin
- Risks and opportunities

Title: {title}
Current Auction Price: {current_price_text}"""
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
                    "content": """You are an expert auction appraiser who helps buyers determine fair prices at auctions. 

CRITICAL: The FIRST LINE of your response must ALWAYS be a single number - the maximum amount someone should bid/pay for this auction RIGHT NOW. This is NOT the retail value, but what makes sense to pay at auction considering:
- Current market prices from actual sold listings
- Condition relative to comparables
- Resale potential with specific platform recommendations
- Competition from other bidders

You must analyze EVERY item visible in photos, even background items, and provide individual valuations with source citations. Reference specific eBay sold listings, web prices, and market trends. Be extremely detailed and thorough in your analysis."""
                },
                {
                    "role": "user",
                    "content": content_parts
                }
            ],
            max_tokens=4000,  # Doubled from 2000
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

def _format_detailed_market_research(market_data: dict) -> str:
    """
    Format market research data with detailed citations
    """
    research_text = []
    
    # eBay data with specific examples
    if market_data['ebay_data'].get('num_sold', 0) > 0:
        research_text.append(f"\n📊 EBAY SOLD LISTINGS DATA:")
        research_text.append(f"- Found {market_data['ebay_data']['num_sold']} sold listings")
        research_text.append(f"- Price range: {market_data['ebay_data']['price_range']}")
        research_text.append(f"- Average sold price: ${market_data['ebay_data']['average_price']:.2f}")
        
        # Recent sales with details
        if market_data['ebay_data'].get('recent_sales'):
            research_text.append("\nRECENT EBAY SALES:")
            for i, sale in enumerate(market_data['ebay_data']['recent_sales'][:5], 1):
                research_text.append(f"{i}. ${sale['price']:.2f} - {sale['title'][:80]}...")
                if sale.get('condition'):
                    research_text.append(f"   Condition: {sale['condition']}")
                if sale.get('sold_date'):
                    research_text.append(f"   Sold: {sale['sold_date']}")
    
    # Web search results with sources
    if market_data['web_results']:
        research_text.append(f"\n🌐 WEB PRICING RESEARCH:")
        for i, result in enumerate(market_data['web_results'][:5], 1):
            if '$' in result.get('snippet', ''):
                research_text.append(f"{i}. {result['title'][:60]}...")
                research_text.append(f"   Source: {result['link']}")
                research_text.append(f"   Info: {result['snippet'][:150]}...")
    
    # Forum discussions
    if market_data['forum_discussions']:
        research_text.append(f"\n💬 COLLECTOR FORUM INSIGHTS:")
        for i, discussion in enumerate(market_data['forum_discussions'][:3], 1):
            research_text.append(f"{i}. {discussion['title'][:60]}...")
            research_text.append(f"   Source: {discussion['link']}")
            research_text.append(f"   Discussion: {discussion['snippet'][:150]}...")
    
    # Price summary with confidence
    if market_data['price_summary'].get('status') == 'success':
        research_text.append(f"\n💰 PRICE ANALYSIS SUMMARY:")
        research_text.append(f"- Market value range: {market_data['price_summary']['estimated_value_range']}")
        research_text.append(f"- Average market value: ${market_data['price_summary']['average_value']:.2f}")
        research_text.append(f"- Confidence level: {market_data['price_summary']['confidence'].upper()}")
        research_text.append(f"- Based on {market_data['price_summary']['data_points']} data points")
    
    # Recommendations
    if market_data['recommendations']:
        research_text.append(f"\n🎯 SELLING RECOMMENDATIONS:")
        research_text.append(f"- Suggested list price: {market_data['recommendations']['list_price']}")
        research_text.append(f"- Accept offers above: {market_data['recommendations']['accept_offers_above']}")
        research_text.append(f"- Quick sale price: {market_data['recommendations']['quick_sale_price']}")
        research_text.append(f"- Strategy: {market_data['recommendations']['strategy']}")
    
    return '\n'.join(research_text) if research_text else "No market data available" 