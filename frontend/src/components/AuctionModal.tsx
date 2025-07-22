'use client';

import { Modal, Stack, Image, Group, Badge, Text, ScrollArea, Button } from '@mantine/core';
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

interface AuctionModalProps {
  auction: Auction | null;
  opened: boolean;
  onClose: () => void;
  onToggleWatchlist: (auctionId: number) => void;
}

export function AuctionModal({ auction, opened, onClose, onToggleWatchlist }: AuctionModalProps) {
  if (!auction) return null;

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={auction.title}
      size="lg"
    >
      <Stack>
        <Image
          src={auction.image_url}
          alt={auction.title}
          height={300}
          fit="contain"
        />
        
        <Group justify="space-between">
          <Badge color="pink" size="lg">{auction.price}</Badge>
          {auction.estimated_value && (
            <Badge color="yellow" size="lg">
              Estimated: ${auction.estimated_value.toFixed(2)}
            </Badge>
          )}
        </Group>

        {auction.analysis && (
          <>
            <Text fw={700} size="lg">Analysis:</Text>
            <ScrollArea h={300}>
              <Text style={{ whiteSpace: 'pre-wrap' }}>
                {auction.analysis}
              </Text>
            </ScrollArea>
          </>
        )}

        <Group mt="md">
          <Button
            component="a"
            href={auction.auction_url}
            target="_blank"
            variant="filled"
            color="blue"
            fullWidth
          >
            View on ShopGoodwill
          </Button>
          <Button
            onClick={() => onToggleWatchlist(auction.id)}
            variant="light"
            color="grape"
            fullWidth
            leftSection={auction.is_watchlisted ? <IconBookmarkFilled size={16} /> : <IconBookmark size={16} />}
          >
            {auction.is_watchlisted ? 'Remove from Watchlist' : 'Add to Watchlist'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
} 