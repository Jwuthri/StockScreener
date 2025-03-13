import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Grid,
  Paper,
  CircularProgress,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import axios from 'axios';
import AdvancedFilters from '../components/AdvancedFilters';

// Create a cache outside the component to track when stocks were first seen
// This will persist even if the component re-renders
const NEW_STOCKS_CACHE = new Map();
const NEW_FLAG_DURATION = 2 * 60 * 1000; // 2 minutes in milliseconds

const StocksCrossingPrevHighPage = () => {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [hasNewNotification, setHasNewNotification] = useState(false);
  const [audioInitialized, setAudioInitialized] = useState(false);

  // Filter states
  const [selectedFilterTab, setSelectedFilterTab] = useState('price');
  const [priceFilterType, setPriceFilterType] = useState('range');
  const [priceRange, setPriceRange] = useState([0, 500]);
  const [priceAbove, setPriceAbove] = useState(0);
  const [priceBelow, setPriceBelow] = useState(1000);
  const [changeFilterType, setChangeFilterType] = useState('any');
  const [changeRange, setChangeRange] = useState([-10, 10]);
  const [changeMin, setChangeMin] = useState(0);
  const [changeMax, setChangeMax] = useState(100);
  const [volumeRange, setVolumeRange] = useState([100000, 10000000]);
  const [sector, setSector] = useState('');
  const [industry, setIndustry] = useState('');
  const [exchange, setExchange] = useState('');

  // Sectors, industries, and exchanges data
  const [sectors, setSectors] = useState([]);
  const [industries, setIndustries] = useState([]);
  const [exchanges, setExchanges] = useState(['NYSE', 'NASDAQ', 'AMEX']);

  // Force component to re-render
  const [forceUpdate, setForceUpdate] = useState(0);

  // Add this at the top of your component
  const [userInteracted, setUserInteracted] = useState(false);
  const audioRef = useRef(null);

  // Add an effect to listen for user interaction
  useEffect(() => {
    const handleUserInteraction = () => {
      setUserInteracted(true);
      // Remove the event listeners once user has interacted
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
    };

    document.addEventListener('click', handleUserInteraction);
    document.addEventListener('keydown', handleUserInteraction);

    return () => {
      document.removeEventListener('click', handleUserInteraction);
      document.removeEventListener('keydown', handleUserInteraction);
    };
  }, []);

  // Function to check if a stock should have the NEW flag
  const isStockNew = (symbol) => {
    if (!NEW_STOCKS_CACHE.has(symbol)) {
      return false;
    }

    const firstSeenTime = NEW_STOCKS_CACHE.get(symbol);
    const currentTime = Date.now();
    return (currentTime - firstSeenTime) < NEW_FLAG_DURATION;
  };

  // Function to clean up expired NEW flags
  const cleanupExpiredFlags = () => {
    console.log('Cleaning up expired NEW flags');
    const currentTime = Date.now();
    let hasChanges = false;

    // Check each stock in the cache
    NEW_STOCKS_CACHE.forEach((firstSeenTime, symbol) => {
      if ((currentTime - firstSeenTime) >= NEW_FLAG_DURATION) {
        console.log(`Removing NEW flag for ${symbol}`);
        NEW_STOCKS_CACHE.delete(symbol);
        hasChanges = true;
      }
    });

    // If we removed any flags, force a re-render
    if (hasChanges) {
      console.log('Forcing re-render after cleanup');
      setForceUpdate(prev => prev + 1);
    }
  };

  // Set up cleanup interval
  useEffect(() => {
    console.log('Setting up cleanup interval');
    const intervalId = setInterval(() => {
      cleanupExpiredFlags();
    }, 10000); // Check every 10 seconds

    return () => clearInterval(intervalId);
  }, []);

  // Add this useEffect to initialize audio properly
  useEffect(() => {
    // Create audio element only once
    if (!audioRef.current) {
      audioRef.current = new Audio('/notification.mp3');

      // Add event listeners for debugging
      audioRef.current.addEventListener('play', () => {
        console.log('Audio started playing');
      });

      audioRef.current.addEventListener('error', (e) => {
        console.error('Audio error:', e);
      });
    }

    return () => {
      // Cleanup
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.removeEventListener('play', () => {});
        audioRef.current.removeEventListener('error', () => {});
      }
    };
  }, []);

  // Function to play sound
  const playNotificationSound = () => {
    if (!audioRef.current || !soundEnabled) return;

    console.log('Attempting to play notification sound...');

    // Reset the audio to the beginning
    audioRef.current.currentTime = 0;

    // Set volume
    audioRef.current.volume = 0.5;

    // Play with promise handling
    const playPromise = audioRef.current.play();

    if (playPromise !== undefined) {
      playPromise
        .then(() => {
          console.log('Audio played successfully');
        })
        .catch(err => {
          console.error('Audio play failed:', err);
          // If it fails due to user interaction requirement, set a flag
          if (err.name === 'NotAllowedError') {
            setAudioInitialized(false);
          }
        });
    }
  };

  // Modified fetchStocks function
  const fetchStocks = async () => {
    setLoading(true);
    setError('');

    console.log('Attempting to fetch stocks...');

    try {
      // Define params object before using it
      const params = {
        min_price: priceFilterType === 'above' ? priceAbove :
                   priceFilterType === 'range' ? priceRange[0] : 0,
        max_price: priceFilterType === 'below' ? priceBelow :
                   priceFilterType === 'range' ? priceRange[1] : 500,
        min_change_percent: changeFilterType === 'down' ? -changeMax :
                            changeFilterType === 'any' ? changeRange[0] : changeMin,
        max_change_percent: changeFilterType === 'down' ? -changeMin :
                            changeFilterType === 'any' ? changeRange[1] : changeMax,
        min_volume: volumeRange[0],
        max_volume: volumeRange[1]
      };

      // Add optional parameters only if they have values
      if (sector) params.sector = sector;
      if (industry) params.industry = industry;
      if (exchange) params.exchange = exchange;

      console.log('Calling API with params:', params);

      // Use the correct endpoint
      const url = 'http://localhost:8000/api/stocks/screener/open-below-prev-high-and-crossed';
      console.log('Calling endpoint:', url);

      const response = await axios.get(url, { params });
      console.log('API response received:', response.data);

      // Get stocks data from response
      const stocksData = Array.isArray(response.data)
        ? response.data
        : response.data.stocks || [];

      // Check for new stocks and add them to the cache
      const currentTime = Date.now();
      let hasNewStocks = false;

      // Get the symbols we already have
      const existingSymbols = new Set(stocks.map(s => s.symbol));

      stocksData.forEach(stock => {
        const symbol = stock.symbol;

        // If this stock wasn't in our previous list and isn't in the cache
        if (!existingSymbols.has(symbol) && !NEW_STOCKS_CACHE.has(symbol)) {
          console.log(`New stock detected: ${symbol}`);
          NEW_STOCKS_CACHE.set(symbol, currentTime);
          hasNewStocks = true;
        }
      });

      if (hasNewStocks && soundEnabled && audioInitialized) {
        playNotificationSound();
      }

      // Sort stocks by freshness (newest first)
      const sortedStocks = stocksData.sort((a, b) => {
        const timeA = NEW_STOCKS_CACHE.get(a.symbol) || 0;
        const timeB = NEW_STOCKS_CACHE.get(b.symbol) || 0;
        return timeB - timeA;
      });

      // Process stocks and add isNew flag
      const processedStocks = sortedStocks.map(stock => {
        return {
          ...stock,
          isNew: isStockNew(stock.symbol)
        };
      });

      // Clean up any expired flags
      cleanupExpiredFlags();

      // Update stocks state
      setStocks(processedStocks);
      setLastUpdated(new Date());

    } catch (err) {
      console.error('Error details:', err);
      setError(`Failed to fetch stock data: ${err.message || 'Unknown error'}. Please try again.`);
    } finally {
      setLoading(false);
    }
  };

  // Initial data fetch
  useEffect(() => {
    fetchStocks();

    // Fetch sectors for filter
    axios.get('/api/stocks/sectors')
      .then(response => {
        if (response.data && Array.isArray(response.data)) {
          setSectors(response.data);
        }
      })
      .catch(err => console.error('Failed to fetch sectors:', err));

    // In a real app, you would also fetch industries
    setIndustries(['Software', 'Hardware', 'Semiconductors', 'Biotechnology', 'Banking', 'Insurance', 'Retail']);
  }, []);

  // Set up auto-refresh interval
  useEffect(() => {
    let intervalId = null;

    if (autoRefresh) {
      intervalId = setInterval(fetchStocks, 10000); // Refresh every 10 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [autoRefresh, priceFilterType, priceRange, priceAbove, priceBelow,
      changeFilterType, changeRange, changeMin, changeMax,
      volumeRange, sector, industry, exchange]);

  // Format helpers
  const formatPrice = (price) => `$${price}`;
  const formatPercentage = (percent) => `${percent}%`;
  const formatVolume = (volume) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  // Handle filter tab change
  const handleFilterTabChange = (event, newValue) => {
    setSelectedFilterTab(newValue);
  };

  // Handle price filter type change
  const handlePriceFilterTypeChange = (event, newValue) => {
    if (newValue !== null) {
      setPriceFilterType(newValue);
    }
  };

  // Handle price range change
  const handlePriceRangeChange = (event, newValue) => {
    setPriceRange(newValue);
  };

  // Handle change filter type change
  const handleChangeFilterTypeChange = (event, newValue) => {
    if (newValue !== null) {
      setChangeFilterType(newValue);
    }
  };

  // Handle change range change
  const handleChangeRangeChange = (event, newValue) => {
    setChangeRange(newValue);
  };

  // Handle volume range change
  const handleVolumeRangeChange = (event, newValue) => {
    setVolumeRange(newValue);
  };

  // Handle volume input change
  const handleVolumeInputChange = (index, event) => {
    const newVolumeRange = [...volumeRange];
    newVolumeRange[index] = Number(event.target.value);
    setVolumeRange(newVolumeRange);
  };

  // Handle sector change
  const handleSectorChange = (event) => {
    setSector(event.target.value);
  };

  // Handle industry change
  const handleIndustryChange = (event) => {
    setIndustry(event.target.value);
  };

  // Handle exchange change
  const handleExchangeChange = (event) => {
    setExchange(event.target.value);
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TrendingUpIcon sx={{ mr: 1, fontSize: 28, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Stocks Crossing Previous Day High
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                color="primary"
              />
            }
            label="Auto Refresh"
          />

          <FormControlLabel
            control={
              <Switch
                checked={soundEnabled}
                onChange={(e) => {
                  setSoundEnabled(e.target.checked);

                  // If turning on sound, try to initialize audio
                  if (e.target.checked) {
                    // User interaction is happening here, so this should work
                    if (audioRef.current) {
                      // Set very low volume for initialization
                      audioRef.current.volume = 0.01;

                      audioRef.current.play()
                        .then(() => {
                          console.log('Audio initialized successfully');
                          setAudioInitialized(true);
                          // Immediately pause so user doesn't hear it
                          audioRef.current.pause();
                          audioRef.current.currentTime = 0;
                        })
                        .catch(err => {
                          console.error('Failed to initialize audio:', err);
                          setAudioInitialized(false);
                        });
                    }
                  }
                }}
                color="primary"
              />
            }
            label={audioInitialized ? "Sound Alerts (Ready)" : "Sound Alerts (Click to Enable)"}
          />

          {lastUpdated && (
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}

          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
            onClick={fetchStocks}
            disabled={loading}
          >
            Refresh
          </Button>

          <Button
            variant="outlined"
            onClick={() => {
              playNotificationSound();
            }}
            disabled={!soundEnabled || !audioInitialized}
            sx={{ ml: 2 }}
          >
            Test Sound
          </Button>
        </Box>
      </Box>

      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Tracking stocks that opened below previous day's high and then crossed above it during the trading session.
      </Typography>

      {/* Advanced Filters */}
      <AdvancedFilters
        showAdvanced={showAdvanced}
        setShowAdvanced={setShowAdvanced}
        selectedFilterTab={selectedFilterTab}
        handleFilterTabChange={handleFilterTabChange}
        priceFilterType={priceFilterType}
        handlePriceFilterTypeChange={handlePriceFilterTypeChange}
        priceRange={priceRange}
        handlePriceRangeChange={handlePriceRangeChange}
        priceAbove={priceAbove}
        setPriceAbove={setPriceAbove}
        priceBelow={priceBelow}
        setPriceBelow={setPriceBelow}
        changeFilterType={changeFilterType}
        handleChangeFilterTypeChange={handleChangeFilterTypeChange}
        changeRange={changeRange}
        handleChangeRangeChange={handleChangeRangeChange}
        changeMin={changeMin}
        setChangeMin={setChangeMin}
        changeMax={changeMax}
        setChangeMax={setChangeMax}
        volumeRange={volumeRange}
        handleVolumeRangeChange={handleVolumeRangeChange}
        handleVolumeInputChange={handleVolumeInputChange}
        sector={sector}
        handleSectorChange={handleSectorChange}
        sectors={sectors}
        industry={industry}
        handleIndustryChange={handleIndustryChange}
        industries={industries}
        exchange={exchange}
        handleExchangeChange={handleExchangeChange}
        exchanges={exchanges}
        formatPrice={formatPrice}
        formatPercentage={formatPercentage}
        formatVolume={formatVolume}
      />

      {error && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'error.light', color: 'error.contrastText' }}>
          <Typography>{error}</Typography>
        </Paper>
      )}

      {loading && stocks.length === 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
          <CircularProgress />
        </Box>
      )}

      {hasNewNotification && (
        <Paper
          sx={{
            p: 2,
            mb: 3,
            bgcolor: 'success.light',
            color: 'success.contrastText',
            animation: 'pulse 1s infinite'
          }}
        >
          <Typography>New stocks detected!</Typography>
        </Paper>
      )}

      <Grid container spacing={2} sx={{ mt: 2 }}>
        {stocks.map((stock) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={stock.symbol}>
            <Card
              sx={{
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6
                },
                border: stock.isNew ? '2px solid #f44336' : 'none'
              }}
            >
              <CardHeader
                title={
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6">{stock.symbol}</Typography>
                    {stock.isNew && (
                      <Chip
                        label="NEW"
                        color="error"
                        size="small"
                        sx={{ fontWeight: 'bold' }}
                      />
                    )}
                  </Box>
                }
                subheader={stock.company_name || stock.name}
              />
              <CardContent>
                <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
                  ${typeof stock.price === 'number' ? stock.price.toFixed(2) : stock.price}
                  <Chip
                    label={`${stock.change_percent >= 0 ? '+' : ''}${typeof stock.change_percent === 'number' ? stock.change_percent.toFixed(2) : stock.change_percent}%`}
                    color={stock.change_percent >= 0 ? 'success' : 'error'}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Typography>

                <Divider sx={{ my: 1 }} />

                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Previous High:</span>
                  <span>${typeof stock.prev_day_high === 'number' ? stock.prev_day_high.toFixed(2) : stock.prev_day_high}</span>
                </Typography>

                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Open:</span>
                  <span>${typeof stock.open_price === 'number' ? stock.open_price.toFixed(2) : stock.open_price}</span>
                </Typography>

                <Typography variant="body2" sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Volume:</span>
                  <span>{formatVolume(stock.volume)}</span>
                </Typography>

                {stock.sector && (
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {stock.sector}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {!loading && stocks.length === 0 && (
        <Paper sx={{ p: 3, textAlign: 'center', mt: 3 }}>
          <Typography variant="h6">No stocks found</Typography>
          <Typography variant="body2" color="text.secondary">
            No stocks have crossed their previous day high after opening below it.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default StocksCrossingPrevHighPage;
