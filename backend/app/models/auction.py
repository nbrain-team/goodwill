from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON
from app.database import Base

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(String)
    image_url = Column(String)
    auction_url = Column(String, unique=True, index=True)
    estimated_value = Column(Float, nullable=True)
    analysis = Column(Text, nullable=True)
    is_watchlisted = Column(Boolean, default=False)
    
    # New fields for detailed information
    description = Column(Text, nullable=True)
    all_images = Column(JSON, nullable=True)  # Store as JSON array
    num_bids = Column(String, nullable=True)
    seller = Column(String, nullable=True)
    item_details = Column(JSON, nullable=True)  # Store various details as JSON
    details_scraped = Column(Boolean, default=False)  # Track if we've scraped details 