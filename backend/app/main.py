from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from app.database import engine, Base, get_db
from app.models.auction import Auction
from app.services.scraper import main as run_scraper
from app.services.analysis import analyze_auction_item
from app.services.detail_scraper import scrape_auction_details
from app.services.utils import parse_price
from app.services.price_research import price_research

# Create tables
Base.metadata.create_all(bind=engine)

# Add migrations for new columns
with engine.connect() as conn:
    try:
        # Check and add new columns if they don't exist
        columns_to_add = [
            ("is_watchlisted", "BOOLEAN DEFAULT FALSE"),
            ("description", "TEXT"),
            ("all_images", "JSON"),
            ("num_bids", "VARCHAR"),
            ("seller", "VARCHAR"),
            ("item_details", "JSON"),
            ("details_scraped", "BOOLEAN DEFAULT FALSE")
        ]
        
        for column_name, column_type in columns_to_add:
            result = conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='auctions' AND column_name='{column_name}'
            """))
            if not result.fetchone():
                conn.execute(text(f"ALTER TABLE auctions ADD COLUMN {column_name} {column_type}"))
                print(f"Added column: {column_name}")
        
        conn.commit()
    except Exception as e:
        print(f"Migration check failed: {e}")

app = FastAPI()

# Configure CORS - be more permissive for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auction Analysis Agent"}

@app.post("/scrape")
def scrape_auctions(db: Session = Depends(get_db)):
    try:
        print("Starting scrape...")
        scraped_data = run_scraper()
        print(f"Scraped {len(scraped_data)} items")
        
        new_items = 0
        for item in scraped_data:
            # Check if the auction already exists
            exists = db.query(Auction).filter(Auction.auction_url == item['auction_url']).first()
            if not exists:
                db_auction = Auction(**item)
                db.add(db_auction)
                new_items += 1
        
        db.commit()
        print(f"Added {new_items} new items to database")
        
        auctions = db.query(Auction).all()
        return {"auctions": auctions}
    except Exception as e:
        print(f"Error during scrape: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auctions")
def get_auctions(db: Session = Depends(get_db)):
    try:
        print("Fetching auctions from database...")
        auctions = db.query(Auction).all()
        print(f"Found {len(auctions)} auctions")
        return {"auctions": auctions}
    except Exception as e:
        print(f"Error fetching auctions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/{auction_id}")
def analyze_auction(auction_id: int, db: Session = Depends(get_db)):
    try:
        db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
        if not db_auction:
            raise HTTPException(status_code=404, detail="Auction not found")

        # First, scrape detailed information if we haven't already
        if not db_auction.details_scraped:
            print(f"Scraping detailed information for auction {auction_id}")
            details = scrape_auction_details(db_auction.auction_url)
            
            if details:
                # Update the auction with detailed information
                if 'description_text' in details:
                    db_auction.description = details['description_text']
                if 'all_images' in details:
                    db_auction.all_images = details['all_images']
                if 'num_bids' in details:
                    db_auction.num_bids = details['num_bids']
                if 'seller' in details:
                    db_auction.seller = details['seller']
                if 'item_details' in details:
                    db_auction.item_details = details['item_details']
                
                db_auction.details_scraped = True
                db.commit()
                print(f"Updated auction with detailed information. Images: {len(details.get('all_images', []))}")

        # Now analyze with all available information
        print(f"Analyzing auction with {len(db_auction.all_images) if db_auction.all_images else 1} images")
        estimated_value, analysis = analyze_auction_item(
            db_auction.title, 
            db_auction.image_url,
            description=db_auction.description,
            all_images=db_auction.all_images,
            current_price=db_auction.price
        )

        db_auction.estimated_value = estimated_value
        db_auction.analysis = analysis
        db.commit()
        db.refresh(db_auction)
        
        return db_auction
    except Exception as e:
        print(f"Error analyzing auction: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/batch")
async def analyze_batch(auction_ids: list[int], db: Session = Depends(get_db)):
    """
    Analyze multiple auctions in batch with concurrent processing
    """
    try:
        results = []
        errors = []
        
        # Create a thread pool for concurrent processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            
            for auction_id in auction_ids:
                # Submit each analysis to the thread pool
                future = executor.submit(
                    analyze_single_auction, 
                    auction_id, 
                    db
                )
                futures.append((auction_id, future))
            
            # Collect results as they complete
            for auction_id, future in futures:
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per item
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error analyzing auction {auction_id}: {e}")
                    errors.append({"id": auction_id, "error": str(e)})
        
        return {
            "analyzed": results,
            "errors": errors,
            "total_analyzed": len(results),
            "total_errors": len(errors)
        }
        
    except Exception as e:
        print(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def analyze_single_auction(auction_id: int, db: Session):
    """
    Analyze a single auction (used for concurrent processing)
    """
    try:
        db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
        if not db_auction:
            raise ValueError("Auction not found")

        # First, scrape detailed information if we haven't already
        if not db_auction.details_scraped:
            print(f"Scraping detailed information for auction {auction_id}")
            details = scrape_auction_details(db_auction.auction_url)
            
            if details:
                # Update the auction with detailed information
                if 'description_text' in details:
                    db_auction.description = details['description_text']
                if 'all_images' in details:
                    db_auction.all_images = details['all_images']
                if 'num_bids' in details:
                    db_auction.num_bids = details['num_bids']
                if 'seller' in details:
                    db_auction.seller = details['seller']
                if 'item_details' in details:
                    db_auction.item_details = details['item_details']
                
                db_auction.details_scraped = True
                db.commit()
                print(f"Updated auction with detailed information. Images: {len(details.get('all_images', []))}")

        # Now analyze with all available information
        print(f"Analyzing auction {auction_id} with {len(db_auction.all_images) if db_auction.all_images else 1} images")
        estimated_value, analysis = analyze_auction_item(
            db_auction.title, 
            db_auction.image_url,
            description=db_auction.description,
            all_images=db_auction.all_images,
            current_price=db_auction.price
        )

        db_auction.estimated_value = estimated_value
        db_auction.analysis = analysis
        db.commit()
        db.refresh(db_auction)
        
        return db_auction
        
    except Exception as e:
        print(f"Error in analyze_single_auction for {auction_id}: {e}")
        raise

@app.get("/market-research/{auction_id}")
def get_market_research(auction_id: int, db: Session = Depends(get_db)):
    """
    Get market research data for a specific auction
    """
    try:
        db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
        if not db_auction:
            raise HTTPException(status_code=404, detail="Auction not found")
        
        print(f"Getting market research for: {db_auction.title}")
        research_data = price_research.research_item_value(
            db_auction.title, 
            db_auction.description
        )
        
        return {
            "auction_id": auction_id,
            "title": db_auction.title,
            "market_research": research_data
        }
        
    except Exception as e:
        print(f"Error getting market research: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opportunities")
def get_opportunities(db: Session = Depends(get_db)):
    all_auctions = db.query(Auction).filter(Auction.estimated_value != None).all()
    
    opportunities = []
    for auction in all_auctions:
        current_price = parse_price(auction.price)
        if current_price is None or auction.estimated_value is None:
            continue
            
        # Define an opportunity as estimated value being > 50% of current price
        if auction.estimated_value > (current_price * 1.5):
            opportunities.append(auction)
            
    return {"auctions": opportunities}

@app.post("/watchlist/{auction_id}")
def toggle_watchlist(auction_id: int, db: Session = Depends(get_db)):
    db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not db_auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    db_auction.is_watchlisted = not db_auction.is_watchlisted
    db.commit()
    db.refresh(db_auction)
    
    return db_auction 