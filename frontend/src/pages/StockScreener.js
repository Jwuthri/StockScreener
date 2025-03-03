import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, Paper, Table, 
  TableBody, TableCell, TableContainer, TableHead, 
  TableRow, CircularProgress, Grid, FormControl,
  InputLabel, Select, MenuItem, Chip, Slider, 
  ToggleButtonGroup, ToggleButton, FormControlLabel,
  Switch, Divider, Alert, Container, Accordion,
  AccordionSummary, AccordionDetails, Tabs, Tab,
  Checkbox, InputAdornment, Autocomplete, IconButton,
  Tooltip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import BarChartIcon from '@mui/icons-material/BarChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import ClearIcon from '@mui/icons-material/Clear';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
import { debounce } from 'lodash';
import NotificationsIcon from '@mui/icons-material/Notifications';
import LaunchIcon from '@mui/icons-material/Launch';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import SearchOffIcon from '@mui/icons-material/SearchOff';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const StockScreener = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [stocks, setStocks] = useState([]);
  const [rawStocksData, setRawStocksData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [popularStocks, setPopularStocks] = useState([]);
  const [sector, setSector] = useState('');
  const [sectors, setSectors] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [error, setError] = useState('');
  
  // Advanced filter states
  const [priceRange, setPriceRange] = useState([0, 50]);
  const [changeRange, setChangeRange] = useState([-10, 10]);
  const [minVolume, setMinVolume] = useState(100000);
  const [showPositiveCandles, setShowPositiveCandles] = useState(false);
  const [showPrevDayHighCross, setShowPrevDayHighCross] = useState(true);
  const [timeframe, setTimeframe] = useState("5m");
  const [numCandles, setNumCandles] = useState(3);
  const [positiveCandleStocks, setPositiveCandleStocks] = useState([]);
  
  // Add date state
  const [selectedDate, setSelectedDate] = useState(null);
  
  // Enhanced filter states
  const [selectedFilterTab, setSelectedFilterTab] = useState(0);
  
  // Enhanced volume filter options
  const [volumeRange, setVolumeRange] = useState([100000, 10000000]);
  const [maxVolumeOption, setMaxVolumeOption] = useState(10000000);
  
  // Enhanced price filter options
  const [priceFilterType, setPriceFilterType] = useState("range"); // "range" or "above" or "below"
  const [priceAbove, setPriceAbove] = useState(5);
  const [priceBelow, setPriceBelow] = useState(100);
  
  // Enhanced change filter options
  const [changeFilterType, setChangeFilterType] = useState("any"); // "any" or "up" or "down"
  const [changeMin, setChangeMin] = useState(1);
  const [changeMax, setChangeMax] = useState(10);
  
  // Enhanced Industry filter
  const [industry, setIndustry] = useState('');
  const [industries, setIndustries] = useState([]);
  
  // Exchange filter
  const [exchange, setExchange] = useState('');
  const [exchanges, setExchanges] = useState(['NYSE', 'NASDAQ', 'AMEX', 'OTC']);
  
  // Add new state for previous day high cross option in advanced filters
  const [includePrevDayHighCross, setIncludePrevDayHighCross] = useState(false);
  
  // Add state to control advanced filters in Previous Day High Cross screener
  const [showAdvancedInPDHC, setShowAdvancedInPDHC] = useState(false);
  
  // Add state to control advanced filters in Consecutive Positive Candles screener
  const [showAdvancedInPC, setShowAdvancedInPC] = useState(false);
  
  // Add new state variables for search UI
  const [searchFocused, setSearchFocused] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [topSymbols, setTopSymbols] = useState(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']);
  
  // Add a new state variable for result limit
  const [maxResults, setMaxResults] = useState(15);
  
  // Fetch popular stocks on component mount
  useEffect(() => {
    const fetchPopularStocks = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/api/stocks/popular`);
        setPopularStocks(response.data.popular_stocks);
        
        // Extract unique sectors for filter
        const uniqueSectors = [...new Set(response.data.popular_stocks
          .filter(stock => stock.sector)
          .map(stock => stock.sector))];
        setSectors(uniqueSectors);
        
        // Extract unique industries for filter if available
        const uniqueIndustries = [...new Set(response.data.popular_stocks
          .filter(stock => stock.industry)
          .map(stock => stock.industry))];
        setIndustries(uniqueIndustries);
        
        setStocks(response.data.popular_stocks);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching popular stocks:', error);
        setLoading(false);
      }
    };
    
    fetchPopularStocks();
  }, []);
  
  // Fetch search suggestions based on input
  const fetchSearchSuggestions = debounce(async (query) => {
    if (!query || query.length < 2) {
      setSearchSuggestions([]);
      return;
    }
    
    try {
      setIsSearching(true);
      const response = await axios.get(`${API_URL}/api/stocks/search?query=${query}`);
      if (response.data && Array.isArray(response.data)) {
        setSearchSuggestions(response.data.slice(0, 10));
      }
    } catch (error) {
      console.error('Error fetching search suggestions:', error);
    } finally {
      setIsSearching(false);
    }
  }, 300);
  
  // Handle search input change
  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    fetchSearchSuggestions(query);
  };
  
  // Clear search
  const handleClearSearch = () => {
    setSearchQuery('');
    setSearchSuggestions([]);
  };
  
  // Handle search submission
  const handleSearchSubmit = async (symbol = searchQuery) => {
    if (!symbol) return;
    
    // Add to recent searches if not already present
    if (!recentSearches.includes(symbol)) {
      const updatedRecentSearches = [symbol, ...recentSearches].slice(0, 5);
      setRecentSearches(updatedRecentSearches);
      localStorage.setItem('recentStockSearches', JSON.stringify(updatedRecentSearches));
    }
    
    // Execute search
    try {
      setLoading(true);
      setError('');
      
      const response = await axios.get(`${API_URL}/api/stocks/info/${symbol}`);
      if (response.data) {
        setStocks([response.data]);
      } else {
        setStocks([]);
        setError(`No results found for "${symbol}"`);
      }
      
      setLastUpdated(new Date());
      setSearchQuery('');
    } catch (error) {
      console.error('Error searching for stock:', error);
      setError(`Error searching for "${symbol}". Please try again.`);
      setStocks([]);
    } finally {
      setLoading(false);
    }
  };
  
  // Helper function to debounce API calls
  function debounce(func, wait) {
    let timeout;
    return function(...args) {
      const context = this;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
  }
  
  // Load recent searches from localStorage on mount
  useEffect(() => {
    const savedSearches = localStorage.getItem('recentStockSearches');
    if (savedSearches) {
      try {
        setRecentSearches(JSON.parse(savedSearches));
      } catch (e) {
        console.error('Error parsing saved searches:', e);
      }
    }
  }, []);
  
  const handleFilterSearch = async () => {
    // Call the handlePrevDayHighCrossSearch function directly
    return handlePrevDayHighCrossSearch();
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearchSubmit();
    }
  };
  
  const handleSectorChange = (e) => {
    setSector(e.target.value);
  };
  
  const handlePriceRangeChange = (event, newValue) => {
    setPriceRange(newValue);
  };
  
  const handleChangeRangeChange = (event, newValue) => {
    setChangeRange(newValue);
  };
  
  const handleVolumeChange = (event) => {
    setMinVolume(event.target.value === '' ? 0 : Number(event.target.value));
  };
  
  const filteredStocks = sector && !showPositiveCandles
    ? stocks.filter(stock => stock.sector === sector)
    : stocks;
  
  const navigateToStockDetails = (symbol) => {
    navigate(`/stock/${symbol}`);
  };
  
  const navigateToAlerts = (symbol) => {
    navigate(`/alerts?stock=${symbol}`);
  };
  
  const refreshData = async () => {
    setLoading(true);
    if (showPositiveCandles) {
      await handlePositiveCandlesSearch();
    } else if (showPrevDayHighCross) {
      await handlePrevDayHighCrossSearch();
    } else {
      // If we get here, use the implementation of handleFilterSearch
      await handlePrevDayHighCrossSearch();
    }
    setLastUpdated(new Date());
    setLoading(false);
  };
  
  const formatPercentage = (value) => `${value}%`;
  
  const handlePositiveCandlesSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      const endpoint = `${API_URL}/api/stocks/screener/consecutive-positive`;
      
      const params = {
        timeframe,
        num_candles: numCandles,
        limit: maxResults
      };
      
      // Only add advanced filter parameters if advanced filters are shown
      if (showAdvancedInPC) {
        // Price filter
        if (priceFilterType === "range") {
          params.min_price = priceRange[0];
          params.max_price = priceRange[1];
        } else if (priceFilterType === "above") {
          params.min_price = priceAbove;
        } else if (priceFilterType === "below") {
          params.max_price = priceBelow;
        }
        
        // Change % filter
        if (changeFilterType === "up") {
          params.min_change_percent = changeMin;
        } else if (changeFilterType === "down") {
          params.max_change_percent = -changeMin;
        } else {
          if (changeRange[0] !== -10) {
            params.min_change_percent = changeRange[0];
          }
          if (changeRange[1] !== 10) {
            params.max_change_percent = changeRange[1];
          }
        }
        
        // Volume filter
        if (volumeRange[0]) {
          params.min_volume = Number(String(volumeRange[0]).replace(/,/g, ''));
        }
        if (volumeRange[1]) {
          params.max_volume = Number(String(volumeRange[1]).replace(/,/g, ''));
        }
        
        // Add sector if selected
        if (sector) {
          params.sector = sector;
        }
        
        // Add industry if selected
        if (industry) {
          params.industry = industry;
        }
        
        // Add exchange if selected
        if (exchange) {
          params.exchange = exchange;
        }
      }
      
      console.log("Searching for stocks with consecutive positive candles with params:", params);
      console.log("Making API request to:", endpoint);
      
      const response = await axios.get(endpoint, { params });
      console.log("Full API Response:", response);
      console.log("API Response data:", response.data);
      
      if (response.data && response.data.stocks) {
        // Log the first stock for debugging
        console.log("First stock in response:", response.data.stocks[0]);
        
        const processedStocks = response.data.stocks.map(stock => {
          // Detailed logging for each stock
          console.log(`Processing stock ${stock.symbol}:`, {
            raw_price: stock.price,
            price_display: stock.price_display,
            raw_change_percent: stock.change_percent,
            change_percent_display: stock.change_percent_display,
            volume: stock.volume,
            volume_display: stock.volume_display
          });
          
          return {
            ...stock,
            // Use display values directly since they're already formatted correctly
            price: stock.price_display || 'N/A',
            change_percent: stock.change_percent_display || 'N/A',
            volume: stock.volume_display || 'N/A'
          };
        });
        
        console.log("Processed stocks:", processedStocks);
        setPositiveCandleStocks(processedStocks);
        setStocks(processedStocks);
      } else {
        console.log("No stocks found in response");
        setPositiveCandleStocks([]);
        setStocks([]);
        setError('No stocks found with consecutive positive candles. Try adjusting your parameters.');
      }
      
      setLastUpdated(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error finding stocks with consecutive positive candles:', error);
      setError('Error fetching stocks with consecutive positive candles.');
      setPositiveCandleStocks([]);
      setStocks([]);
      setLoading(false);
    }
  };
  
  const handleTimeframeChange = (e) => {
    setTimeframe(e.target.value);
  };
  
  const handleNumCandlesChange = (e) => {
    setNumCandles(Number(e.target.value));
  };
  
  // Add date handling functions
  const handleDateChange = (newDate) => {
    setSelectedDate(newDate);
  };
  
  const handlePrevDayHighCrossSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      const endpoint = `${API_URL}/api/stocks/screener/crossing-prev-day-high`;
      
      const params = {
        limit: maxResults  // Use the maxResults state variable instead of hardcoded 50
      };
      
      // Only add advanced filter parameters if advanced filters are shown
      if (showAdvancedInPDHC) {
        // Add price filters based on selected filter type
        if (priceFilterType === "range") {
          params.min_price = priceRange[0];
          params.max_price = priceRange[1];
        } else if (priceFilterType === "above") {
          params.min_price = priceAbove;
        } else if (priceFilterType === "below") {
          params.max_price = priceBelow;
        }
        
        // Add change percentage filters based on selected filter type
        if (changeFilterType === "any") {
          params.min_change_percent = changeRange[0];
          params.max_change_percent = changeRange[1];
        } else if (changeFilterType === "up") {
          params.min_change_percent = changeMin;
        } else if (changeFilterType === "down") {
          params.max_change_percent = -changeMin;
        }
        
        // Add volume filters - ensure they're clean numbers
        if (volumeRange[0]) {
          params.min_volume = Number(String(volumeRange[0]).replace(/,/g, ''));
        }
        
        if (volumeRange[1]) {
          params.max_volume = Number(String(volumeRange[1]).replace(/,/g, ''));
        }
        
        // Add sector if selected
        if (sector) {
          params.sector = sector;
        }
        
        // Add industry if selected
        if (industry) {
          params.industry = industry;
        }
        
        // Add exchange if selected
        if (exchange) {
          params.exchange = exchange;
        }
      }
      
      console.log("Searching for stocks crossing above previous day high with params:", params);
      try {
        console.log("Making API request to:", endpoint);
        const response = await axios.get(endpoint, { params });      
        console.log("Full API Response:", response);
        console.log("API Response data:", response.data);
        
        if (response.data.stocks && response.data.stocks.length > 0) {
          // Log the first stock for debugging
          console.log("First stock in response:", response.data.stocks[0]);
          
          const processedStocks = response.data.stocks.map(stock => {
            // Detailed logging for each stock
            console.log(`Processing stock ${stock.symbol}:`, {
              raw_price: stock.price,
              price_display: stock.price_display,
              raw_change_percent: stock.change_percent,
              change_percent_display: stock.change_percent_display,
              volume: stock.volume,
              volume_display: stock.volume_display
            });
            
            return {
              ...stock,
              // Use display values directly since they're already formatted correctly
              price: stock.price_display || 'N/A',
              change_percent: stock.change_percent_display || 'N/A',
              volume: stock.volume_display || 'N/A'
            };
          });
          
          console.log("Processed stocks:", processedStocks);
          setStocks(processedStocks);
        } else {
          console.log("No stocks found in response");
          setStocks([]);
        }
      } catch (error) {
        console.error("Error fetching stocks:", error);
        setStocks([]);
      }
      
      setLastUpdated(new Date());
      setLoading(false);
    } catch (error) {
      console.error('Error finding stocks crossing above previous day high:', error);
      setError('Error fetching stocks crossing above previous day high. Please try again.');
      setStocks([]);
      setLoading(false);
    }
  };
  
  // Now that handlePrevDayHighCrossSearch is defined, we can assign it
  // Add this line after the handlePrevDayHighCrossSearch function
  Object.assign(handleFilterSearch, { 
    implementation: handlePrevDayHighCrossSearch 
  });
  
  // Handle volume range change
  const handleVolumeRangeChange = (event, newValue) => {
    // Make sure the values are clean numbers
    const cleanValues = newValue.map(val => (
      typeof val === 'string' ? Number(val.replace(/,/g, '')) : val
    ));
    setVolumeRange(cleanValues);
  };
  
  // And when manually entering volume values
  const handleVolumeInputChange = (index, event) => {
    const value = event.target.value;
    // Remove commas and convert to number
    const numericValue = Number(String(value).replace(/,/g, ''));
    
    if (index === 0) {
      setVolumeRange([numericValue, volumeRange[1]]);
    } else {
      setVolumeRange([volumeRange[0], numericValue]);
    }
  };
  
  // Handle industry change
  const handleIndustryChange = (e) => {
    setIndustry(e.target.value);
  };
  
  // Handle exchange change
  const handleExchangeChange = (e) => {
    setExchange(e.target.value);
  };
  
  // Handle price filter type change
  const handlePriceFilterTypeChange = (event, newValue) => {
    if (newValue !== null) {
      setPriceFilterType(newValue);
    }
  };
  
  // Handle change filter type change
  const handleChangeFilterTypeChange = (event, newValue) => {
    if (newValue !== null) {
      setChangeFilterType(newValue);
    }
  };
  
  // Handle filter tab change
  const handleFilterTabChange = (event, newValue) => {
    setSelectedFilterTab(newValue);
  };
  
  // Format volume for display
  const formatVolume = (value) => {
    // If already formatted (includes K, M, or B), return as is
    if (typeof value === 'string' && (value.includes('K') || value.includes('M') || value.includes('B'))) {
      return value;
    }
    
    // Return N/A for null, undefined, or 0
    if (!value) {
      return 'N/A';
    }
    
    return value;
  };

  // Format percentage change values for display
  const formatPercentageChange = (value) => {
    // If already formatted (includes % or starts with + or -), return as is
    if (typeof value === 'string' && (value.includes('%') || value.startsWith('+') || value.startsWith('-'))) {
      return value;
    }
    
    // Return N/A for null or undefined
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    // Convert to number if not already
    const numValue = typeof value === 'number' ? value : Number(value);
    
    // If not a number, show N/A
    if (isNaN(numValue)) {
      return 'N/A';
    }
    
    // Format with sign and 2 decimal places
    return `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`;
  };

  // Format price for display
  const formatPrice = (value) => {
    // If already formatted (includes $ or currency formatting), return as is
    if (typeof value === 'string' && (value.includes('$') || value.includes('£') || value.includes('€'))) {
      return value;
    }
    
    // Return N/A for null or undefined
    if (value === null || value === undefined) {
      return 'N/A';
    }
    
    // Convert to number if not already
    const numValue = typeof value === 'number' ? value : Number(value);
    
    // If not a number, show N/A
    if (isNaN(numValue)) {
      return 'N/A';
    }
    
    // Format with dollar sign and 2 decimal places
    return `$${numValue.toFixed(2)}`;
  };
  
  // Add a handler for the results limit slider
  const handleMaxResultsChange = (event, newValue) => {
    setMaxResults(newValue);
  };

  // Values for max results slider
  const maxResultsMarks = [
    { value: 5, label: '5' },
    { value: 25, label: '25' },
    { value: 50, label: '50' },
    { value: 100, label: '100' },
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          borderRadius: 2,
          background: 'linear-gradient(to right, #f8f9fa, #e9ecef)',
          mb: 4 
        }}
      >
        <Typography 
          variant="h4" 
          gutterBottom 
          sx={{ 
            fontWeight: 600, 
            color: '#2c3e50',
            mb: 2,
            display: 'flex',
            alignItems: 'center' 
          }}
        >
          <ShowChartIcon sx={{ mr: 1, fontSize: 36 }} />
          Stock Screener
        </Typography>
        
        <Typography 
          variant="subtitle1" 
          gutterBottom 
          sx={{ 
            color: '#7f8c8d',
            mb: 3 
          }}
        >
          Find real-time stock opportunities with advanced filtering options
        </Typography>
        
        <Paper 
          elevation={searchFocused ? 8 : 2} 
          sx={{ 
            p: 0.5, 
            mb: 3, 
            transition: 'all 0.3s ease',
            borderRadius: 3,
            border: searchFocused ? '1px solid #3f51b5' : '1px solid #e0e0e0',
            boxShadow: searchFocused ? '0 4px 20px rgba(0, 0, 0, 0.1)' : 'none'
          }}
        >
          <Autocomplete
            freeSolo
            options={searchSuggestions}
            getOptionLabel={(option) => {
              if (typeof option === 'string') return option;
              return option.symbol || '';
            }}
            renderOption={(props, option) => {
              const stockOption = typeof option === 'string' 
                ? { symbol: option } 
                : option;
              
              return (
                <li {...props} style={{ padding: '8px 16px' }}>
                  <Grid container alignItems="center">
                    <Grid item xs>
                      <Typography variant="body1" fontWeight="bold">
                        {stockOption.symbol}
                      </Typography>
                      {stockOption.name && (
                        <Typography variant="body2" color="text.secondary">
                          {stockOption.name}
                        </Typography>
                      )}
                    </Grid>
                    {stockOption.sector && (
                      <Grid item>
                        <Chip 
                          label={stockOption.sector} 
                          size="small" 
                          sx={{ fontSize: '0.7rem', borderRadius: 1 }} 
                        />
                      </Grid>
                    )}
                  </Grid>
                </li>
              );
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="Search for stock symbols or companies..."
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
                variant="outlined"
                fullWidth
                InputProps={{
                  ...params.InputProps,
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="primary" sx={{ ml: 1 }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <>
                      {isSearching ? (
                        <CircularProgress color="inherit" size={20} />
                      ) : searchQuery ? (
                        <InputAdornment position="end">
                          <IconButton 
                            edge="end" 
                            onClick={handleClearSearch}
                            size="small"
                          >
                            <ClearIcon />
                          </IconButton>
                        </InputAdornment>
                      ) : null}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                  sx: { 
                    borderRadius: 3,
                    pl: 1,
                    pr: 1,
                    fontSize: '1.1rem'
                  }
                }}
                onKeyPress={handleKeyPress}
              />
            )}
            onChange={(event, value) => {
              if (value && typeof value === 'string') {
                handleSearchSubmit(value);
              } else if (value && value.symbol) {
                handleSearchSubmit(value.symbol);
              }
            }}
          />
        </Paper>
        
        <Box sx={{ mb: 2 }}>
          <Grid container spacing={1}>
            {/* Quick Search Chips */}
            {topSymbols.map((symbol) => (
              <Grid item key={symbol}>
                <Chip
                  label={symbol}
                  clickable
                  color="primary"
                  variant="outlined"
                  onClick={() => handleSearchSubmit(symbol)}
                  sx={{ 
                    borderRadius: 2,
                    '&:hover': { backgroundColor: 'rgba(63, 81, 181, 0.08)' }
                  }}
                />
              </Grid>
            ))}
            
            {/* Recent Searches */}
            {recentSearches.length > 0 && (
              <>
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }}>
                    <Chip 
                      label="Recent Searches" 
                      size="small" 
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }} 
                    />
                  </Divider>
                </Grid>
                {recentSearches.map((symbol) => (
                  <Grid item key={`recent-${symbol}`}>
                    <Chip
                      label={symbol}
                      size="small"
                      clickable
                      onClick={() => handleSearchSubmit(symbol)}
                      onDelete={() => {
                        const updated = recentSearches.filter(s => s !== symbol);
                        setRecentSearches(updated);
                        localStorage.setItem('recentStockSearches', JSON.stringify(updated));
                      }}
                      sx={{ 
                        borderRadius: 2,
                        bgcolor: 'rgba(0, 0, 0, 0.04)'
                      }}
                    />
                  </Grid>
                ))}
              </>
            )}
          </Grid>
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={refreshData}
            sx={{ borderRadius: 2 }}
          >
            Refresh Data
          </Button>
        </Box>
      </Paper>

      {/* Screener Options */}
      <Typography variant="h6" gutterBottom sx={{ mt: 4, mb: 2, fontWeight: 600 }}>
        Screener Options
      </Typography>
      
      {/* Add Max Results Slider in a nice card */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 2, background: 'linear-gradient(to right, #f8f9fa, #f5f5f5)' }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
              Maximum Results:
            </Typography>
          </Grid>
          <Grid item xs={12} sm={8}>
            <Box sx={{ px: 2 }}>
              <Slider
                value={maxResults}
                onChange={handleMaxResultsChange}
                min={5}
                max={100}
                step={null}
                marks={maxResultsMarks}
                valueLabelDisplay="auto"
                sx={{
                  '& .MuiSlider-thumb': {
                    height: 24,
                    width: 24,
                    backgroundColor: '#fff',
                    border: '2px solid currentColor',
                    '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
                      boxShadow: '0px 0px 0px 8px rgba(63, 81, 181, 0.16)',
                    },
                  }
                }}
              />
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Filter buttons - only keep two options with updated layout */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Button
            fullWidth
            variant={showPrevDayHighCross ? "contained" : "outlined"}
            startIcon={<TrendingUpIcon />}
            onClick={() => {
              setShowPositiveCandles(false);
              setShowPrevDayHighCross(true);
            }}
            sx={{ 
              py: 1.5,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              borderRadius: 2,
              height: '100%'
            }}
          >
            Stocks Crossing Previous Day High
          </Button>
        </Grid>
        <Grid item xs={12} md={6}>
          <Button
            fullWidth
            variant={showPositiveCandles ? "contained" : "outlined"}
            startIcon={<ShowChartIcon />}
            onClick={() => {
              setShowPositiveCandles(true);
              setShowPrevDayHighCross(false);
            }}
            sx={{ 
              py: 1.5,
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              borderRadius: 2,
              height: '100%'
            }}
          >
            Consecutive Positive Candles
          </Button>
        </Grid>
      </Grid>
      
      {/* Positive Candles Screener */}
      {showPositiveCandles && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Consecutive Positive Candles Screener</Typography>
          </Box>

          <Alert severity="info" sx={{ mb: 2 }}>
            This screener finds stocks that have {numCandles} consecutive positive candles (close &gt; open) on the {timeframe} timeframe.
            These stocks may be in a strong uptrend and could present trading opportunities.
          </Alert>
          
          <Grid container spacing={3}>
            {/* Timeframe Selection */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Timeframe</InputLabel>
                <Select
                  value={timeframe}
                  onChange={handleTimeframeChange}
                  label="Timeframe"
                >
                  <MenuItem value="1m">1 Minute</MenuItem>
                  <MenuItem value="5m">5 Minutes</MenuItem>
                  <MenuItem value="15m">15 Minutes</MenuItem>
                  <MenuItem value="30m">30 Minutes</MenuItem>
                  <MenuItem value="1h">1 Hour</MenuItem>
                  <MenuItem value="4h">4 Hours</MenuItem>
                  <MenuItem value="1d">1 Day</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {/* Number of Candles */}
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Consecutive Candles</InputLabel>
                <Select
                  value={numCandles}
                  onChange={handleNumCandlesChange}
                  label="Consecutive Candles"
                >
                  {[2, 3, 4, 5, 6, 7, 8, 9, 10].map(num => (
                    <MenuItem key={num} value={num}>{num} Candles</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            {/* Search Button */}
            <Grid item xs={12} md={4}>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={handlePositiveCandlesSearch}
                disabled={loading}
                sx={{ height: '56px' }}
              >
                {loading ? <CircularProgress size={24} /> : 'Find Stocks'}
              </Button>
            </Grid>
          </Grid>
          
          {/* Toggle for Advanced Filters */}
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            p: 2, 
            backgroundColor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
            borderRadius: 2,
            mb: 2,
            mt: 2
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="subtitle1" fontWeight={500}>
                Advanced Filters
              </Typography>
            </Box>
            <Switch 
              checked={showAdvancedInPC}
              onChange={(e) => setShowAdvancedInPC(e.target.checked)}
              color="primary"
              sx={{
                '& .MuiSwitch-switchBase.Mui-checked': {
                  color: 'primary.main',
                },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                  backgroundColor: 'primary.main',
                },
              }}
            />
          </Box>
          
          {/* Advanced Filters in Positive Candles Screener */}
          {showAdvancedInPC && (
            <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="subtitle1" gutterBottom>
                Narrow down stocks with consecutive positive candles:
              </Typography>
              
              <Tabs
                value={selectedFilterTab}
                onChange={handleFilterTabChange}
                sx={{ mb: 2 }}
              >
                <Tab label="Price" value="price" />
                <Tab label="Change %" value="change" />
                <Tab label="Volume" value="volume" />
                <Tab label="Sector" value="sector" />
              </Tabs>
              
              {selectedFilterTab === 'price' && (
                <Box sx={{ p: 1 }}>
                  <ToggleButtonGroup
                    value={priceFilterType}
                    exclusive
                    onChange={handlePriceFilterTypeChange}
                    sx={{ mb: 2, display: 'flex' }}
                  >
                    <ToggleButton value="range" sx={{ flex: 1 }}>Price Range</ToggleButton>
                    <ToggleButton value="above" sx={{ flex: 1 }}>Price Above</ToggleButton>
                    <ToggleButton value="below" sx={{ flex: 1 }}>Price Below</ToggleButton>
                  </ToggleButtonGroup>
                </Box>
              )}
              
              {selectedFilterTab === 'change' && (
                <Box sx={{ p: 1 }}>
                  <ToggleButtonGroup
                    value={changeFilterType}
                    exclusive
                    onChange={handleChangeFilterTypeChange}
                    sx={{ mb: 2, display: 'flex' }}
                  >
                    <ToggleButton value="any" sx={{ flex: 1 }}>Change Range</ToggleButton>
                    <ToggleButton value="up" sx={{ flex: 1 }}>Up by at least</ToggleButton>
                    <ToggleButton value="down" sx={{ flex: 1 }}>Down by at least</ToggleButton>
                  </ToggleButtonGroup>
                </Box>
              )}
              
              {selectedFilterTab === 'volume' && (
                <Box sx={{ p: 1 }}>
                  <Typography id="volume-range-slider" gutterBottom>
                    Volume Range: {formatVolume(volumeRange[0])} to {formatVolume(volumeRange[1])}
                  </Typography>
                  <Slider
                    value={volumeRange}
                    onChange={handleVolumeRangeChange}
                    valueLabelFormat={formatVolume}
                    valueLabelDisplay="auto"
                    min={0}
                    max={100000000}
                    step={1000000}
                    sx={{ width: '100%' }}
                  />
                </Box>
              )}
              
              {selectedFilterTab === 'sector' && (
                <Box sx={{ p: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Sector</InputLabel>
                        <Select
                          value={sector}
                          onChange={handleSectorChange}
                          label="Sector"
                        >
                          <MenuItem value="">
                            <em>All Sectors</em>
                          </MenuItem>
                          {sectors.map((sector) => (
                            <MenuItem key={sector} value={sector}>{sector}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Industry</InputLabel>
                        <Select
                          value={industry}
                          onChange={handleIndustryChange}
                          label="Industry"
                        >
                          <MenuItem value="">
                            <em>All Industries</em>
                          </MenuItem>
                          {industries.map((industryOption) => (
                            <MenuItem key={industryOption} value={industryOption}>
                              {industryOption}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Box>
          )}
        </Paper>
      )}
      
      {/* Update the Previous Day High Cross Screener section */}
      {showPrevDayHighCross && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Stocks Crossing Previous Day High Screener</Typography>
          </Box>
          
          <Alert severity="info" sx={{ mb: 2 }}>
            This screener finds stocks that have their current price crossing above the previous day's high.
            This can signal increased momentum and potential breakout opportunities.
          </Alert>
          
          {/* Add filter options in a grid like in the Consecutive Positive Candles section */}
          <Grid container spacing={3}>
            {/* No filters to select here, so let's use an informative text component */}
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 2, height: '56px', display: 'flex', alignItems: 'center', bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)' }}>
                <Typography variant="body1" color="text.secondary">
                  Finds stocks currently trading above their previous day's high
                </Typography>
              </Paper>
            </Grid>
            
            {/* Search Button */}
            <Grid item xs={12} md={4}>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={handlePrevDayHighCrossSearch}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                sx={{ height: '56px' }}
              >
                {loading ? 'Searching...' : 'Find Stocks'}
              </Button>
            </Grid>
          </Grid>
          
          {/* Toggle for Advanced Filters */}
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            p: 2, 
            backgroundColor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
            borderRadius: 2,
            mb: 2,
            mt: 2
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="subtitle1" fontWeight={500}>
                Advanced Filters
              </Typography>
            </Box>
            <Switch 
              checked={showAdvancedInPDHC}
              onChange={(e) => setShowAdvancedInPDHC(e.target.checked)}
              color="primary"
              sx={{
                '& .MuiSwitch-switchBase.Mui-checked': {
                  color: 'primary.main',
                },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': {
                  backgroundColor: 'primary.main',
                },
              }}
            />
          </Box>
          
          {/* Advanced Filters in PDHC */}
          {showAdvancedInPDHC && (
            <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="subtitle1" gutterBottom>
                Narrow down stocks crossing previous day high:
              </Typography>
              
              <Tabs
                value={selectedFilterTab}
                onChange={handleFilterTabChange}
                indicatorColor="primary"
                textColor="primary"
                variant="standard"
                sx={{ mb: 2 }}
              >
                <Tab label="Price" value="price" />
                <Tab label="Volume" value="volume" />
                <Tab label="Change %" value="change" />
                <Tab label="Sector" value="sector" />
              </Tabs>
              
              {selectedFilterTab === "price" && (
                <Box>
                  <Box sx={{ mb: 3 }}>
                    <ToggleButtonGroup
                      value={priceFilterType}
                      exclusive
                      onChange={handlePriceFilterTypeChange}
                      fullWidth
                      color="primary"
                      sx={{ mb: 2 }}
                    >
                      <ToggleButton value="range">Price Range</ToggleButton>
                      <ToggleButton value="above">Above Price</ToggleButton>
                      <ToggleButton value="below">Below Price</ToggleButton>
                    </ToggleButtonGroup>
                    
                    {priceFilterType === "range" && (
                      <>
                        <Typography gutterBottom>
                          Price Range: ${priceRange[0]} to ${priceRange[1]}
                        </Typography>
                        <Slider
                          value={priceRange}
                          onChange={handlePriceRangeChange}
                          valueLabelDisplay="auto"
                          min={0}
                          max={500}
                          step={1}
                        />
                      </>
                    )}
                    
                    {priceFilterType === "above" && (
                      <TextField
                        label="Price Above"
                        type="number"
                        value={priceAbove}
                        onChange={(e) => setPriceAbove(Number(e.target.value))}
                        fullWidth
                        InputProps={{
                          startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
                          inputProps: { min: 0 }
                        }}
                      />
                    )}
                    
                    {priceFilterType === "below" && (
                      <TextField
                        label="Price Below"
                        type="number"
                        value={priceBelow}
                        onChange={(e) => setPriceBelow(Number(e.target.value))}
                        fullWidth
                        InputProps={{
                          startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
                          inputProps: { min: 0 }
                        }}
                      />
                    )}
                  </Box>
                </Box>
              )}
              
              {selectedFilterTab === "volume" && (
                <Box>
                  <Typography gutterBottom>
                    Volume Range: {formatVolume(volumeRange[0])} to {formatVolume(volumeRange[1])}
                  </Typography>
                  <Slider
                    value={volumeRange}
                    onChange={handleVolumeRangeChange}
                    valueLabelDisplay="auto"
                    valueLabelFormat={formatVolume}
                    min={1000}
                    max={100000000}
                    step={10000}
                    scale={(x) => x}
                  />
                  
                  <Grid container spacing={2} sx={{ mt: 2 }}>
                    <Grid item xs={6}>
                      <TextField
                        label="Min Volume"
                        type="number"
                        value={volumeRange[0]}
                        onChange={(e) => handleVolumeInputChange(0, e)}
                        fullWidth
                        InputProps={{
                          inputProps: { min: 0 }
                        }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="Max Volume"
                        type="number"
                        value={volumeRange[1]}
                        onChange={(e) => handleVolumeInputChange(1, e)}
                        fullWidth
                        InputProps={{
                          inputProps: { min: 0 }
                        }}
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}
              
              {selectedFilterTab === "change" && (
                <Box>
                  <Box sx={{ mb: 3 }}>
                    <ToggleButtonGroup
                      value={changeFilterType}
                      exclusive
                      onChange={handleChangeFilterTypeChange}
                      fullWidth
                      color="primary"
                      sx={{ mb: 2 }}
                    >
                      <ToggleButton value="any">Any Change Range</ToggleButton>
                      <ToggleButton value="up">% Up Only</ToggleButton>
                      <ToggleButton value="down">% Down Only</ToggleButton>
                    </ToggleButtonGroup>
                    
                    {changeFilterType === "any" && (
                      <>
                        <Typography gutterBottom>
                          Change %: {changeRange[0]}% to {changeRange[1]}%
                        </Typography>
                        <Slider
                          value={changeRange}
                          onChange={handleChangeRangeChange}
                          valueLabelDisplay="auto"
                          valueLabelFormat={formatPercentage}
                          min={-20}
                          max={20}
                          step={0.5}
                        />
                      </>
                    )}
                    
                    {changeFilterType === "up" && (
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <TextField
                            label="Minimum % Change"
                            type="number"
                            value={changeMin}
                            onChange={(e) => setChangeMin(Number(e.target.value))}
                            fullWidth
                            InputProps={{
                              endAdornment: <Typography>%</Typography>,
                              inputProps: { min: 0 }
                            }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <TextField
                            label="Maximum % Change"
                            type="number"
                            value={changeMax}
                            onChange={(e) => setChangeMax(Number(e.target.value))}
                            fullWidth
                            InputProps={{
                              endAdornment: <Typography>%</Typography>,
                              inputProps: { min: 0 }
                            }}
                          />
                        </Grid>
                      </Grid>
                    )}
                    
                    {changeFilterType === "down" && (
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <TextField
                            label="Minimum % Down"
                            type="number"
                            value={changeMin}
                            onChange={(e) => setChangeMin(Number(e.target.value))}
                            fullWidth
                            InputProps={{
                              endAdornment: <Typography>%</Typography>,
                              inputProps: { min: 0 }
                            }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <TextField
                            label="Maximum % Down"
                            type="number"
                            value={changeMax}
                            onChange={(e) => setChangeMax(Number(e.target.value))}
                            fullWidth
                            InputProps={{
                              endAdornment: <Typography>%</Typography>,
                              inputProps: { min: 0 }
                            }}
                          />
                        </Grid>
                      </Grid>
                    )}
                  </Box>
                </Box>
              )}
              
              {selectedFilterTab === "sector" && (
                <Box sx={{ p: 1 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Sector</InputLabel>
                        <Select
                          value={sector}
                          onChange={handleSectorChange}
                          label="Sector"
                        >
                          <MenuItem value="">
                            <em>All Sectors</em>
                          </MenuItem>
                          {sectors.map((sector) => (
                            <MenuItem key={sector} value={sector}>{sector}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    {/* Industry Selection */}
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Industry</InputLabel>
                        <Select
                          value={industry}
                          onChange={handleIndustryChange}
                          label="Industry"
                        >
                          <MenuItem value="">
                            <em>All Industries</em>
                          </MenuItem>
                          {industries.map((ind) => (
                            <MenuItem key={ind} value={ind}>{ind}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    {/* Exchange Selection */}
                    <Grid item xs={12} md={12} sx={{ mt: 2 }}>
                      <FormControl fullWidth>
                        <InputLabel>Exchange</InputLabel>
                        <Select
                          value={exchange}
                          onChange={handleExchangeChange}
                          label="Exchange"
                        >
                          <MenuItem value="">
                            <em>All Exchanges</em>
                          </MenuItem>
                          {exchanges.map((ex) => (
                            <MenuItem key={ex} value={ex}>{ex}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Box>
          )}
        </Paper>
      )}
      
      {/* Add the results section for displaying fetched stocks */}
      {(stocks.length > 0 || loading) && (
        <Paper sx={{ p: 0, mt: 3, borderRadius: 2, overflow: 'hidden' }}>
          {/* Results Header */}
          <Box sx={{ 
            p: 2, 
            bgcolor: 'background.paper', 
            borderBottom: '1px solid', 
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                p: 1,
                bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
                borderRadius: 2,
                mr: 2
              }}>
                {loading ? (
                  <CircularProgress size={20} sx={{ mr: 1 }} />
                ) : (
                  <BarChartIcon color="primary" sx={{ mr: 1 }} />
                )}
                <Typography variant="h6" sx={{ fontWeight: 500 }}>
                  Results
                </Typography>
              </Box>
              
              {stocks.length > 0 && (
                <Chip 
                  label={`${stocks.length} found`} 
                  size="medium" 
                  color="primary" 
                  sx={{ borderRadius: '16px', fontWeight: 500 }} 
                />
              )}
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {lastUpdated && (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <AccessTimeIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                  <Typography variant="body2" color="text.secondary">
                    Updated {lastUpdated.toLocaleTimeString()}
                  </Typography>
                </Box>
              )}
              
              <Button 
                variant="outlined" 
                startIcon={<RefreshIcon />} 
                onClick={refreshData}
                size="small"
                sx={{ borderRadius: 8 }}
              >
                Refresh
              </Button>
            </Box>
          </Box>
          
          {/* Results Table */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
              <CircularProgress />
              <Typography variant="body1" color="text.secondary" sx={{ ml: 2 }}>
                Loading stocks...
              </Typography>
            </Box>
          ) : stocks.length > 0 ? (
            <Box sx={{ p: 0 }}>
              <TableContainer component={Box}>
                <Table size="medium">
                  <TableHead>
                    <TableRow sx={{ 
                      bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
                    }}>
                      <TableCell sx={{ fontWeight: 600, py: 1.5 }}>Symbol</TableCell>
                      <TableCell sx={{ fontWeight: 600, py: 1.5 }}>Name</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Price</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Change %</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Volume</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Sector</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600, py: 1.5 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stocks.map((stock) => (
                      <TableRow 
                        key={stock.symbol || `stock-${Math.random()}`}
                        hover
                        sx={{
                          '&:last-child td, &:last-child th': { border: 0 },
                          cursor: 'pointer',
                          transition: 'background-color 0.2s',
                          '&:hover': {
                            backgroundColor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
                          }
                        }}
                        onClick={() => navigateToStockDetails(stock.symbol)}
                      >
                        <TableCell component="th" scope="row" sx={{ py: 2 }}>
                          <Typography fontWeight="bold">{stock.symbol || 'N/A'}</Typography>
                        </TableCell>
                        <TableCell sx={{ py: 2 }}>{stock.name || 'N/A'}</TableCell>
                        <TableCell align="right" sx={{ py: 2 }}>
                          {(() => {
                            // Make sure we're handling all possible price formats
                            const price = stock.price !== undefined ? stock.price : (
                              stock.current_price !== undefined ? stock.current_price : (
                                stock.close !== undefined ? stock.close : null
                              )
                            );
                            return formatPrice(price);
                          })()}
                        </TableCell>
                        <TableCell 
                          align="right"
                          sx={{ 
                            py: 2,
                            color: (() => {
                              // Safely determine the color based on change_percent
                              const changePercent = stock.change_percent !== undefined ? stock.change_percent : (
                                stock.percent_change !== undefined ? stock.percent_change : (
                                  stock.change !== undefined ? stock.change : 0
                                )
                              );
                              const numValue = typeof changePercent === 'string' ? parseFloat(changePercent) : changePercent;
                              return !isNaN(numValue) && numValue >= 0 ? 'success.main' : 'error.main';
                            })(),
                            fontWeight: 'bold'
                          }}
                        >
                          {(() => {
                            // Make sure we're handling all possible change_percent formats
                            const changePercent = stock.change_percent !== undefined ? stock.change_percent : (
                              stock.percent_change !== undefined ? stock.percent_change : (
                                stock.change !== undefined ? stock.change : null
                              )
                            );
                            return formatPercentageChange(changePercent);
                          })()}
                        </TableCell>
                        <TableCell align="right" sx={{ py: 2 }}>
                          {formatVolume(stock.volume)}
                        </TableCell>
                        <TableCell align="right" sx={{ py: 2 }}>
                          <Chip 
                            label={stock.sector || 'N/A'} 
                            size="small" 
                            sx={{ 
                              borderRadius: '12px',
                              bgcolor: (theme) => 
                                stock.sector ? (theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)') 
                                  : 'transparent'
                            }} 
                          />
                        </TableCell>
                        <TableCell align="center" sx={{ py: 2 }}>
                          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                            <Tooltip title="Set alerts">
                              <IconButton 
                                size="small" 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigateToAlerts(stock.symbol);
                                }}
                                color="primary"
                                sx={{ bgcolor: 'rgba(63, 81, 181, 0.08)' }}
                              >
                                <NotificationsIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="View on Yahoo Finance">
                              <IconButton 
                                size="small" 
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(`https://finance.yahoo.com/quote/${stock.symbol}`, '_blank');
                                }}
                                color="secondary"
                                sx={{ bgcolor: 'rgba(245, 0, 87, 0.08)' }}
                              >
                                <OpenInNewIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          ) : (
            <Box sx={{ p: 4, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <SearchOffIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2, opacity: 0.5 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No stocks found
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center" sx={{ maxWidth: 500 }}>
                Try adjusting your search criteria or filters to find more stocks.
              </Typography>
              <Button 
                variant="outlined" 
                startIcon={<FilterListIcon />} 
                sx={{ mt: 2 }}
                onClick={() => {
                  if (showPositiveCandles) {
                    setShowAdvancedInPC(true);
                  } else if (showPrevDayHighCross) {
                    setShowAdvancedInPDHC(true);
                  }
                }}
              >
                Adjust Filters
              </Button>
            </Box>
          )}
          
          {/* Debug section - only show if needed */}
          {rawStocksData.length > 0 && (
            <Box sx={{ mt: 4, borderTop: '1px dashed #ccc', pt: 4, px: 3, pb: 3 }}>
              <Accordion sx={{ 
                boxShadow: 'none',
                '&:before': { display: 'none' },
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                mb: 2,
              }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle2" color="primary">
                    Debug Information
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ fontSize: '0.85rem' }}>
                    <pre style={{ whiteSpace: 'pre-wrap', overflow: 'auto', maxHeight: '300px', backgroundColor: '#f5f5f5', padding: 16, borderRadius: 4 }}>
                      {JSON.stringify(rawStocksData[0], null, 2)}
                    </pre>
                  </Box>
                </AccordionDetails>
              </Accordion>
              
              <Typography variant="caption" color="text.secondary">
                This debug information is only visible during development.
              </Typography>
            </Box>
          )}
        </Paper>
      )}
      
      {/* Show error message if there's an error */}
      {error && (
        <Alert severity="error" sx={{ mt: 3 }}>
          {error}
        </Alert>
      )}
    </Container>
  );
};

export default StockScreener;
