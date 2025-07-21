'use client';

import { useState, useEffect } from 'react';

interface Auction {
  id: number;
  title: string;
  price: string;
  image_url: string;
  auction_url: string;
  estimated_value: number | null;
  analysis: string | null;
}

export default function Home() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const fetchAuctions = async () => {
    try {
      const response = await fetch(`${backendUrl}/auctions`);
      if (!response.ok) {
        throw new Error('Failed to fetch auctions');
      }
      const data = await response.json();
      setAuctions(data.auctions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  useEffect(() => {
    fetchAuctions();
  }, []);

  const handleScrape = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${backendUrl}/scrape`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to fetch auctions');
      }
      const data = await response.json();
      setAuctions(data.auctions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async (auctionId: number) => {
    try {
      const response = await fetch(`${backendUrl}/analyze/${auctionId}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to analyze auction');
      }
      const updatedAuction = await response.json();
      setAuctions(auctions.map(a => a.id === auctionId ? updatedAuction : a));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem', backgroundColor: '#111', color: '#eee' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', color: 'white' }}>Auction Analysis Agent</h1>
        <button
          onClick={handleScrape}
          disabled={isLoading}
          style={{ padding: '0.5rem 1rem', cursor: 'pointer', backgroundColor: '#0070f3', color: 'white', border: 'none', borderRadius: '5px' }}
        >
          {isLoading ? 'Scraping...' : 'Scrape Auctions'}
        </button>
      </header>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {auctions.map((auction) => (
          <div key={auction.id} style={{ border: '1px solid #333', borderRadius: '8px', padding: '1rem', backgroundColor: '#222' }}>
            <img src={auction.image_url} alt={auction.title} style={{ width: '100%', height: '200px', objectFit: 'cover', borderRadius: '4px', marginBottom: '1rem' }} />
            <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>{auction.title}</h2>
            <p style={{ fontWeight: 'bold', color: '#2ecc71', marginBottom: '0.5rem' }}>{auction.price}</p>
            {auction.estimated_value && (
              <p style={{ fontWeight: 'bold', color: '#f1c40f', marginBottom: '0.5rem' }}>
                Estimated Value: ${auction.estimated_value.toFixed(2)}
              </p>
            )}
            {auction.analysis && (
              <p style={{ fontSize: '0.875rem', color: '#ccc', marginBottom: '1rem' }}>{auction.analysis}</p>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
              <a href={auction.auction_url} target="_blank" rel="noopener noreferrer" style={{ color: '#3498db' }}>
                View Auction
              </a>
              <button
                onClick={() => handleAnalyze(auction.id)}
                style={{ padding: '0.25rem 0.75rem', cursor: 'pointer', backgroundColor: '#8e44ad', color: 'white', border: 'none', borderRadius: '5px' }}
              >
                Analyze
              </button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
