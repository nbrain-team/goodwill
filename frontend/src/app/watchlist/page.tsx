'use client';

import { useState, useEffect, useCallback } from 'react';
import { Title, Grid, Card, Image, Text, Badge, Skeleton, Group, ActionIcon } from '@mantine/core';
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

export default function WatchlistPage() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
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

  const handleToggleWatchlist = async (auctionId: number) => {
    try {
      const response = await fetch(`${backendUrl}/watchlist/${auctionId}`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to update watchlist');
      // Refetch all auctions to ensure data is consistent
      fetchAuctions();
      // Close modal if removing from watchlist
      if (selectedAuction && selectedAuction.id === auctionId && selectedAuction.is_watchlisted) {
        setModalOpened(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  const openAuctionDetails = (auction: Auction) => {
    setSelectedAuction(auction);
    setModalOpened(true);
  };

  const watchlistedAuctions = auctions.filter(a => a.is_watchlisted);

  return (
    <AppLayout>
      <Title order={1} mb="xl">My Watchlist</Title>

      {error && <Text c="red.6">{error}</Text>}

      <AuctionModal
        auction={selectedAuction}
        opened={modalOpened}
        onClose={() => setModalOpened(false)}
        onToggleWatchlist={handleToggleWatchlist}
      />

      <Grid>
        {isLoading ? (
          Array.from({ length: 3 }).map((_, index) => (
            <Grid.Col span={{ base: 12, md: 6, lg: 4 }} key={index}>
              <Skeleton height={300} />
            </Grid.Col>
          ))
        ) : watchlistedAuctions.length === 0 ? (
          <Text>You haven&apos;t added any auctions to your watchlist yet.</Text>
        ) : (
          watchlistedAuctions.map((auction) => (
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
                  <Image src={auction.image_url} height={160} alt={auction.title} />
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
              </Card>
            </Grid.Col>
          ))
        )}
      </Grid>
    </AppLayout>
  );
} 