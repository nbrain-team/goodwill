'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button, Grid, Card, Image, Text, Badge, Skeleton, Group, ActionIcon, Checkbox, Stack } from '@mantine/core';
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
  const [isBatchAnalyzing, setIsBatchAnalyzing] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
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

  const handleBatchAnalyze = async () => {
    if (selectedIds.size === 0) {
      setError('Please select items to analyze');
      return;
    }

    setIsBatchAnalyzing(true);
    setError(null);
    
    try {
      const response = await fetch(`${backendUrl}/analyze/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(Array.from(selectedIds)),
      });
      
      if (!response.ok) throw new Error('Failed to analyze batch');
      
      const result = await response.json();
      
      // Update auctions with analyzed results
      if (result.analyzed && result.analyzed.length > 0) {
        setAuctions(prevAuctions => 
          prevAuctions.map(auction => {
            const analyzed = result.analyzed.find((a: Auction) => a.id === auction.id);
            return analyzed || auction;
          })
        );
      }
      
      // Clear selections after analysis
      setSelectedIds(new Set());
      
      // Show summary
      if (result.total_errors > 0) {
        setError(`Analyzed ${result.total_analyzed} items. ${result.total_errors} errors occurred.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsBatchAnalyzing(false);
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

  const toggleSelection = (auctionId: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(auctionId)) {
        newSet.delete(auctionId);
      } else {
        newSet.add(auctionId);
      }
      return newSet;
    });
  };

  const selectAll = () => {
    setSelectedIds(new Set(auctions.map(a => a.id)));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  return (
    <AppLayout>
      <Stack gap="md">
        <Group justify="space-between">
          <Group>
            <Button onClick={handleScrape} loading={isLoading}>
              Scrape for New Auctions
            </Button>
            {selectedIds.size > 0 && (
              <>
                <Button 
                  onClick={handleBatchAnalyze} 
                  loading={isBatchAnalyzing}
                  color="grape"
                >
                  Analyze Selected ({selectedIds.size})
                </Button>
                <Button 
                  onClick={clearSelection}
                  variant="subtle"
                  size="sm"
                >
                  Clear Selection
                </Button>
              </>
            )}
          </Group>
          {auctions.length > 0 && (
            <Button 
              onClick={selectedIds.size === auctions.length ? clearSelection : selectAll}
              variant="subtle"
              size="sm"
            >
              {selectedIds.size === auctions.length ? 'Deselect All' : 'Select All'}
            </Button>
          )}
        </Group>

        {error && <Text c="red.6">{error}</Text>}
      </Stack>

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
                style={{ 
                  cursor: 'pointer',
                  position: 'relative',
                  border: selectedIds.has(auction.id) ? '2px solid #7950f2' : undefined
                }}
                onClick={() => openAuctionDetails(auction)}
              >
                <Checkbox
                  checked={selectedIds.has(auction.id)}
                  onChange={(e) => {
                    e.stopPropagation();
                    toggleSelection(auction.id);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    position: 'absolute',
                    top: 10,
                    left: 10,
                    zIndex: 10,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    borderRadius: 4,
                    padding: 2
                  }}
                />
                
                <Card.Section>
                  <Image
                    src={auction.image_url}
                    height={160}
                    alt={auction.title}
                  />
                </Card.Section>

                <Group justify="space-between" mt="md" mb="xs">
                  <Text fw={500} lineClamp={2} style={{ paddingLeft: 30 }}>{auction.title}</Text>
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
                    disabled={isBatchAnalyzing}
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
