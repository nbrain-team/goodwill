import { Title } from '@mantine/core';
import { AppLayout } from '@/components/AppLayout';

export default function WatchlistPage() {
  return (
    <AppLayout>
      <Title order={1} mb="xl">My Watchlist</Title>
      {/* Watchlist content will go here */}
      <p>Auctions you save will appear here.</p>
    </AppLayout>
  );
} 