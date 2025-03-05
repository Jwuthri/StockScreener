import React, { createContext, useContext, useState, useEffect } from 'react';

const StockDataContext = createContext();

export const useStockData = () => useContext(StockDataContext);

export const StockDataProvider = ({ children }) => {
  // Default cache expiry time in minutes
  const DEFAULT_CACHE_EXPIRY = 5;
  
  // Cache for different filtered data
  const [cachedData, setCachedData] = useState({
    // Structure will be:
    // {
    //   'filter=gainers': { data: [...], timestamp: Date, expiryMinutes: 5 },
    //   'filter=losers': { data: [...], timestamp: Date, expiryMinutes: 5 },
    //   'screener/consecutive-positive?timeframe=5m&num_candles=3': { data: [...], timestamp: Date, expiryMinutes: 5 },
    //   etc.
    // }
  });

  // Function to check if cache exists and is valid
  const hasCache = (cacheKey) => {
    const cached = cachedData[cacheKey];
    if (!cached) return false;
    
    // Check if cache is expired
    const now = new Date();
    const cacheTime = new Date(cached.timestamp);
    const expiryMinutes = cached.expiryMinutes || DEFAULT_CACHE_EXPIRY;
    const diffMinutes = (now - cacheTime) / (1000 * 60);
    
    return diffMinutes <= expiryMinutes;
  };

  // Function to get cached data
  const getCachedData = (cacheKey) => {
    const cached = cachedData[cacheKey];
    if (!cached) return null;
    
    // Check if cache is expired
    const now = new Date();
    const cacheTime = new Date(cached.timestamp);
    const expiryMinutes = cached.expiryMinutes || DEFAULT_CACHE_EXPIRY;
    const diffMinutes = (now - cacheTime) / (1000 * 60);
    
    if (diffMinutes > expiryMinutes) {
      // Cache is expired, remove it
      clearCacheForKey(cacheKey);
      return null;
    }
    
    return cached;
  };

  // Function to set cached data with optional expiry time
  const setCachedDataForKey = (cacheKey, data, expiryMinutes = DEFAULT_CACHE_EXPIRY) => {
    setCachedData(prev => ({
      ...prev,
      [cacheKey]: {
        data,
        timestamp: new Date(),
        expiryMinutes
      }
    }));
  };

  // Function to clear all cached data
  const clearCache = () => {
    setCachedData({});
  };

  // Function to clear specific cached data
  const clearCacheForKey = (cacheKey) => {
    setCachedData(prev => {
      const newCache = { ...prev };
      delete newCache[cacheKey];
      return newCache;
    });
  };

  // Expose the context value
  const contextValue = {
    hasCache,
    getCachedData,
    setCachedDataForKey,
    clearCache,
    clearCacheForKey,
    cachedData
  };

  return (
    <StockDataContext.Provider value={contextValue}>
      {children}
    </StockDataContext.Provider>
  );
};

export default StockDataContext; 