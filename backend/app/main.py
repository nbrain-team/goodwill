from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models.auction import Auction
from app.services.scraper import main as run_scraper

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow CORS for the frontend
origins = [
    "http://localhost:3000",  # Next.js default port
    # Add your deployed frontend URL here
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