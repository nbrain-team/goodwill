'use client';

import { Modal, Stack, Image, Group, Badge, Text, ScrollArea, Button, Tabs, Table, Card, SimpleGrid, Title, Divider, Box, Paper } from '@mantine/core';
import { IconBookmark, IconBookmarkFilled, IconPhoto, IconAnalyze, IconChartBar } from '@tabler/icons-react';
import { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';

interface Auction {
  id: number;
  title: string;
  price: string;
  image_url: string;
  auction_url: string;
  estimated_value: number | null;
  analysis: string | null;
  is_watchlisted: boolean;
  all_images?: string[];
  description?: string;
  seller?: string;
  num_bids?: string;
  item_details?: any;
}

interface AuctionModalProps {
  auction: Auction | null;
  opened: boolean;
  onClose: () => void;
  onToggleWatchlist: (auctionId: number) => void;
}

export function AuctionModal({ auction, opened, onClose, onToggleWatchlist }: AuctionModalProps) {
  const [selectedImage, setSelectedImage] = useState(0);

  if (!auction) return null;

  const allImages = auction.all_images && auction.all_images.length > 0 
    ? auction.all_images 
    : [auction.image_url];

  // Parse analysis for structured data
  const parsedAnalysis = useMemo(() => {
    if (!auction.analysis) return { items: [], summary: auction.analysis || '' };
    
    const lines = auction.analysis.split('\n');
    const items: any[] = [];
    let summary = [];
    let inItemSection = false;
    
    for (const line of lines) {
      // Check for item listings
      if (line.match(/^Item \d+:|^- Item \d+:/)) {
        inItemSection = true;
        const match = line.match(/^(?:- )?Item \d+: (.+) - (?:Value: )?\$?([\d,]+(?:\.\d{2})?)/);
        if (match) {
          items.push({
            description: match[1],
            value: parseFloat(match[2].replace(/,/g, ''))
          });
        }
      } else if (inItemSection && line.trim() === '') {
        inItemSection = false;
      } else if (!inItemSection) {
        summary.push(line);
      }
    }
    
    return { items, summary: summary.join('\n') };
  }, [auction.analysis]);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        <Group>
          <Title order={3}>{auction.title}</Title>
          <Badge color="pink" size="lg">{auction.price}</Badge>
        </Group>
      }
      size="xl"
      fullScreen={window.innerWidth < 768}
    >
      <Tabs defaultValue="overview">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconPhoto size={16} />}>
            Overview
          </Tabs.Tab>
          <Tabs.Tab value="analysis" leftSection={<IconAnalyze size={16} />}>
            Analysis
          </Tabs.Tab>
          <Tabs.Tab value="market" leftSection={<IconChartBar size={16} />}>
            Market Data
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="xs">
          <Stack>
            {/* Image Gallery */}
            <Card shadow="sm" p="lg">
              <Image
                src={allImages[selectedImage]}
                alt={auction.title}
                height={400}
                fit="contain"
                mb="md"
              />
              {allImages.length > 1 && (
                <SimpleGrid cols={{ base: 4, sm: 6, md: 8 }} spacing="xs">
                  {allImages.map((img, idx) => (
                    <Image
                      key={idx}
                      src={img}
                      alt={`${auction.title} - Image ${idx + 1}`}
                      height={60}
                      fit="cover"
                      style={{
                        cursor: 'pointer',
                        border: selectedImage === idx ? '2px solid #7950f2' : '2px solid transparent',
                        borderRadius: 4
                      }}
                      onClick={() => setSelectedImage(idx)}
                    />
                  ))}
                </SimpleGrid>
              )}
            </Card>

            {/* Auction Details */}
            <Paper shadow="xs" p="md">
              <Group justify="space-between" mb="md">
                <Text fw={700}>Auction Details</Text>
                {auction.estimated_value && (
                  <Badge color="yellow" size="lg">
                    Est. Value: ${auction.estimated_value.toFixed(2)}
                  </Badge>
                )}
              </Group>
              
              <Table>
                <Table.Tbody>
                  <Table.Tr>
                    <Table.Td fw={600}>Current Price</Table.Td>
                    <Table.Td>{auction.price}</Table.Td>
                  </Table.Tr>
                  {auction.num_bids && (
                    <Table.Tr>
                      <Table.Td fw={600}>Number of Bids</Table.Td>
                      <Table.Td>{auction.num_bids}</Table.Td>
                    </Table.Tr>
                  )}
                  {auction.seller && (
                    <Table.Tr>
                      <Table.Td fw={600}>Seller</Table.Td>
                      <Table.Td>{auction.seller}</Table.Td>
                    </Table.Tr>
                  )}
                  {auction.estimated_value && (
                    <Table.Tr>
                      <Table.Td fw={600}>Profit Potential</Table.Td>
                      <Table.Td>
                        {(() => {
                          const currentPrice = parseFloat(auction.price.replace(/[^0-9.]/g, ''));
                          const profit = auction.estimated_value - currentPrice;
                          const profitPercent = (profit / currentPrice) * 100;
                          return (
                            <Text color={profit > 0 ? 'green' : 'red'}>
                              ${profit.toFixed(2)} ({profitPercent.toFixed(0)}%)
                            </Text>
                          );
                        })()}
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            </Paper>

            {/* Description */}
            {auction.description && (
              <Paper shadow="xs" p="md">
                <Text fw={700} mb="sm">Seller's Description</Text>
                <ScrollArea h={200}>
                  <Text size="sm">{auction.description}</Text>
                </ScrollArea>
              </Paper>
            )}
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="analysis" pt="xs">
          <Stack>
            {/* Individual Items Table */}
            {parsedAnalysis.items.length > 0 && (
              <Paper shadow="xs" p="md">
                <Text fw={700} mb="md">Individual Item Values</Text>
                <Table striped highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Item</Table.Th>
                      <Table.Th style={{ textAlign: 'right' }}>Retail Value</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {parsedAnalysis.items.map((item, idx) => (
                      <Table.Tr key={idx}>
                        <Table.Td>{item.description}</Table.Td>
                        <Table.Td style={{ textAlign: 'right' }}>${item.value.toFixed(2)}</Table.Td>
                      </Table.Tr>
                    ))}
                    <Table.Tr>
                      <Table.Td fw={700}>Total Retail Value</Table.Td>
                      <Table.Td fw={700} style={{ textAlign: 'right' }}>
                        ${parsedAnalysis.items.reduce((sum, item) => sum + item.value, 0).toFixed(2)}
                      </Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              </Paper>
            )}

            {/* Full Analysis */}
            <Paper shadow="xs" p="md">
              <Text fw={700} mb="md">Detailed Analysis</Text>
              <ScrollArea h={400}>
                <Box style={{ 
                  '& h1, & h2, & h3': { marginTop: '1em', marginBottom: '0.5em' },
                  '& p': { marginBottom: '0.5em' },
                  '& ul': { paddingLeft: '1.5em' }
                }}>
                  <ReactMarkdown>
                    {parsedAnalysis.summary}
                  </ReactMarkdown>
                </Box>
              </ScrollArea>
            </Paper>
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="market" pt="xs">
          <Paper shadow="xs" p="md">
            <Text fw={700} mb="md">Market Research Data</Text>
            <Text c="dimmed" size="sm">
              Market data integration coming soon...
            </Text>
          </Paper>
        </Tabs.Panel>
      </Tabs>

      <Divider my="md" />

      <Group>
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
    </Modal>
  );
} 