import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Container, Typography, Grid, Paper, Box, Tabs, Tab, CircularProgress,
  Card, CardContent, Divider, Button, Chip, List, ListItem, ListItemText
} from '@mui/material';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import InfoIcon from '@mui/icons-material/Info';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import BarChartIcon from '@mui/icons-material/BarChart';
import NewspaperIcon from '@mui/icons-material/Newspaper';

const Stock = () => {
  const { symbol } = useParams();
  const [stockData, setStockData] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeframe, setTimeframe] = useState('1D');

  // Fetch stock details
  useEffect(() => {
    const fetchStockData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`/api/details/${symbol}`);
        setStockData(response.data);
        setError(null);
      } catch (err) {
        console.error("Error fetching stock details:", err);
        setError("Failed to load stock data. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchStockData();
  }, [symbol]);

  // Fetch chart data
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const response = await axios.get(`/api/chart/${symbol}?timeframe=${timeframe}`);
        
        // Transform data for the chart
        const formattedData = response.data.data.map(point => ({
          date: new Date(point.time * 1000).toLocaleString(),
          price: point.price,
          volume: point.volume
        }));
        
        setChartData(formattedData);
      } catch (err) {
        console.error("Error fetching chart data:", err);
      }
    };

    if (symbol) {
      fetchChartData();
    }
  }, [symbol, timeframe]);

  const handleTimeframeChange = (event, newValue) => {
    setTimeframe(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography color="error" variant="h6">{error}</Typography>
      </Container>
    );
  }

  // Format percent change for display
  const percentChange = stockData ? parseFloat(stockData.percent_change) : 0;
  const isPositive = percentChange >= 0;
  const formattedPercentChange = isPositive 
    ? `+${percentChange.toFixed(2)}%` 
    : `${percentChange.toFixed(2)}%`;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {stockData && (
        <>
          <Box sx={{ mb: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom>
              {stockData.name} ({stockData.symbol})
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
              <Typography variant="h5" component="span" sx={{ mr: 2 }}>
                ${stockData.price}
              </Typography>
              <Typography 
                variant="subtitle1" 
                component="span" 
                sx={{ color: isPositive ? 'success.main' : 'error.main' }}
              >
                {stockData.change} ({formattedPercentChange})
              </Typography>
            </Box>
          </Box>

          <Grid container spacing={3}>
            {/* Chart section */}
            <Grid item xs={12}>
              <Paper sx={{ p: 2 }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                  <Tabs value={timeframe} onChange={handleTimeframeChange} aria-label="chart timeframe">
                    <Tab label="1D" value="1D" />
                    <Tab label="5D" value="5D" />
                    <Tab label="1M" value="1M" />
                    <Tab label="3M" value="3M" />
                    <Tab label="6M" value="6M" />
                    <Tab label="1Y" value="1Y" />
                    <Tab label="5Y" value="5Y" />
                  </Tabs>
                </Box>
                <Box sx={{ height: 400 }}>
                  {chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={chartData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fontSize: 12 }} 
                          tickFormatter={(val) => {
                            if (timeframe === "1D" || timeframe === "5D") {
                              return new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            } else {
                              return new Date(val).toLocaleDateString();
                            }
                          }}
                        />
                        <YAxis 
                          domain={['dataMin', 'dataMax']}
                          tickFormatter={(val) => `$${val.toFixed(2)}`}
                        />
                        <Tooltip 
                          formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                          labelFormatter={(label) => new Date(label).toLocaleString()}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="price" 
                          stroke={isPositive ? "#4caf50" : "#f44336"} 
                          dot={false}
                          strokeWidth={2}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <CircularProgress />
                    </Box>
                  )}
                </Box>
              </Paper>
            </Grid>

            {/* Company Info */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <InfoIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Company Info</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Sector" 
                        secondary={stockData.sector} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Industry" 
                        secondary={stockData.industry} 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Description" 
                        secondary={stockData.description}
                        secondaryTypographyProps={{
                          style: { 
                            whiteSpace: 'normal',
                            display: '-webkit-box',
                            WebkitLineClamp: 4,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }
                        }}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            {/* Key Stats */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <BarChartIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Key Statistics</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Market Cap</Typography>
                      <Typography variant="body1">{stockData.market_cap}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">P/E Ratio</Typography>
                      <Typography variant="body1">{stockData.pe_ratio}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">EPS</Typography>
                      <Typography variant="body1">{stockData.eps}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Dividend Yield</Typography>
                      <Typography variant="body1">{stockData.dividend_yield}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">P/B Ratio</Typography>
                      <Typography variant="body1">{stockData.pb_ratio}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Volume</Typography>
                      <Typography variant="body1">{stockData.volume}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Avg Volume</Typography>
                      <Typography variant="body1">{stockData.avg_volume}</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* News */}
            <Grid item xs={12} md={4}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <NewspaperIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">Related News</Typography>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  
                  {/* For now, just show a placeholder */}
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
                    <Typography color="text.secondary">
                      News API integration coming soon
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
};

export default Stock; 