'use client';

import { Modal, Stack, Image, Group, Badge, Text, ScrollArea, Button, Tabs, Table, Card, SimpleGrid, Title, Divider, Box, Paper, Skeleton, Anchor } from '@mantine/core';
import { IconBookmark, IconBookmarkFilled, IconPhoto, IconAnalyze, IconChartBar } from '@tabler/icons-react';
import { useState, useMemo, useEffect } from 'react';
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
  item_details?: Record<string, unknown>;
}

interface AuctionModalProps {
  auction: Auction | null;
  opened: boolean;
  onClose: () => void;
  onToggleWatchlist: (auctionId: number) => void;
}

interface ParsedItem {
  description: string;
  value: number;
}

export function AuctionModal({ auction, opened, onClose, onToggleWatchlist }: AuctionModalProps) {
  const [selectedImage, setSelectedImage] = useState(0);
  const [marketData, setMarketData] = useState<any>(null);
  const [loadingMarketData, setLoadingMarketData] = useState(false);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

  const allImages = useMemo(() => {
    if (!auction) return [];
    return auction.all_images && auction.all_images.length > 0 
      ? auction.all_images 
      : [auction.image_url];
  }, [auction]);

  // Parse analysis for structured data
  const parsedAnalysis = useMemo(() => {
    if (!auction || !auction.analysis) return { items: [], summary: '' };
    
    const lines = auction.analysis.split('\n');
    const items: ParsedItem[] = [];
    const summary: string[] = [];
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
  }, [auction]);

  // Fetch market research data when modal opens or auction changes
  useEffect(() => {
    if (opened && auction && auction.analysis) {
      fetchMarketData();
    }
  }, [opened, auction?.id]);

  const fetchMarketData = async () => {
    if (!auction) return;
    
    setLoadingMarketData(true);
    try {
      const response = await fetch(`${backendUrl}/market-research/${auction.id}`);
      if (!response.ok) throw new Error('Failed to fetch market research');
      const data = await response.json();
      setMarketData(data.market_research);
    } catch (error) {
      console.error('Error fetching market research:', error);
    } finally {
      setLoadingMarketData(false);
    }
  };

  if (!auction) return null;

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
                <Text fw={700} mb="sm">Seller&apos;s Description</Text>
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
          {loadingMarketData ? (
            <Stack>
              <Skeleton height={100} />
              <Skeleton height={200} />
              <Skeleton height={150} />
            </Stack>
          ) : marketData ? (
            <Stack>
              {/* eBay Sold Listings */}
              {marketData.ebay_data?.num_sold > 0 && (
                <Paper shadow="xs" p="md">
                  <Group mb="md">
                    <Text fw={700}>📊 eBay Sold Listings</Text>
                    <Badge color="blue">{marketData.ebay_data.num_sold} sold</Badge>
                  </Group>
                  
                  <Table striped>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td fw={600}>Average Sold Price</Table.Td>
                        <Table.Td>${marketData.ebay_data.average_price?.toFixed(2) || 'N/A'}</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td fw={600}>Price Range</Table.Td>
                        <Table.Td>{marketData.ebay_data.price_range || 'N/A'}</Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>

                  {marketData.ebay_data.recent_sales && marketData.ebay_data.recent_sales.length > 0 && (
                    <>
                      <Text fw={600} mt="md" mb="sm">Recent Sales:</Text>
                      <ScrollArea h={200}>
                        <Stack gap="xs">
                          {marketData.ebay_data.recent_sales.slice(0, 5).map((sale: any, idx: number) => (
                            <Paper key={idx} p="xs" withBorder>
                              <Group justify="space-between">
                                <Text size="sm" lineClamp={1}>{sale.title}</Text>
                                <Badge color="green">${sale.price.toFixed(2)}</Badge>
                              </Group>
                              {sale.condition && <Text size="xs" c="dimmed">Condition: {sale.condition}</Text>}
                              {sale.link && (
                                <Anchor href={sale.link} target="_blank" size="xs">
                                  View listing
                                </Anchor>
                              )}
                            </Paper>
                          ))}
                        </Stack>
                      </ScrollArea>
                    </>
                  )}
                </Paper>
              )}

              {/* Web Search Results */}
              {marketData.web_results && marketData.web_results.length > 0 && (
                <Paper shadow="xs" p="md">
                  <Text fw={700} mb="md">🌐 Web Pricing Research</Text>
                  <ScrollArea h={200}>
                    <Stack gap="xs">
                      {marketData.web_results.slice(0, 5).map((result: any, idx: number) => (
                        <Paper key={idx} p="xs" withBorder>
                          <Anchor href={result.link} target="_blank" size="sm" fw={500}>
                            {result.title}
                          </Anchor>
                          <Text size="xs" c="dimmed" mt={4}>{result.snippet}</Text>
                        </Paper>
                      ))}
                    </Stack>
                  </ScrollArea>
                </Paper>
              )}

              {/* Price Summary */}
              {marketData.price_summary?.status === 'success' && (
                <Paper shadow="xs" p="md">
                  <Text fw={700} mb="md">💰 Price Analysis Summary</Text>
                  <Table>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td fw={600}>Market Value Range</Table.Td>
                        <Table.Td>{marketData.price_summary.estimated_value_range}</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td fw={600}>Average Market Value</Table.Td>
                        <Table.Td>${marketData.price_summary.average_value?.toFixed(2) || 'N/A'}</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td fw={600}>Confidence Level</Table.Td>
                        <Table.Td>
                          <Badge color={
                            marketData.price_summary.confidence === 'high' ? 'green' :
                            marketData.price_summary.confidence === 'medium' ? 'yellow' : 'red'
                          }>
                            {marketData.price_summary.confidence?.toUpperCase()}
                          </Badge>
                        </Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td fw={600}>Data Points</Table.Td>
                        <Table.Td>{marketData.price_summary.data_points}</Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>
                </Paper>
              )}

              {/* Recommendations */}
              {marketData.recommendations && (
                <Paper shadow="xs" p="md">
                  <Text fw={700} mb="md">🎯 Selling Recommendations</Text>
                  <Table>
                    <Table.Tbody>
                      <Table.Tr>
                        <Table.Td fw={600}>Suggested List Price</Table.Td>
                        <Table.Td>{marketData.recommendations.list_price}</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td fw={600}>Accept Offers Above</Table.Td>
                        <Table.Td>{marketData.recommendations.accept_offers_above}</Table.Td>
                      </Table.Tr>
                      <Table.Tr>
                        <Table.Td fw={600}>Quick Sale Price</Table.Td>
                        <Table.Td>{marketData.recommendations.quick_sale_price}</Table.Td>
                      </Table.Tr>
                    </Table.Tbody>
                  </Table>
                  <Text size="sm" mt="md" c="dimmed">
                    Strategy: {marketData.recommendations.strategy}
                  </Text>
                </Paper>
              )}
            </Stack>
          ) : (
            <Paper shadow="xs" p="md">
              <Text fw={700} mb="md">Market Research Data</Text>
              <Text c="dimmed" size="sm">
                Analyze this item first to see market research data.
              </Text>
            </Paper>
          )}
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