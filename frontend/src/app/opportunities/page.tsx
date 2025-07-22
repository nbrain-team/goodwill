'use client';

import { useState, useEffect, useCallback } from 'react';
import { Title, Grid, Card, Image, Text, Badge, Skeleton, Group, ActionIcon, Button } from '@mantine/core';
import { AppLayout } from '@/components/AppLayout';
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  return (
    <AppLayout>
      <Title order={1} mb="xl">Top Opportunities</Title>
      <Text mb="xl">Auctions where the estimated value is at least 50% greater than the current price.</Text>

      {error && <Text c="red.6">{error}</Text>}

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
              <Card shadow="sm" padding="lg" radius="md" withBorder>
                <Card.Section>
                  <Image src={auction.image_url} height={160} alt={auction.title} />
                </Card.Section>

                <Group justify="space-between" mt="md" mb="xs">
                  <Text fw={500} lineClamp={2}>{auction.title}</Text>
                   <ActionIcon variant="subtle" color="gray" onClick={() => handleToggleWatchlist(auction.id)}>
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
                  <Button component="a" href={auction.auction_url} target="_blank" variant="light" color="blue" fullWidth>
                    View Auction
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