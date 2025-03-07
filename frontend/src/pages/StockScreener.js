import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, TextField, Button, Paper, Table, 
  TableBody, TableCell, TableContainer, TableHead, 
  TableRow, CircularProgress, Grid, FormControl,
  InputLabel, Select, MenuItem, Chip, Slider, 
  ToggleButtonGroup, ToggleButton,
  Switch, Alert, Accordion,
  AccordionSummary, AccordionDetails, Tabs, Tab,
  IconButton, Tooltip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import RefreshIcon from '@mui/icons-material/Refresh';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ShowChartIcon from '@mui/icons-material/ShowChart';
import BarChartIcon from '@mui/icons-material/BarChart';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import NotificationsIcon from '@mui/icons-material/Notifications';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import SearchOffIcon from '@mui/icons-material/SearchOff';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Reusable component for advanced filters
const AdvancedFilters = ({ 
  showAdvanced, 
  selectedFilterTab, 
  handleFilterTabChange, 
  priceFilterType, 
  handlePriceFilterTypeChange, 
  priceRange, 
  handlePriceRangeChange, 
  priceAbove, 
  setPriceAbove, 
  priceBelow, 
  setPriceBelow, 
  changeFilterType, 
  handleChangeFilterTypeChange, 
  changeRange, 
  handleChangeRangeChange, 
  changeMin, 
  setChangeMin, 
  changeMax, 
  setChangeMax, 
  volumeRange, 
  handleVolumeRangeChange, 
  handleVolumeInputChange, 
  sector, 
  handleSectorChange, 
  sectors, 
  industry, 
  handleIndustryChange, 
  industries, 
  exchange, 
  handleExchangeChange, 
  exchanges, 
  formatPrice, 
  formatPercentage, 
  formatVolume 
}) => {
  if (!showAdvanced) return null;
  
  return (
    <Box sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
      <Typography variant="subtitle1" gutterBottom>
        Narrow down stocks:
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
        <Tab label="Change %" value="change" />
        <Tab label="Volume" value="volume" />
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
                  valueLabelFormat={formatPrice}
                  min={0}
                  max={2000}
                  sx={{ mt: 1 }}
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
                  min={-200}
                  max={200}
                  sx={{ mt: 1 }}
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
  );
};

// Reusable component for the Advanced Filters toggle
const AdvancedFilterToggle = ({ showAdvanced, setShowAdvanced }) => (
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
      checked={showAdvanced}
      onChange={(e) => setShowAdvanced(e.target.checked)}
      color="primary"
    />
  </Box>
);

// Reusable component for screener box
const ScreenerBox = ({ 
  title, 
  description, 
  onSearch, 
  loading,
  showAdvanced,
  setShowAdvanced,
  children,
  advancedFiltersProps
}) => {
  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        {description}
      </Alert>
      
      {children}
      
      <AdvancedFilterToggle 
        showAdvanced={showAdvanced} 
        setShowAdvanced={setShowAdvanced} 
      />
      
      <AdvancedFilters 
        showAdvanced={showAdvanced}
        {...advancedFiltersProps}
      />
    </Paper>
  );
};

// Reusable StockTable component
const StockTable = ({ 
  stocks, 
  loading, 
  error, 
  lastUpdated, 
  refreshData, 
  navigateToStockDetails, 
  navigateToAlerts,
  showOpenBelowPrevHigh
}) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
        <CircularProgress />
        <Typography variant="body1" color="text.secondary" sx={{ ml: 2 }}>
          Loading stocks...
        </Typography>
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 3 }}>
        {error}
      </Alert>
    );
  }
  
  if (stocks.length === 0) {
    return (
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
        >
          Adjust Filters
        </Button>
      </Box>
    );
  }
  
  return (
    <Box sx={{ p: 0 }}>
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
              
              {/* Add conditional columns for Open Below Prev High screener */}
              {showOpenBelowPrevHigh && (
                <>
                  <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Open</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Prev High</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 600, py: 1.5 }}>Diff %</TableCell>
                </>
              )}
              
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
                  {stock.price || 'N/A'}
                </TableCell>
                <TableCell 
                  align="right"
                  sx={{ 
                    py: 2,
                    color: (() => {
                      // Parse change percentage to determine color
                      const changeText = stock.change_percent || '';
                      if (changeText.includes('-')) return 'error.main';
                      if (changeText.includes('+') || changeText.match(/[0-9]/)) return 'success.main';
                      return 'text.primary';
                    })()
                  }}
                >
                  {stock.change_percent || 'N/A'}
                </TableCell>
                
                {/* Add conditional cells for Open Below Prev High screener */}
                {showOpenBelowPrevHigh && (
                  <>
                    <TableCell align="right" sx={{ py: 2 }}>
                      {stock.open || 'N/A'}
                    </TableCell>
                    <TableCell align="right" sx={{ py: 2 }}>
                      {stock.prevHigh || 'N/A'}
                    </TableCell>
                    <TableCell 
                      align="right" 
                      sx={{ 
                        py: 2,
                        color: 'info.main'
                      }}
                    >
                      {stock.difference || 'N/A'}
                    </TableCell>
                  </>
                )}
                
                <TableCell align="right" sx={{ py: 2 }}>
                  {stock.volume || 'N/A'}
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
  );
};

