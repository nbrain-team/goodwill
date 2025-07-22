from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base, get_db
from app.models.auction import Auction
from app.services.scraper import main as run_scraper
from app.services.analysis import analyze_auction_item
from app.services.utils import parse_price

# Create tables
Base.metadata.create_all(bind=engine)

# Add migration for is_watchlisted column if it doesn't exist
with engine.connect() as conn:
    try:
        # Check if column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='auctions' AND column_name='is_watchlisted'
        """))
        if not result.fetchone():
            # Add the column if it doesn't exist
            conn.execute(text("ALTER TABLE auctions ADD COLUMN is_watchlisted BOOLEAN DEFAULT FALSE"))
            conn.commit()
    except Exception as e:
        print(f"Migration check failed: {e}")
        # If the check fails, it might be because the table doesn't exist yet
        # In that case, the create_all above will create it with the column

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
    db_auction = db.query(Auction).filter(Auction.id == auction_id).first()
    if not db_auction:
        raise HTTPException(status_code=404, detail="Auction not found")

    estimated_value, analysis = analyze_auction_item(db_auction.title, db_auction.image_url)

    db_auction.estimated_value = estimated_value
    db_auction.analysis = analysis
    db.commit()
    db.refresh(db_auction)
    
    return db_auction

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