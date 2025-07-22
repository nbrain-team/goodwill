import { Title } from '@mantine/core';
import { AppLayout } from '@/components/AppLayout';

export default function OpportunitiesPage() {
  return (
    <AppLayout>
      <Title order={1} mb="xl">Top Opportunities</Title>
      {/* Opportunities content will go here */}
      <p>Auctions with a high estimated value compared to their current price will appear here.</p>
    </AppLayout>
  );
} 