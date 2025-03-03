import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stock API calls
export const getPopularStocks = async () => {
  try {
    const response = await api.get('/api/stocks/popular');
    return response.data.popular_stocks;
  } catch (error) {
    console.error('Error fetching popular stocks:', error);
    throw error;
  }
};

export const searchStocks = async (query) => {
  try {
    const response = await api.get(`/api/stocks/search?query=${query}`);
    return response.data.results;
  } catch (error) {
    console.error('Error searching stocks:', error);
    throw error;
  }
};

export const getStockInfo = async (symbol) => {
  try {
    const response = await api.get(`/api/stocks/info/${symbol}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching stock info for ${symbol}:`, error);
    throw error;
  }
};

export const getStockPrice = async (symbol) => {
  try {
    const response = await api.get(`/api/stocks/price/${symbol}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching stock price for ${symbol}:`, error);
    throw error;
  }
};

export const getStockHistory = async (symbol, period = '1mo') => {
  try {
    const response = await api.get(`/api/stocks/history/${symbol}?period=${period}`);
    return response.data.history;
  } catch (error) {
    console.error(`Error fetching stock history for ${symbol}:`, error);
    throw error;
  }
};

// Alert API calls
export const createAlert = async (alertData) => {
  try {
    const response = await api.post('/api/alerts/create', alertData);
    return response.data;
  } catch (error) {
    console.error('Error creating alert:', error);
    throw error;
  }
};

export const getUserAlerts = async (email) => {
  try {
    const response = await api.get(`/api/alerts/user/${email}`);
    return response.data.alerts;
  } catch (error) {
    console.error(`Error fetching alerts for ${email}:`, error);
    throw error;
  }
};

export const updateAlert = async (alertId, data) => {
  try {
    const response = await api.put(`/api/alerts/${alertId}`, data);
    return response.data;
  } catch (error) {
    console.error(`Error updating alert ${alertId}:`, error);
    throw error;
  }
};

export const deleteAlert = async (alertId) => {
  try {
    const response = await api.delete(`/api/alerts/${alertId}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting alert ${alertId}:`, error);
    throw error;
  }
};

export const getTriggeredAlerts = async () => {
  try {
    const response = await api.get('/api/alerts/triggered');
    return response.data.triggered_alerts;
  } catch (error) {
    console.error('Error fetching triggered alerts:', error);
    throw error;
  }
};

export const getAlertTypes = async () => {
  try {
    const response = await api.get('/api/alerts/types');
    return response.data.alert_types;
  } catch (error) {
    console.error('Error fetching alert types:', error);
    throw error;
  }
};

export default api; 