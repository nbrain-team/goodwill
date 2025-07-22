import os
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_auction_item(title: str, image_url: str) -> tuple[float, str]:
    """
    Analyze an auction item using GPT-4o and return estimated value and analysis
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert appraiser specializing in collectibles and auction items. You must ALWAYS provide a numeric estimated value in USD."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": f"""Analyze this auction item and provide:
1. FIRST LINE: A single number representing the estimated fair market value in USD (e.g., 125.50)
2. SUBSEQUENT LINES: A detailed analysis including:
   - Item identification (what it is, brand/manufacturer if applicable)
   - Condition assessment based on the image
   - Key factors affecting value
   - Market demand insights
   
If you cannot determine an exact value, provide your best estimate based on similar items.
The item title is: {title}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
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
        
        # If we couldn't find a value in the first line, search the entire response
        if estimated_value is None:
            all_numbers = re.findall(r'\$?(\d+\.?\d*)', content)
            if all_numbers:
                # Take the first reasonable number (between 1 and 10000)
                for num_str in all_numbers:
                    try:
                        num = float(num_str)
                        if 1 <= num <= 10000:
                            estimated_value = num
                            break
                    except ValueError:
                        continue
        
        # If still no value, use a default
        if estimated_value is None:
            estimated_value = 25.0  # Default fallback value
            
        # Get the analysis (everything after the first line, or the entire content if no clear separation)
        if len(lines) > 1:
            analysis = "\n".join(lines[1:]).strip()
        else:
            analysis = content
            
        # Ensure we have some analysis text
        if not analysis or analysis == str(estimated_value):
            analysis = f"Collectible item: {title}. Estimated value based on general market conditions."
        
        print(f"Analyzed '{title}': Value=${estimated_value}, Analysis length={len(analysis)}")
        
        return estimated_value, analysis
        
    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        # Return reasonable defaults
        return 25.0, f"Analysis unavailable. Error: {str(e)}" 