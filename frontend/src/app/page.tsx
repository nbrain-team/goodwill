'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button, Grid, Card, Image, Text, Badge, Skeleton, Group, ActionIcon } from '@mantine/core';
import { AppLayout } from '@/components/AppLayout';
import { AuctionModal } from '@/components/AuctionModal';
import { IconBookmark, IconBookmarkFilled } from '@tabler/icons-react';

interface Auction {
  id: number;
  title: string;
  price: string;
  image_url: string;
  auction_url: string;
  estimated_value: number | null;
  analysis: string | null;
  is_watchlisted: boolean;
}

export default function Home() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAuction, setSelectedAuction] = useState<Auction | null>(null);
  const [modalOpened, setModalOpened] = useState(false);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const fetchAuctions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${backendUrl}/auctions`);
      if (!response.ok) throw new Error('Failed to fetch auctions');
      const data = await response.json();
      setAuctions(data.auctions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    fetchAuctions();
  }, [fetchAuctions]);

  const handleScrape = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${backendUrl}/scrape`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to fetch auctions');
      const data = await response.json();
      setAuctions(data.auctions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async (auctionId: number) => {
    setIsAnalyzing(auctionId);
    try {
      const response = await fetch(`${backendUrl}/analyze/${auctionId}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to analyze auction');
      const updatedAuction = await response.json();
      setAuctions(auctions.map(a => a.id === auctionId ? updatedAuction : a));
      // Update modal auction if it's the same one
      if (selectedAuction && selectedAuction.id === auctionId) {
        setSelectedAuction(updatedAuction);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsAnalyzing(null);
    }
  };

  const handleToggleWatchlist = async (auctionId: number) => {
    try {
      const response = await fetch(`${backendUrl}/watchlist/${auctionId}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to update watchlist');
      const updatedAuction = await response.json();
      setAuctions(auctions.map(a => a.id === auctionId ? updatedAuction : a));
      // Update modal auction if it's the same one
      if (selectedAuction && selectedAuction.id === auctionId) {
        setSelectedAuction(updatedAuction);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  const openAuctionDetails = (auction: Auction) => {
    setSelectedAuction(auction);
    setModalOpened(true);
  };

  return (
    <AppLayout>
      <Group mb="xl">
        <Button onClick={handleScrape} loading={isLoading}>
          Scrape for New Auctions
        </Button>
      </Group>

      {error && <Text c="red.6">{error}</Text>}

      <AuctionModal
        auction={selectedAuction}
        opened={modalOpened}
        onClose={() => setModalOpened(false)}
        onToggleWatchlist={handleToggleWatchlist}
      />

      <Grid>
        {isLoading && !auctions.length ? (
          Array.from({ length: 6 }).map((_, index) => (
            <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={index}>
              <Skeleton height={300} />
            </Grid.Col>
          ))
        ) : (
          auctions.map((auction) => (
            <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={auction.id}>
              <Card 
                shadow="sm" 
                padding="lg" 
                radius="md" 
                withBorder
                style={{ cursor: 'pointer' }}
                onClick={() => openAuctionDetails(auction)}
              >
                <Card.Section>
                  <Image
                    src={auction.image_url}
                    height={160}
                    alt={auction.title}
                  />
                </Card.Section>

                <Group justify="space-between" mt="md" mb="xs">
                  <Text fw={500} lineClamp={2}>{auction.title}</Text>
                  <ActionIcon 
                    variant="subtle" 
                    color="gray" 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleWatchlist(auction.id);
                    }}
                  >
                    {auction.is_watchlisted ? <IconBookmarkFilled /> : <IconBookmark />}
                  </ActionIcon>
                </Group>
                
                <Badge color="pink">{auction.price}</Badge>

                {auction.estimated_value && (
                  <Group mt="sm">
                    <Text fw={700}>Estimated Value:</Text>
                    <Badge color="yellow">${auction.estimated_value.toFixed(2)}</Badge>
                  </Group>
                )}

                <Text size="sm" c="dimmed" mt="sm" lineClamp={3}>
                  {auction.analysis || 'No analysis yet.'}
                </Text>
                
                <Group mt="md">
                  <Button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAnalyze(auction.id);
                    }}
                    loading={isAnalyzing === auction.id}
                    variant="light" 
                    color="grape" 
                    fullWidth
                  >
                    {auction.analysis ? 'Re-analyze' : 'Analyze'}
                  </Button>
                </Group>
              </Card>
            </Grid.Col>
          ))
        )}
      </Grid>
    </AppLayout>
  );
}
