from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(String) # Keep as string to handle non-numeric values like '$1.23 (5 bids)'
    image_url = Column(String)
    auction_url = Column(String, unique=True, index=True)
    estimated_value = Column(Float, nullable=True)
    analysis = Column(String, nullable=True) 