const StockScreener = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [stocks, setStocks] = useState([]);
  const [rawStocksData, setRawStocksData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sector, setSector] = useState('');
  const [sectors, setSectors] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [error, setError] = useState('');
  
  // Advanced filter states
  const [priceRange, setPriceRange] = useState([0, 5000]);
  const [changeRange, setChangeRange] = useState([-500, 500]);
  const [showPositiveCandles, setShowPositiveCandles] = useState(false);
  const [showPrevDayHighCross, setShowPrevDayHighCross] = useState(true);
  const [showNegativeCandles, setShowNegativeCandles] = useState(false);
  const [showPrevDayLowCross, setShowPrevDayLowCross] = useState(false);
  const [timeframe, setTimeframe] = useState("5m");
  const [numCandles, setNumCandles] = useState(3);
  
  // Enhanced filter states
  const [selectedFilterTab, setSelectedFilterTab] = useState("price");
  
  // Enhanced volume filter options
  const [volumeRange, setVolumeRange] = useState([100000, 10000000]);
  
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
  const [exchanges] = useState(['NYSE', 'NASDAQ', 'AMEX', 'OTC']);
  
  // Advanced filters visibility for different screeners
  const [showAdvancedInPDHC, setShowAdvancedInPDHC] = useState(false);
  const [showAdvancedInPC, setShowAdvancedInPC] = useState(false);
  const [showAdvancedInOBPH, setShowAdvancedInOBPH] = useState(false);
  
  // Add new state variables for search UI
  const [recentSearches, setRecentSearches] = useState([]);
  
  // Add a new state variable for result limit
  const [maxResults, setMaxResults] = useState(15);
  
  // Add state for the Open Below Prev High screener
  const [showOpenBelowPrevHigh, setShowOpenBelowPrevHigh] = useState(false);
  const [openBelowPrevHighParams, setOpenBelowPrevHighParams] = useState({
    min_price: 0.25,
    max_price: 10.0,
    min_volume: 250000,
    limit: 50
  });
  
  // Fetch popular stocks on component mount
  useEffect(() => {
    const fetchPopularStocks = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/api/stocks/popular`);
        
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
  
  // Helper function to get filter parameters based on the current advanced filter settings
  const getAdvancedFilterParams = (showAdvanced) => {
    const params = {
      limit: maxResults
    };
    
    if (!showAdvanced) return params;
    
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
    if (changeFilterType === "any") {
      params.min_change_percent = changeRange[0];
      params.max_change_percent = changeRange[1];
    } else if (changeFilterType === "up") {
      params.min_change_percent = changeMin;
    } else if (changeFilterType === "down") {
      params.max_change_percent = -changeMin;
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
    
    return params;
  };
  
  // Function to handle filter search
  const handleFilterSearch = async () => {
    // Determine which screener is active and call the appropriate search function
    if (showPositiveCandles) {
      return handlePositiveCandlesSearch();
    } else if (showNegativeCandles) {
      return handleNegativeCandlesSearch();
    } else if (showPrevDayHighCross) {
      return handlePrevDayHighCrossSearch();
    } else if (showPrevDayLowCross) {
      return handlePrevDayLowCrossSearch();
    } else if (showOpenBelowPrevHigh) {
      return handleOpenBelowPrevHighSearch();
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
    } else if (showNegativeCandles) {
      await handleNegativeCandlesSearch();
    } else if (showPrevDayHighCross) {
      await handlePrevDayHighCrossSearch();
    } else if (showPrevDayLowCross) {
      await handlePrevDayLowCrossSearch();
    } else if (showOpenBelowPrevHigh) {
      await handleOpenBelowPrevHighSearch();
    }
    setLastUpdated(new Date());
    setLoading(false);
  };
  
  // Formatting helper functions
  const formatPercentage = (value) => {
    if (value === "N/A" || value == null) return "N/A";
    const num = parseFloat(value);
    return isNaN(num) ? "N/A" : `${num.toFixed(2)}%`;
  };
  
  const formatPrice = (value) => {
    if (value === "N/A" || value == null) return "N/A";
    const num = parseFloat(value);
    return isNaN(num) ? "N/A" : `$${num.toFixed(2)}`;
  };
  
  const formatVolume = (value) => {
    if (typeof value === 'string' && (value.includes('K') || value.includes('M') || value.includes('B'))) {
      return value;
    }
    if (!value) {
      return 'N/A';
    }
    
    const num = parseFloat(value);
    if (isNaN(num)) return 'N/A';
    
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    
    return value.toString();
  };
  
  // Process API response data to standardize the format for display
  const processStockData = (stockData) => {
    return stockData.map(stock => ({
      ...stock,
      price: stock.price_display || 
             (typeof stock.price === 'number' ? formatPrice(stock.price) : 'N/A'),
      
      change_percent: stock.change_percent_display || 
                     (typeof stock.change_percent === 'number' ? formatPercentage(stock.change_percent) : 'N/A'),
      
      volume: stock.volume_display || 
             (typeof stock.volume === 'number' ? formatVolume(stock.volume) : 'N/A')
    }));
  };
  
  // API search functions
  const handlePositiveCandlesSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      const endpoint = `${API_URL}/api/stocks/screener/consecutive-positive`;
      
      const params = {
        ...getAdvancedFilterParams(showAdvancedInPC),
        timeframe,
        num_candles: numCandles
      };
      
      console.log("Searching for stocks with consecutive positive candles with params:", params);
      
      const response = await axios.get(endpoint, { params });
      
      if (response.data && response.data.stocks) {
        const processedStocks = processStockData(response.data.stocks);
        setStocks(processedStocks);
        setRawStocksData(response.data.stocks);
      } else {
        setStocks([]);
        setRawStocksData([]);
        setError('No stocks found with consecutive positive candles. Try adjusting your parameters.');
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error finding stocks with consecutive positive candles:', error);
      setError('Error fetching stocks with consecutive positive candles.');
      setStocks([]);
      setRawStocksData([]);
    } finally {
      setLoading(false);
    }
  };
  
  const handleTimeframeChange = (e) => {
    setTimeframe(e.target.value);
  };
  
  const handleNumCandlesChange = (e) => {
    setNumCandles(Number(e.target.value));
  };
  
  const handlePrevDayHighCrossSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      const endpoint = `${API_URL}/api/stocks/screener/crossing-prev-day-high`;
      const params = getAdvancedFilterParams(showAdvancedInPDHC);
      
      console.log("Searching for stocks crossing above previous day high with params:", params);
      
      const response = await axios.get(endpoint, { params });
      
      if (response.data && response.data.stocks) {
        const processedStocks = processStockData(response.data.stocks);
        setStocks(processedStocks);
        setRawStocksData(response.data.stocks);
      } else {
        setStocks([]);
        setRawStocksData([]);
        setError('No stocks found crossing above previous day high. Try adjusting your parameters.');
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error finding stocks crossing above previous day high:', error);
      setError('Error fetching stocks crossing above previous day high.');
      setStocks([]);
      setRawStocksData([]);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle volume range change
  const handleVolumeRangeChange = (event, newValue) => {
    const cleanValues = newValue.map(val => (
      typeof val === 'string' ? Number(val.replace(/,/g, '')) : val
    ));
    setVolumeRange(cleanValues);
  };
  
  // Handle manual volume input change
  const handleVolumeInputChange = (index, event) => {
    const value = event.target.value;
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
  
  // Handle max results change
  const handleMaxResultsChange = (event, newValue) => {
    setMaxResults(newValue);
  };
  
  // Values for max results slider
  const maxResultsMarks = [
    { value: 5, label: '5' },
    { value: 15, label: '15' },
    { value: 25, label: '25' },
    { value: 50, label: '50' },
    { value: 75, label: '75' },
    { value: 100, label: '100' },
  ];
  
  const handleNegativeCandlesSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      const endpoint = `${API_URL}/api/stocks/screener/consecutive-negative`;
      
      const params = {
        ...getAdvancedFilterParams(showAdvancedInPC),
        timeframe,
        num_candles: numCandles
      };
      
      console.log("Searching for stocks with consecutive negative candles with params:", params);
      
      const response = await axios.get(endpoint, { params });
      
      if (response.data && response.data.stocks) {
        const processedStocks = processStockData(response.data.stocks);
        setStocks(processedStocks);
        setRawStocksData(response.data.stocks);
      } else {
        setStocks([]);
        setRawStocksData([]);
        setError('No stocks found with consecutive negative candles. Try adjusting your parameters.');
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error finding stocks with consecutive negative candles:', error);
      setError('Error fetching stocks with consecutive negative candles.');
      setStocks([]);
      setRawStocksData([]);
    } finally {
      setLoading(false);
    }
  };
  
  const handlePrevDayLowCrossSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      const endpoint = `${API_URL}/api/stocks/screener/crossing-prev-day-low`;
      const params = getAdvancedFilterParams(showAdvancedInPDHC);
      
      console.log("Searching for stocks below previous day low with params:", params);
      
      const response = await axios.get(endpoint, { params });
      
      if (response.data && response.data.stocks) {
        const processedStocks = processStockData(response.data.stocks);
        setStocks(processedStocks);
        setRawStocksData(response.data.stocks);
      } else {
        setStocks([]);
        setRawStocksData([]);
        setError('No stocks found below previous day low. Try adjusting your parameters.');
      }
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error finding stocks below previous day low:', error);
      setError('Error fetching stocks below previous day low.');
      setStocks([]);
      setRawStocksData([]);
    } finally {
      setLoading(false);
    }
  };
  
  const handleOpenBelowPrevHighSearch = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Combine standard params with specific params for this screener
      const params = {
        ...getAdvancedFilterParams(showAdvancedInOBPH),
        min_price: openBelowPrevHighParams.min_price,
        max_price: openBelowPrevHighParams.max_price,
        min_volume: openBelowPrevHighParams.min_volume
      };
      
      const response = await axios.get(`${API_URL}/api/stocks/screener/open-below-prev-high`, { params });
      
      if (response.data && response.data.stocks) {
        const formattedStocks = response.data.stocks.map(stock => ({
          ...stock,
          symbol: stock.symbol,
          name: stock.name,
          price: formatPrice(stock.current_price),
          change_percent: formatPercentage(stock.change_percent),
          open: formatPrice(stock.open_price),
          prevHigh: formatPrice(stock.prev_day_high),
          difference: formatPercentage(stock.diff_percent),
          volume: formatVolume(stock.volume),
          sector: stock.sector
        }));
        
        setStocks(formattedStocks);
        setRawStocksData(response.data.stocks);
        setLastUpdated(new Date());
      } else {
        setError('No stocks found matching your criteria.');
        setStocks([]);
        setRawStocksData([]);
      }
    } catch (error) {
      console.error('Error fetching stocks with open below previous day high:', error);
      setError('Error fetching stocks. Please try again later.');
      setStocks([]);
      setRawStocksData([]);
    } finally {
      setLoading(false);
    }
  };
  
  // Shared filter props for advanced filters component
  const advancedFiltersProps = {
    selectedFilterTab,
    handleFilterTabChange,
    priceFilterType,
    handlePriceFilterTypeChange,
    priceRange,
    handlePriceRangeChange,
    priceAbove,
    setPriceAbove,
    priceBelow,
    setPriceBelow,
    changeFilterType,
    handleChangeFilterTypeChange,
    changeRange,
    handleChangeRangeChange,
    changeMin,
    setChangeMin,
    changeMax,
    setChangeMax,
    volumeRange,
    handleVolumeRangeChange,
    handleVolumeInputChange,
    sector,
    handleSectorChange,
    sectors,
    industry,
    handleIndustryChange,
    industries,
    exchange,
    handleExchangeChange,
    exchanges,
    formatPrice,
    formatPercentage,
    formatVolume
  };

  return (
    <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
        Stock Screener
      </Typography>
      
      <Box sx={{ mb: 4, width: '100%', maxWidth: 1200 }}>
        <Typography variant="h6" gutterBottom>
          Screener Options
        </Typography>
        
        {/* Max Results Slider */}
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
        
        {/* Filter buttons */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6} lg={2.4}>
            <Button
              fullWidth
              variant={showPrevDayHighCross ? "contained" : "outlined"}
              startIcon={<TrendingUpIcon />}
              onClick={() => {
                setShowPositiveCandles(false);
                setShowPrevDayHighCross(true);
                setShowNegativeCandles(false);
                setShowPrevDayLowCross(false);
                setShowOpenBelowPrevHigh(false);
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
              Above Prev Day High
            </Button>
          </Grid>
          <Grid item xs={12} md={6} lg={2.4}>
            <Button
              fullWidth
              variant={showPrevDayLowCross ? "contained" : "outlined"}
              startIcon={<TrendingUpIcon sx={{ transform: 'rotate(180deg)' }} />}
              onClick={() => {
                setShowPositiveCandles(false);
                setShowPrevDayHighCross(false);
                setShowNegativeCandles(false);
                setShowPrevDayLowCross(true);
                setShowOpenBelowPrevHigh(false);
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
              Below Prev Day Low
            </Button>
          </Grid>
          <Grid item xs={12} md={6} lg={2.4}>
            <Button
              fullWidth
              variant={showOpenBelowPrevHigh ? "contained" : "outlined"}
              startIcon={<ShowChartIcon />}
              onClick={() => {
                setShowPositiveCandles(false);
                setShowPrevDayHighCross(false);
                setShowNegativeCandles(false);
                setShowPrevDayLowCross(false);
                setShowOpenBelowPrevHigh(true);
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
              Open Below Prev High
            </Button>
          </Grid>
          <Grid item xs={12} md={6} lg={2.4}>
            <Button
              fullWidth
              variant={showPositiveCandles ? "contained" : "outlined"}
              startIcon={<ShowChartIcon />}
              onClick={() => {
                setShowPositiveCandles(true);
                setShowPrevDayHighCross(false);
                setShowNegativeCandles(false);
                setShowPrevDayLowCross(false);
                setShowOpenBelowPrevHigh(false);
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
              Consecutive Pos Candles
            </Button>
          </Grid>
          <Grid item xs={12} md={6} lg={2.4}>
            <Button
              fullWidth
              variant={showNegativeCandles ? "contained" : "outlined"}
              startIcon={<ShowChartIcon sx={{ transform: 'scaleY(-1)' }} />}
              onClick={() => {
                setShowPositiveCandles(false);
                setShowPrevDayHighCross(false);
                setShowNegativeCandles(true);
                setShowPrevDayLowCross(false);
                setShowOpenBelowPrevHigh(false);
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
              Consecutive Neg Candles
            </Button>
          </Grid>
        </Grid>
        
        {/* Positive Candles Screener */}
        {showPositiveCandles && (
          <ScreenerBox
            title="Consecutive Positive Candles Screener"
            description={`This screener finds stocks that have ${numCandles} consecutive positive candles (close > open) on the ${timeframe} timeframe. 
                         These stocks may be in a strong uptrend and could present trading opportunities.`}
            onSearch={handlePositiveCandlesSearch}
            loading={loading}
            showAdvanced={showAdvancedInPC}
            setShowAdvanced={setShowAdvancedInPC}
            advancedFiltersProps={advancedFiltersProps}
          >
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
          </ScreenerBox>
        )}
        
        {/* Negative Candles Screener */}
        {showNegativeCandles && (
          <ScreenerBox
            title="Consecutive Negative Candles Screener"
            description={`This screener finds stocks that have ${numCandles} consecutive negative candles (close < open) on the ${timeframe} timeframe. 
                         These stocks may be in a strong downtrend and could present trading opportunities.`}
            onSearch={handleNegativeCandlesSearch}
            loading={loading}
            showAdvanced={showAdvancedInPC}
            setShowAdvanced={setShowAdvancedInPC}
            advancedFiltersProps={advancedFiltersProps}
          >
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
                  onClick={handleNegativeCandlesSearch}
                  disabled={loading}
                  sx={{ height: '56px' }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Find Stocks'}
                </Button>
              </Grid>
            </Grid>
          </ScreenerBox>
        )}
        
        {/* Above Previous Day High Screener */}
        {showPrevDayHighCross && (
          <ScreenerBox
            title="Stocks Above Previous Day High Screener"
            description="This screener finds stocks that have their current price crossing above the previous day's high. 
                         This can signal increased momentum and potential breakout opportunities."
            onSearch={handlePrevDayHighCrossSearch}
            loading={loading}
            showAdvanced={showAdvancedInPDHC}
            setShowAdvanced={setShowAdvancedInPDHC}
            advancedFiltersProps={advancedFiltersProps}
          >
            <Grid container spacing={3}>
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
          </ScreenerBox>
        )}
        
        {/* Below Previous Day Low Screener */}
        {showPrevDayLowCross && (
          <ScreenerBox
            title="Stocks Below Previous Day Low Screener"
            description="This screener finds stocks that have their current price below the previous day's low. 
                         This can signal increased downward momentum and potential breakdown opportunities."
            onSearch={handlePrevDayLowCrossSearch}
            loading={loading}
            showAdvanced={showAdvancedInPDHC}
            setShowAdvanced={setShowAdvancedInPDHC}
            advancedFiltersProps={advancedFiltersProps}
          >
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Paper sx={{ p: 2, height: '56px', display: 'flex', alignItems: 'center', bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)' }}>
                  <Typography variant="body1" color="text.secondary">
                    Finds stocks currently trading below their previous day's low
                  </Typography>
                </Paper>
              </Grid>
              
              {/* Search Button */}
              <Grid item xs={12} md={4}>
                <Button
                  fullWidth
                  variant="contained"
                  color="primary"
                  onClick={handlePrevDayLowCrossSearch}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                  sx={{ height: '56px' }}
                >
                  {loading ? 'Searching...' : 'Find Stocks'}
                </Button>
              </Grid>
            </Grid>
          </ScreenerBox>
        )}
        
        {/* Open Below Previous Day High Screener */}
        {showOpenBelowPrevHigh && (
          <ScreenerBox
            title="Stocks With Open Below Previous Day High"
            description="Find stocks where the current day's opening price is below the previous day's high.
                        This can identify potential buying opportunities for stocks that opened in a good entry range."
            onSearch={handleOpenBelowPrevHighSearch}
            loading={loading}
            showAdvanced={showAdvancedInOBPH}
            setShowAdvanced={setShowAdvancedInOBPH}
            advancedFiltersProps={advancedFiltersProps}
          >
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Price Range
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TextField
                    size="small"
                    label="Min $"
                    type="number"
                    inputProps={{ min: 0, step: 0.01 }}
                    value={openBelowPrevHighParams.min_price}
                    onChange={(e) => setOpenBelowPrevHighParams({
                      ...openBelowPrevHighParams,
                      min_price: parseFloat(e.target.value)
                    })}
                    sx={{ width: '100%' }}
                  />
                  <Typography variant="body2">to</Typography>
                  <TextField
                    size="small"
                    label="Max $"
                    type="number"
                    inputProps={{ min: 0, step: 0.01 }}
                    value={openBelowPrevHighParams.max_price}
                    onChange={(e) => setOpenBelowPrevHighParams({
                      ...openBelowPrevHighParams,
                      max_price: parseFloat(e.target.value)
                    })}
                    sx={{ width: '100%' }}
                  />
                </Box>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Min Volume
                </Typography>
                <TextField
                  size="small"
                  type="number"
                  inputProps={{ min: 0, step: 10000 }}
                  value={openBelowPrevHighParams.min_volume}
                  onChange={(e) => setOpenBelowPrevHighParams({
                    ...openBelowPrevHighParams,
                    min_volume: parseInt(e.target.value)
                  })}
                  sx={{ width: '100%' }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleOpenBelowPrevHighSearch}
                  startIcon={<SearchIcon />}
                  sx={{ mt: 3, width: '100%' }}
                >
                  Find Stocks
                </Button>
              </Grid>
            </Grid>
          </ScreenerBox>
        )}
        
        {/* Results Table */}
        {(stocks.length > 0 || loading) && (
          <Paper sx={{ p: 0, mt: 3, borderRadius: 2, overflow: 'hidden' }}>
            <StockTable 
              stocks={stocks}
              loading={loading}
              error={error}
              lastUpdated={lastUpdated}
              refreshData={refreshData}
              navigateToStockDetails={navigateToStockDetails}
              navigateToAlerts={navigateToAlerts}
              showOpenBelowPrevHigh={showOpenBelowPrevHigh}
            />
          </Paper>
        )}
      </Box>
    </Box>
  );
};

export default StockScreener;