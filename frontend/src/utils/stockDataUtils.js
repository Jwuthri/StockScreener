import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Formatting helper functions
export const formatPercentage = (value) => {
  if (value === "N/A" || value == null) return "N/A";
  const num = parseFloat(value);
  return isNaN(num) ? "N/A" : `${num.toFixed(2)}%`;
};

export const formatPrice = (value) => {
  if (value === "N/A" || value == null) return "N/A";
  const num = parseFloat(value);
  return isNaN(num) ? "N/A" : `$${num.toFixed(2)}`;
};

export const formatVolume = (value) => {
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
export const processStockData = (stockData) => {
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

// Cache functions for Home page data
export const getHomePageCacheKey = (dataType) => {
  return `homePage_${dataType}`;
};

export const saveHomePageDataToCache = (dataType, data) => {
  const cacheKey = getHomePageCacheKey(dataType);
  const cacheData = {
    timestamp: new Date().getTime(),
    data: data,
    lastUpdated: new Date()
  };

  localStorage.setItem(cacheKey, JSON.stringify(cacheData));
  return cacheData;
};

export const loadHomePageDataFromCache = (dataType) => {
  const cacheKey = getHomePageCacheKey(dataType);
  const cached = localStorage.getItem(cacheKey);

  if (cached) {
    try {
      const parsedCache = JSON.parse(cached);
      // Check if cache is less than 5 minutes old
      const cacheAge = new Date().getTime() - parsedCache.timestamp;
      if (cacheAge < 5 * 60 * 1000) { // 5 minutes
        return parsedCache;
      }
    } catch (error) {
      console.error(`Error parsing ${dataType} cache:`, error);
      // If there's an error parsing the cache, remove it
      localStorage.removeItem(cacheKey);
    }
  }
  return null;
};

// Function to fetch top gainers with caching
export const fetchTopGainers = async (limit = 10, forceRefresh = false) => {
  // Try to load from cache first if not forcing refresh
  if (!forceRefresh) {
    const cachedData = loadHomePageDataFromCache('topGainers');
    if (cachedData) {
      return cachedData.data;
    }
  }

  try {
    const response = await axios.get(`${API_URL}/api/stocks/top-gainers`, {
      params: { limit }
    });

    if (response.data && response.data.stocks) {
      const processedStocks = processStockData(response.data.stocks);
      // Save to cache
      saveHomePageDataToCache('topGainers', processedStocks);
      return processedStocks;
    }
    return [];
  } catch (error) {
    console.error('Error fetching top gainers:', error);
    return [];
  }
};

// Function to fetch top losers with caching
export const fetchTopLosers = async (limit = 10, forceRefresh = false) => {
  // Try to load from cache first if not forcing refresh
  if (!forceRefresh) {
    const cachedData = loadHomePageDataFromCache('topLosers');
    if (cachedData) {
      return cachedData.data;
    }
  }

  try {
    const response = await axios.get(`${API_URL}/api/stocks/top-losers`, {
      params: { limit }
    });

    if (response.data && response.data.stocks) {
      const processedStocks = processStockData(response.data.stocks);
      // Save to cache
      saveHomePageDataToCache('topLosers', processedStocks);
      return processedStocks;
    }
    return [];
  } catch (error) {
    console.error('Error fetching top losers:', error);
    return [];
  }
};

// Function to fetch most active stocks with caching
export const fetchMostActive = async (limit = 10, forceRefresh = false) => {
  // Try to load from cache first if not forcing refresh
  if (!forceRefresh) {
    const cachedData = loadHomePageDataFromCache('mostActive');
    if (cachedData) {
      return cachedData.data;
    }
  }

  try {
    const response = await axios.get(`${API_URL}/api/stocks/most-active`, {
      params: { limit }
    });

    if (response.data && response.data.stocks) {
      const processedStocks = processStockData(response.data.stocks);
      // Save to cache
      saveHomePageDataToCache('mostActive', processedStocks);
      return processedStocks;
    }
    return [];
  } catch (error) {
    console.error('Error fetching most active stocks:', error);
    return [];
  }
};

// Function to refresh all home page data
export const refreshHomePageData = async () => {
  try {
    const [gainers, losers, active] = await Promise.all([
      fetchTopGainers(10, true),
      fetchTopLosers(10, true),
      fetchMostActive(10, true)
    ]);

    return {
      topGainers: gainers,
      topLosers: losers,
      mostActive: active,
      lastUpdated: new Date()
    };
  } catch (error) {
    console.error('Error refreshing home page data:', error);
    throw error;
  }
};
