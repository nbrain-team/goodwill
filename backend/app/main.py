from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.scraper import main as run_scraper

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
async def scrape_auctions():
    data = run_scraper()
    return {"auctions": data} 