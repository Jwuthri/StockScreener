import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as THREE from 'three';
import { 
  Box, Typography, Grid, Paper, 
  CircularProgress, Button, Chip, Alert, Tabs, Tab,
  IconButton, Tooltip, useTheme
} from '@mui/material';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import ViewInArIcon from '@mui/icons-material/ViewInAr';
import NotificationsNoneOutlinedIcon from '@mui/icons-material/NotificationsNoneOutlined';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import StarIcon from '@mui/icons-material/Star';
import ShareIcon from '@mui/icons-material/Share';
import { alpha, styled } from '@mui/material/styles';
import axios from 'axios';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip as RechartsTooltip, ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import StockChart3D from '../components/StockChart3D';
import StockChartFallback from '../components/StockChartFallback';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Styled components
const StyledPaper = styled(Paper)(({ theme }) => ({
  borderRadius: 16,
  boxShadow: 'none',
  border: `1px solid ${alpha(theme.palette.divider, 0.6)}`,
  overflow: 'hidden'
}));

const StyledTab = styled(Tab)(({ theme }) => ({
  fontWeight: 500,
  textTransform: 'none',
  minHeight: 48,
  fontSize: '0.875rem'
}));

const PriceSection = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  marginBottom: theme.spacing(3)
}));

const MetricBox = styled(Box)(({ theme, isPositive }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  padding: '4px 12px',
  borderRadius: 4,
  backgroundColor: isPositive 
    ? alpha(theme.palette.success.main, 0.1)
    : alpha(theme.palette.error.main, 0.1),
  color: isPositive ? theme.palette.success.main : theme.palette.error.main,
  fontWeight: 600
}));

