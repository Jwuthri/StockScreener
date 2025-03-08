import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Paper, CircularProgress, Button } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { fetchTopGainers, fetchTopLosers, fetchMostActive, refreshHomePageData } from '../utils/stockDataUtils';
import StockList from '../components/StockList';

const Home = () => {
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [mostActive, setMostActive] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState('');

  // Load data on component mount
  useEffect(() => {
    const loadHomePageData = async () => {
      setLoading(true);
      try {
        // Fetch all data in parallel
        const [gainers, losers, active] = await Promise.all([
          fetchTopGainers(),
          fetchTopLosers(),
          fetchMostActive()
        ]);

        setTopGainers(gainers);
        setTopLosers(losers);
        setMostActive(active);
        setLastUpdated(new Date());
      } catch (error) {
        console.error('Error loading home page data:', error);
        setError('Failed to load market data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadHomePageData();
  }, []);

  // Handle refresh button click
  const handleRefresh = async () => {
    setLoading(true);
    setError('');

    try {
      const refreshedData = await refreshHomePageData();
      setTopGainers(refreshedData.topGainers);
      setTopLosers(refreshedData.topLosers);
      setMostActive(refreshedData.mostActive);
      setLastUpdated(refreshedData.lastUpdated);
    } catch (error) {
      setError('Failed to refresh data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">Market Overview</Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {lastUpdated && (
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}

          <Button
            variant="outlined"
            startIcon={loading ? <CircularProgress size={20} /> : <RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'error.light', color: 'error.contrastText' }}>
          <Typography>{error}</Typography>
        </Paper>
      )}

      <Grid container spacing={3}>
        {/* Top Gainers */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
              Top Gainers
            </Typography>
            <StockList
              stocks={topGainers}
              loading={loading}
              emptyMessage="No gainers data available"
            />
          </Paper>
        </Grid>

        {/* Top Losers */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'error.main' }}>
              Top Losers
            </Typography>
            <StockList
              stocks={topLosers}
              loading={loading}
              emptyMessage="No losers data available"
            />
          </Paper>
        </Grid>

        {/* Most Active */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ color: 'info.main' }}>
              Most Active
            </Typography>
            <StockList
              stocks={mostActive}
              loading={loading}
              emptyMessage="No active stocks data available"
            />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home;
