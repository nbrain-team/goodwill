import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_auction_item(title: str, image_url: str) -> (float, str):
    """
    Analyzes an auction item using GPT-4o and returns an estimated value and analysis.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Please analyze this auction item. Based on the title and image, what is its estimated fair market value? Provide only a single number for the value (e.g., 125.50). Also, provide a brief analysis of the item, including its name, any notable features, and your reasoning for the valuation. The title is: {title}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        
        content = response.choices[0].message.content
        
        # Extract value and analysis
        lines = content.strip().split('\n')
        estimated_value = float(lines[0])
        analysis = "\n".join(lines[1:]).strip()
        
        return estimated_value, analysis

    except Exception as e:
        print(f"An error occurred during OpenAI API call: {e}")
        return None, "Error during analysis." 