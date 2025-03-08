import React, { useState, useEffect } from 'react';
import {
  Box, Typography, TextField, Button, Paper, Table,
  TableBody, TableCell, TableContainer, TableHead,
  TableRow, CircularProgress, Switch, Dialog,
  DialogTitle, DialogContent, DialogActions, FormControl,
  InputLabel, Select, MenuItem, IconButton, Alert, useTheme
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useSearchParams } from 'react-router-dom';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const alertTypes = [
  { value: 'price_above', label: 'Price Above' },
  { value: 'price_below', label: 'Price Below' },
  { value: 'volume_above', label: 'Volume Above' },
  { value: 'volume_below', label: 'Volume Below' },
];

const Alerts = () => {
  const theme = useTheme();
  const [searchParams] = useSearchParams();
  const stockSymbol = searchParams.get('stock');

  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedStock, setSelectedStock] = useState(stockSymbol || '');
  const [alertType, setAlertType] = useState('price_above');
  const [threshold, setThreshold] = useState('');
  const [stocks, setStocks] = useState([]);
  const [error, setError] = useState('');

  // Fetch user alerts when email changes
  useEffect(() => {
    if (email) {
      fetchAlerts();
    }
  }, [email]);

  // Handle stock symbol from query params
  useEffect(() => {
    if (stockSymbol) {
      setSelectedStock(stockSymbol);
      setOpenDialog(true);
    }
  }, [stockSymbol]);

  // Fetch available stocks
  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/stocks/popular`);
        setStocks(response.data.popular_stocks);
      } catch (error) {
        console.error('Error fetching stocks:', error);
      }
    };

    fetchStocks();
  }, []);

  const fetchAlerts = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await axios.get(`${API_URL}/api/alerts?email=${email}`);
      setAlerts(response.data.alerts);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      setError('Failed to load alerts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async () => {
    if (!email || !selectedStock || !alertType || !threshold) {
      setError('Please fill in all required fields.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await axios.post(`${API_URL}/api/alerts`, {
        user_email: email,
        stock_symbol: selectedStock,
        alert_type: alertType,
        threshold_value: parseFloat(threshold)
      });

      // Refresh the alerts list
      fetchAlerts();
      setOpenDialog(false);
      // Reset form
      setSelectedStock('');
      setAlertType('price_above');
      setThreshold('');
    } catch (error) {
      console.error('Error creating alert:', error);
      setError('Failed to create alert. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setError('');
  };

  const handleToggleAlert = async (alertId, isActive) => {
    try {
      await axios.put(`${API_URL}/api/alerts/${alertId}`, {
        is_active: !isActive
      });

      // Update the alert in the local state
      setAlerts(alerts.map(alert =>
        alert.id === alertId ? { ...alert, is_active: !isActive } : alert
      ));
    } catch (error) {
      console.error('Error updating alert:', error);
      setError('Failed to update alert status. Please try again.');
    }
  };

  const handleDeleteAlert = async (alertId) => {
    try {
      await axios.delete(`${API_URL}/api/alerts/${alertId}`);

      // Remove the alert from the local state
      setAlerts(alerts.filter(alert => alert.id !== alertId));
    } catch (error) {
      console.error('Error deleting alert:', error);
      setError('Failed to delete alert. Please try again.');
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Stock Price Alerts
      </Typography>

      {/* Email input section */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <TextField
          label="Your Email"
          variant="outlined"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          sx={{ mr: 2, flexGrow: 1 }}
        />
        <Button
          variant="contained"
          color="primary"
          onClick={fetchAlerts}
          disabled={!email}
        >
          Load My Alerts
        </Button>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
          sx={{ ml: 2 }}
          disabled={!email}
        >
          New Alert
        </Button>
      </Box>

      {/* Error message */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading indicator */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Alerts table */}
          {alerts.length > 0 ? (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Stock</TableCell>
                    <TableCell>Alert Type</TableCell>
                    <TableCell>Threshold</TableCell>
                    <TableCell>Active</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.id} hover>
                      <TableCell sx={{ fontWeight: 'bold' }}>
                        {alert.stock_symbol}
                      </TableCell>
                      <TableCell>
                        {alertTypes.find(type => type.value === alert.alert_type)?.label || alert.alert_type}
                      </TableCell>
                      <TableCell>{alert.threshold_value}</TableCell>
                      <TableCell>
                        <Switch
                          checked={alert.is_active}
                          onChange={() => handleToggleAlert(alert.id, alert.is_active)}
                          color="primary"
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          color="error"
                          onClick={() => handleDeleteAlert(alert.id)}
                          size="small"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            email ? (
              <Typography variant="body1">
                No alerts found. Create a new alert to get started.
              </Typography>
            ) : (
              <Typography variant="body1">
                Enter your email and click "Load My Alerts" to view your alerts.
              </Typography>
            )
          )}
        </>
      )}

      {/* Create Alert Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Alert</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Stock</InputLabel>
              <Select
                value={selectedStock}
                onChange={(e) => setSelectedStock(e.target.value)}
                label="Stock"
              >
                {stocks.map((stock) => (
                  <MenuItem key={stock.symbol} value={stock.symbol}>
                    {stock.symbol} - {stock.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Alert Type</InputLabel>
              <Select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value)}
                label="Alert Type"
              >
                {alertTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Threshold Value"
              variant="outlined"
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
              sx={{ mb: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleCreateAlert}
            variant="contained"
            color="primary"
            disabled={!email || !selectedStock || !alertType || !threshold}
          >
            Create Alert
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Alerts;
