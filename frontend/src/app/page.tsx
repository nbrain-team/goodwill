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

  const getBackendUrl = () => {
    const rawUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (rawUrl && !rawUrl.startsWith('http')) {
      return `https://${rawUrl}`;
    }
    return rawUrl || 'http://localhost:8000';
  };
  
  const backendUrl = getBackendUrl();

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
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-8">Auction Analysis Agent</h1>
      <button
        onClick={handleScrape}
        disabled={isLoading}
        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:bg-gray-500"
      >
        {isLoading ? 'Scraping...' : 'Scrape Auctions'}
      </button>

      {error && <p className="text-red-500 mt-4">{error}</p>}

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-6xl">
        {auctions.map((auction) => (
          <div key={auction.id} className="bg-gray-800 p-4 rounded-lg shadow-lg flex flex-col justify-between">
            <div>
              <img src={auction.image_url} alt={auction.title} className="w-full h-48 object-cover rounded-md mb-4" />
              <h2 className="text-xl font-semibold mb-2">{auction.title}</h2>
              <p className="text-lg font-bold text-green-400 mb-2">{auction.price}</p>
              {auction.estimated_value && (
                <p className="text-lg font-bold text-yellow-400 mb-2">Estimated Value: ${auction.estimated_value.toFixed(2)}</p>
              )}
              {auction.analysis && (
                <p className="text-sm text-gray-300 mb-4">{auction.analysis}</p>
              )}
            </div>
            <div className="flex justify-between items-center mt-4">
                <a href={auction.auction_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
                View Auction
                </a>
                <button 
                onClick={() => handleAnalyze(auction.id)}
                className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-1 px-3 rounded"
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
