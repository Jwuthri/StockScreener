import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Grid, Paper, Card, CardContent, 
  CardHeader, Divider, List, ListItem, ListItemText, 
  ListItemAvatar, Avatar, CircularProgress, Button,
  Tabs, Tab, Alert, Container, Chip
} from '@mui/material';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { Link } from 'react-router-dom';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [marketData, setMarketData] = useState(null);
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [mostActive, setMostActive] = useState([]);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('gainers');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [stockLimit, setStockLimit] = useState(10);
  
  // Parse the filter from URL query parameters
  const urlParams = new URLSearchParams(location.search);
  const filter = urlParams.get('filter');
  
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const filterParam = params.get('filter');
    
    if (filterParam) {
      if (['gainers', 'losers', 'most-active'].includes(filterParam)) {
        setActiveTab(filterParam);
      }
    } else {
      // Set the default tab to 'gainers' when no filter parameter is provided
      setActiveTab('gainers');
      // Update URL to reflect the default tab
      navigate('?filter=gainers', { replace: true });
    }
  }, [location.search, navigate]);
  
  useEffect(() => {
    fetchDashboardData();
  }, [stockLimit]);
  
  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    
    try {
      const [gainersRes, losersRes, activeRes] = await Promise.all([
        axios.get(`${API_URL}/api/stocks/gainers?limit=${stockLimit}`),
        axios.get(`${API_URL}/api/stocks/losers?limit=${stockLimit}`),
        axios.get(`${API_URL}/api/stocks/most-active?limit=${stockLimit}`)
      ]);
      
      // Process each dataset to ensure consistent formatting
      const processStockData = (stocks) => {
        if (!stocks || !Array.isArray(stocks)) return [];
        
        return stocks.map(stock => {
          // Format values properly for display
          return {
            ...stock,
            price: stock.price_display || 
                  (typeof stock.price === 'number' ? `$${stock.price.toFixed(2)}` : 
                   typeof stock.price === 'string' ? stock.price : 'N/A'),
            
            // Handle percent change consistently
            change_percent: (() => {
              const pct = stock.percent_change;
              if (pct === null || pct === undefined) return 'N/A';
              
              // If it's already a formatted string with % (from backend)
              if (typeof pct === 'string' && pct.includes('%')) {
                return pct; // Return as is, it's already formatted
              }
              
              // Otherwise parse and format
              const numPct = typeof pct === 'number' ? pct : parseFloat(pct);
              if (isNaN(numPct)) return 'N/A';
              return `${numPct >= 0 ? '+' : ''}${numPct.toFixed(2)}%`;
            })(),
            
            volume: stock.volume_display || 
                   (typeof stock.volume === 'number' ? 
                    stock.volume >= 1000000 ? `${(stock.volume / 1000000).toFixed(1)}M` :
                    stock.volume >= 1000 ? `${(stock.volume / 1000).toFixed(1)}K` :
                    stock.volume.toString() : stock.volume || 'N/A')
          };
        });
      };
      
      const processedGainers = processStockData(gainersRes.data.gainers || []);
      const processedLosers = processStockData(losersRes.data.losers || []);
      const processedActive = processStockData(activeRes.data.most_active || []);
      
      setTopGainers(processedGainers);
      setTopLosers(processedLosers);
      setMostActive(processedActive);
      
      setLastUpdated(new Date());
      setUsingDemoData(
        gainersRes.data.is_demo || 
        losersRes.data.is_demo || 
        activeRes.data.is_demo
      );
      
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError('Error fetching market data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };
  
  const refreshData = () => {
    fetchDashboardData();
  };
  
  // Generate sample price history data for chart
  const generateChartData = () => {
    const data = [];
    const now = new Date();
    for (let i = 30; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        'S&P 500': 4400 + Math.random() * 200,
        'NASDAQ': 15800 + Math.random() * 700,
      });
    }
    return data;
  };
  
  const chartData = generateChartData();
  
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    
    // Update URL based on selected tab
    if (newValue === 'gainers') {
      navigate('/?filter=gainers');
    } else if (newValue === 'losers') {
      navigate('/?filter=losers');
    } else if (newValue === 'most-active') {
      navigate('/?filter=most-active');
    }
  };
  
  const renderStockList = (stocks, loading, error) => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress size={24} />
        </Box>
      );
    }

    if (error) {
      return (
        <Box sx={{ p: 2, color: 'error.main' }}>
          <Typography>{error}</Typography>
        </Box>
      );
    }

    if (!stocks || stocks.length === 0) {
      return (
        <Box sx={{ p: 2 }}>
          <Typography>No stocks available</Typography>
        </Box>
      );
    }

    return (
      <List disablePadding>
        {stocks.map((stock, index) => (
          <ListItem 
            key={index} 
            button 
            component={Link} 
            to={`/stock/${stock.symbol}`}
            sx={{ 
              borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
              py: 1
            }}
          >
            <ListItemText 
              primary={stock.symbol} 
              secondary={stock.name || 'Unknown'} 
              primaryTypographyProps={{ fontWeight: 'bold' }}
            />
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                {stock.price}
              </Typography>
              <Typography 
                variant="body2" 
                color={(() => {
                  // Handle both formatted strings and numeric values
                  const pctStr = stock.change_percent;
                  if (pctStr === 'N/A') return 'text.secondary';
                  
                  // If it's a string with a % sign
                  if (typeof pctStr === 'string') {
                    // Remove any + sign and % sign for parsing
                    const cleanedStr = pctStr.replace('+', '').replace('%', '');
                    return parseFloat(cleanedStr) >= 0 ? 'success.main' : 'error.main';
                  }
                  
                  return 'text.secondary';
                })()}
              >
                {stock.change_percent}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Vol: {stock.volume}
              </Typography>
            </Box>
          </ListItem>
        ))}
      </List>
    );
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange} 
              aria-label="market trend tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab 
                icon={<ArrowUpwardIcon fontSize="small" />} 
                iconPosition="start" 
                label="Top Gainers" 
                value="gainers" 
              />
              <Tab 
                icon={<ArrowDownwardIcon fontSize="small" />} 
                iconPosition="start" 
                label="Top Losers" 
                value="losers" 
              />
              <Tab 
                icon={<ShowChartIcon fontSize="small" />} 
                iconPosition="start" 
                label="Most Active" 
                value="most-active" 
              />
            </Tabs>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="body2" sx={{ mr: 1 }}>Show:</Typography>
                <select 
                  value={stockLimit}
                  onChange={(e) => {
                    setStockLimit(Number(e.target.value));
                  }}
                  style={{ 
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: '1px solid #ccc'
                  }}
                >
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </Box>
              <Button 
                startIcon={<RefreshIcon />} 
                size="small" 
                onClick={refreshData}
                variant="outlined"
              >
                Refresh
              </Button>
            </Box>
          </Box>
        </Grid>
        
        <Grid item xs={12}>
          {activeTab === 'gainers' && (
            <Paper elevation={1} sx={{ p: 0 }}>
              <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight="medium">Top Gainers</Typography>
                <Chip 
                  label={`${topGainers.length} stocks`} 
                  size="small" 
                  color="success" 
                  sx={{ fontWeight: 500 }}
                />
              </Box>
              {renderStockList(topGainers, loading, error)}
            </Paper>
          )}
          
          {activeTab === 'losers' && (
            <Paper elevation={1} sx={{ p: 0 }}>
              <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight="medium">Top Losers</Typography>
                <Chip 
                  label={`${topLosers.length} stocks`} 
                  size="small" 
                  color="error" 
                  sx={{ fontWeight: 500 }}
                />
              </Box>
              {renderStockList(topLosers, loading, error)}
            </Paper>
          )}
          
          {activeTab === 'most-active' && (
            <Paper elevation={1} sx={{ p: 0 }}>
              <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6" fontWeight="medium">Most Active</Typography>
                <Chip 
                  label={`${mostActive.length} stocks`} 
                  size="small" 
                  color="primary" 
                  sx={{ fontWeight: 500 }}
                />
              </Box>
              {renderStockList(mostActive, loading, error)}
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