const StockDetail = () => {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  
  const [loading, setLoading] = useState(true);
  const [stockData, setStockData] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [use3DFallback, setUse3DFallback] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [chartTimeRange, setChartTimeRange] = useState('1D');
  
  useEffect(() => {
    const fetchStockDetails = async () => {
      setLoading(true);
      setError('');
      
      try {
        // Fetch stock details
        const stockResponse = await axios.get(`${API_URL}/api/stocks/details/${symbol}`);
        setStockData(stockResponse.data);
        
        // Fetch price history
        const historyResponse = await axios.get(`${API_URL}/api/stocks/history/${symbol}?period=1mo`);
        setPriceHistory(historyResponse.data.price_history);
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching stock details:', error);
        setError('Failed to load stock data. Please try again later.');
        
        // Demo data for development
        setStockData({
          symbol: symbol,
          name: `${symbol} Inc.`,
          sector: 'Technology',
          industry: 'Software',
          price: 156.78,
          change: 2.34,
          change_percent: 1.52,
          market_cap: 2400000000000,
          pe_ratio: 28.6,
          dividend_yield: 0.68,
          volume: 45000000,
          avg_volume: 52000000,
          high_52week: 180.25,
          low_52week: 120.18,
          open: 154.20,
          previous_close: 154.44
        });
        
        // Generate sample price history
        const sampleHistory = generateSamplePriceHistory(30);
        setPriceHistory(sampleHistory);
        
        setLoading(false);
      }
    };
    
    fetchStockDetails();
    
    // Check if we should use fallback based on prior errors
    const hasThreeError = localStorage.getItem('useChartFallback') === 'true';
    setUse3DFallback(hasThreeError);
    
    // Check if stock is in favorites
    const favorites = JSON.parse(localStorage.getItem('favoriteStocks') || '[]');
    setIsFavorite(favorites.includes(symbol));
    
  }, [symbol]);
  
  // Add a new useEffect to update chart data when timeframe changes
  useEffect(() => {
    const fetchChartData = async () => {
      if (!symbol || loading) return;
      
      try {
        console.log(`Fetching chart data for ${symbol} with timeframe ${chartTimeRange}`);
        // Map from UI timeframe to API timeframe format
        const timeframeMap = {
          '1D': '1D',
          '1W': '5D',
          '1M': '1M',
          '3M': '3M',
          '1Y': '1Y',
          'All': '5Y'
        };
        
        const apiTimeframe = timeframeMap[chartTimeRange] || '1D';
        const chartResponse = await axios.get(`${API_URL}/api/stocks/chart/${symbol}?timeframe=${apiTimeframe}`);
        
        if (chartResponse.data && chartResponse.data.data) {
          // Transform data for LineChart
          const formattedData = chartResponse.data.data.map(point => {
            // Ensure time is a proper Date object by multiplying by 1000 if it's in seconds
            const timestamp = point.time * 1000; // Convert to milliseconds if in seconds
            return {
              date: new Date(timestamp).toISOString(),
              close: point.price,
              volume: point.volume
            };
          });
          
          console.log(`Received ${formattedData.length} data points for chart`);
          console.log(`Sample data point:`, formattedData[0]);
          setPriceHistory(formattedData);
        }
      } catch (error) {
        console.error(`Error fetching chart data: ${error}`);
      }
    };
    
    fetchChartData();
  }, [symbol, chartTimeRange, loading]);
  
  const generateSamplePriceHistory = (days) => {
    const data = [];
    const now = new Date();
    let basePrice = 150;
    
    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Add some random variation to price
      const randomChange = (Math.random() - 0.5) * 4;
      basePrice += randomChange;
      
      data.push({
        date: date.toISOString().split('T')[0],
        close: basePrice,
        open: basePrice - (Math.random() * 2),
        high: basePrice + (Math.random() * 2),
        low: basePrice - (Math.random() * 2),
        volume: Math.floor(Math.random() * 10000000) + 40000000
      });
    }
    
    return data;
  };
  
  // Transform price history data for 3D visualization
  const get3DChartData = () => {
    return priceHistory.map((item, index) => ({
      value: item.close,
      isHighlighted: index === priceHistory.length - 1 || 
                     (index > 0 && Math.abs(item.close - priceHistory[index - 1].close) > 3)
    }));
  };
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  const handle3DError = () => {
    console.warn('Error loading 3D chart, using fallback');
    setUse3DFallback(true);
    localStorage.setItem('useChartFallback', 'true');
  };
  
  const formatLargeNumber = (num) => {
    if (num >= 1000000000000) {
      return `$${(num / 1000000000000).toFixed(2)}T`;
    } else if (num >= 1000000000) {
      return `$${(num / 1000000000).toFixed(2)}B`;
    } else if (num >= 1000000) {
      return `$${(num / 1000000).toFixed(2)}M`;
    } else {
      return `$${num.toLocaleString()}`;
    }
  };
  
  const formatNumber = (num) => {
    return num ? num.toLocaleString() : 'N/A';
  };
  
  const toggleFavorite = () => {
    const favorites = JSON.parse(localStorage.getItem('favoriteStocks') || '[]');
    
    if (isFavorite) {
      const newFavorites = favorites.filter(fav => fav !== symbol);
      localStorage.setItem('favoriteStocks', JSON.stringify(newFavorites));
    } else {
      favorites.push(symbol);
      localStorage.setItem('favoriteStocks', JSON.stringify(favorites));
    }
    
    setIsFavorite(!isFavorite);
  };
  
  // Find min and max for the chart
  const calculatePriceRange = () => {
    if (!priceHistory || priceHistory.length === 0) return { min: 0, max: 100 };
    
    const prices = priceHistory.map(d => d.close);
    const min = Math.min(...prices) * 0.995; // 0.5% below minimum
    const max = Math.max(...prices) * 1.005; // 0.5% above maximum
    
    return { min, max };
  };
  
  const customTooltipFormatter = (value, name) => {
    if (name === 'close') return ['$' + value.toFixed(2), 'Price'];
    return [value, name];
  };

  const timeRangeButtons = ['1D', '1W', '1M', '3M', '1Y', 'All'];
  
  return (
    <Box>
      {loading ? (
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          height: '70vh',
          flexDirection: 'column',
          gap: 2
        }}>
          <CircularProgress size={40} sx={{ color: theme.palette.grey[800] }} />
          <Typography variant="body2" color="text.secondary">
            Loading {symbol} data...
          </Typography>
        </Box>
      ) : error && !stockData ? (
        <Alert 
          severity="error" 
          sx={{ 
            my: 2,
            borderRadius: theme.shape.borderRadius * 2
          }}
        >
          {error}
        </Alert>
      ) : stockData && (
        <>
          {/* Stock Header */}
          <Box sx={{ mb: 4 }}>
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'flex-start',
              mb: 1
            }}>
              <Box>
                <Typography variant="h4" component="h1" fontWeight={600}>
                  {stockData.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {symbol} • {stockData.sector}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title={isFavorite ? "Remove from Watchlist" : "Add to Watchlist"}>
                  <IconButton 
                    onClick={toggleFavorite}
                    sx={{ 
                      color: isFavorite ? theme.palette.warning.main : theme.palette.text.secondary,
                    }}
                  >
                    {isFavorite ? <StarIcon /> : <StarBorderIcon />}
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Share">
                  <IconButton sx={{ color: theme.palette.text.secondary }}>
                    <ShareIcon />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Set Price Alert">
                  <IconButton 
                    sx={{ color: theme.palette.text.secondary }}
                    onClick={() => navigate(`/alerts?stock=${symbol}`)}
                  >
                    <NotificationsNoneOutlinedIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            
            {/* Price Display */}
            <PriceSection>
              <Typography 
                variant="h3" 
                fontWeight={700} 
                sx={{ mb: 0.5 }}
              >
                ${stockData.price?.toFixed(2)}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <MetricBox isPositive={stockData.change_percent > 0}>
                  {stockData.change_percent > 0 ? (
                    <KeyboardArrowUpIcon fontSize="small" sx={{ mr: 0.5 }} />
                  ) : (
                    <KeyboardArrowDownIcon fontSize="small" sx={{ mr: 0.5 }} />
                  )}
                  {stockData.change > 0 ? '+' : ''}{stockData.change?.toFixed(2)} ({stockData.change_percent > 0 ? '+' : ''}{stockData.change_percent?.toFixed(2)}%)
                </MetricBox>
                
                <Typography variant="body2" color="text.secondary">
                  Today
                </Typography>
              </Box>
            </PriceSection>
          </Box>
          
          {/* Chart */}
          <StyledPaper sx={{ mb: 4, p: 0 }}>
            {/* Chart Time Range Selector */}
            <Box 
              sx={{ 
                display: 'flex', 
                borderBottom: `1px solid ${theme.palette.divider}`,
                px: 3,
                py: 1.5
              }}
            >
              {timeRangeButtons.map((range) => (
                <Button
                  key={range}
                  onClick={() => setChartTimeRange(range)}
                  sx={{
                    minWidth: 40,
                    px: 1.5,
                    py: 0.5,
                    borderRadius: 1.5,
                    mx: 0.5,
                    color: chartTimeRange === range ? 'white' : 'text.secondary',
                    backgroundColor: chartTimeRange === range 
                      ? stockData.change_percent > 0 
                        ? 'success.main' 
                        : 'error.main'
                      : 'transparent',
                    fontWeight: 500,
                    fontSize: '0.8rem',
                    '&:hover': {
                      backgroundColor: chartTimeRange === range 
                        ? stockData.change_percent > 0 
                          ? 'success.dark' 
                          : 'error.dark'
                        : alpha(theme.palette.grey[500], 0.1)
                    }
                  }}
                >
                  {range}
                </Button>
              ))}
              
              <Box sx={{ flexGrow: 1 }} />
              
              <Button
                variant="text"
                color="inherit"
                onClick={() => setTabValue(1)}
                startIcon={<ViewInArIcon />}
                sx={{ 
                  color: 'text.secondary',
                  '&:hover': { backgroundColor: alpha(theme.palette.grey[500], 0.1) }
                }}
              >
                3D View
              </Button>
            </Box>
            
            {/* Price Chart */}
            <Box sx={{ p: 3, pt: 1 }}>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart 
                  data={priceHistory}
                  margin={{ top: 20, right: 5, left: 5, bottom: 5 }}
                >
                  <XAxis 
                    dataKey="date" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    tickMargin={10}
                    tickFormatter={(value) => {
                      try {
                        const date = new Date(value);
                        if (chartTimeRange === '1D') {
                          // Format time as HH:MM for 1D view
                          return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
                        }
                        if (chartTimeRange === '1W' || chartTimeRange === '1M') {
                          return date.getDate(); // Return day of month for 1W and 1M
                        }
                        // For other ranges format as MMM DD
                        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                      } catch (e) {
                        console.error("Date formatting error:", e, value);
                        return "";
                      }
                    }}
                  />
                  <YAxis 
                    domain={[calculatePriceRange().min, calculatePriceRange().max]} 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 12, fill: theme.palette.text.secondary }}
                    tickFormatter={(value) => `$${value.toFixed(0)}`}
                    tickMargin={10}
                    tickCount={6}
                    orientation="right"
                  />
                  <CartesianGrid 
                    stroke={alpha(theme.palette.divider, 0.5)} 
                    strokeDasharray="5 5" 
                    vertical={false}
                  />
                  <RechartsTooltip 
                    formatter={customTooltipFormatter}
                    labelFormatter={(label) => {
                      const date = new Date(label);
                      return date.toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric',
                        year: chartTimeRange === '1Y' || chartTimeRange === 'All' ? 'numeric' : undefined
                      });
                    }}
                    contentStyle={{ 
                      backgroundColor: 'white',
                      borderRadius: 8,
                      border: 'none',
                      boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
                      padding: '8px 12px',
                    }}
                  />
                  <ReferenceLine 
                    y={stockData.previous_close} 
                    stroke={theme.palette.grey[400]} 
                    strokeDasharray="3 3" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="close" 
                    stroke={stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main} 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ 
                      r: 6, 
                      stroke: 'white', 
                      strokeWidth: 2, 
                      fill: stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main 
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          </StyledPaper>
          
          {/* Key Stats */}
          <Typography variant="h6" fontWeight={600} sx={{ mb: 2 }}>
            Key Statistics
          </Typography>
          
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Open
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {stockData.open ? `$${stockData.open.toFixed(2)}` : 'N/A'}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Previous Close
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {stockData.previous_close ? `$${stockData.previous_close.toFixed(2)}` : 'N/A'}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Day Range
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {stockData.price && stockData.change ? 
                    `$${(stockData.price - Math.abs(stockData.change) * 0.8).toFixed(2)} - $${(stockData.price + Math.abs(stockData.change) * 0.2).toFixed(2)}` : 
                    'N/A'}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  52W Range
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {stockData.low_52week && stockData.high_52week ? 
                    `$${stockData.low_52week.toFixed(2)} - $${stockData.high_52week.toFixed(2)}` : 
                    'N/A'}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Volume
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {formatNumber(stockData.volume)}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Avg. Volume
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {formatNumber(stockData.avg_volume)}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  Market Cap
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {formatLargeNumber(stockData.market_cap)}
                </Typography>
              </StyledPaper>
            </Grid>
            
            <Grid item xs={6} sm={3}>
              <StyledPaper sx={{ p: 2, height: '100%' }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  P/E Ratio
                </Typography>
                <Typography variant="subtitle1" fontWeight={600}>
                  {stockData.pe_ratio?.toFixed(2)}
                </Typography>
              </StyledPaper>
            </Grid>
          </Grid>
          
          {/* Tabs */}
          <StyledPaper sx={{ mb: 3, overflow: 'hidden' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="stock details tabs"
              sx={{
                borderBottom: `1px solid ${theme.palette.divider}`,
                '& .MuiTabs-indicator': {
                  backgroundColor: stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main,
                }
              }}
            >
              <StyledTab icon={<ShowChartIcon />} iconPosition="start" label="Chart" />
              <StyledTab icon={<ViewInArIcon />} iconPosition="start" label="3D View" />
              <StyledTab icon={<InfoOutlinedIcon />} iconPosition="start" label="About" />
            </Tabs>
            
            {tabValue === 0 && (
              <Box sx={{ p: 3 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                  Price Chart
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  This chart shows the historical price movement of {stockData.name} ({symbol}) stock. 
                  You can adjust the time range using the buttons above the chart.
                </Typography>
              </Box>
            )}
            
            {tabValue === 1 && (
              <Box sx={{ p: 3 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                  3D Price Visualization
                </Typography>
                
                <StyledPaper 
                  elevation={0} 
                  sx={{ 
                    height: 400, 
                    width: '100%', 
                    p: 1, 
                    bgcolor: alpha(theme.palette.background.paper, 0.5),
                    border: `1px solid ${alpha(theme.palette.divider, 0.5)}`,
                    borderRadius: 3
                  }}
                >
                  {use3DFallback ? (
                    <StockChartFallback data={get3DChartData()} height={370} />
                  ) : (
                    <ErrorBoundary 
                      fallback={<StockChartFallback data={get3DChartData()} height={370} />}
                      onError={handle3DError}
                    >
                      <StockChart3D data={get3DChartData()} height={370} />
                    </ErrorBoundary>
                  )}
                </StyledPaper>
                
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ 
                    mt: 2, 
                    textAlign: 'center',
                    fontSize: '0.8rem'
                  }}
                >
                  {use3DFallback ? 
                    'Enhanced 3D-style visualization of price movement over time' : 
                    'Tip: Click and drag to rotate the view. Scroll to zoom in and out.'}
                </Typography>
              </Box>
            )}
            
            {tabValue === 2 && (
              <Box sx={{ p: 3 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
                  About {stockData.name}
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Box>
                      <Typography variant="body2" color="text.secondary" paragraph>
                        {stockData.name} ({symbol}) is a {stockData.industry} company in the {stockData.sector} sector.
                        The company has a market cap of {formatLargeNumber(stockData.market_cap)}.
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" paragraph>
                        The stock has a P/E ratio of {stockData.pe_ratio?.toFixed(2)}, 
                        and a dividend yield of {stockData.dividend_yield?.toFixed(2)}%.
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary">
                        This stock has traded between ${stockData.low_52week?.toFixed(2)} and ${stockData.high_52week?.toFixed(2)} 
                        over the past 52 weeks.
                      </Typography>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Box sx={{ pl: { md: 2 }, borderLeft: { md: `1px solid ${theme.palette.divider}` } }}>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          Industry
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {stockData.industry}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          Sector
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          {stockData.sector}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          Exchange
                        </Typography>
                        <Typography variant="body1" fontWeight={500}>
                          NASDAQ
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            )}
          </StyledPaper>
          
          <Box sx={{ mb: 4 }}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ 
                py: 1.2,
                borderColor: stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main,
                color: stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main,
                borderWidth: 1.5,
                fontWeight: 600,
                '&:hover': {
                  borderWidth: 1.5,
                  backgroundColor: alpha(stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main, 0.05),
                  borderColor: stockData.change_percent > 0 ? theme.palette.success.main : theme.palette.error.main,
                }
              }}
            >
              Buy {symbol}
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
};

// Error boundary component to catch Three.js errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("3D chart error:", error, errorInfo);
    if (this.props.onError) {
      this.props.onError();
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}

export default StockDetail;
