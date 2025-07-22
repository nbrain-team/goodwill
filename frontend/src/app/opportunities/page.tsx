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

export default function OpportunitiesPage() {
  const [auctions, setAuctions] = useState<Auction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAuction, setSelectedAuction] = useState<Auction | null>(null);
  const [modalOpened, setModalOpened] = useState(false);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const fetchOpportunities = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${backendUrl}/opportunities`);
      if (!response.ok) throw new Error('Failed to fetch opportunities');
      const data = await response.json();
      setAuctions(data.auctions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [backendUrl]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);
  
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
      <Title order={1} mb="xl">Top Opportunities</Title>
      <Text mb="xl">Auctions where the estimated value is at least 50% greater than the current price.</Text>

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
        ) : auctions.length === 0 ? (
          <Text>No opportunities found. Analyze more auctions to find them!</Text>
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