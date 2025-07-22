from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models.auction import Auction
from app.services.scraper import main as run_scraper
from app.services.analysis import analyze_auction_item
from app.services.utils import parse_price

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow CORS for the frontend
origins = [
    "http://localhost:3000",  # Next.js default port
    "https://*.onrender.com", # Allow all onrender.com subdomains
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Auction Analysis Agent"}

@app.post("/scrape")
def scrape_auctions(db: Session = Depends(get_db)):
    scraped_data = run_scraper()
    
    for item in scraped_data:
        # Check if the auction already exists
        exists = db.query(Auction).filter(Auction.auction_url == item['auction_url']).first()
        if not exists:
            db_auction = Auction(**item)
            db.add(db_auction)
    
    db.commit()
    
    auctions = db.query(Auction).all()
    return {"auctions": auctions}

@app.get("/auctions")
def get_auctions(db: Session = Depends(get_db)):
    auctions = db.query(Auction).all()
    return {"auctions": auctions}

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