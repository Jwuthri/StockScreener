import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  TextField, 
  Button, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Typography, 
  Box,
  CircularProgress,
  Divider,
  Alert
} from '@mui/material';
import axios from 'axios';

const CreateAlertDialog = ({ open, onClose, stockSymbol = '' }) => {
  const [alertData, setAlertData] = useState({
    stock_symbol: stockSymbol,
    user_email: '',
    alert_type: 'price_above',
    threshold_value: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentPrice, setCurrentPrice] = useState(null);
  const [alertTypes, setAlertTypes] = useState([]);
  
  // Fetch current price and alert types on open
  useEffect(() => {
    if (open && stockSymbol) {
      fetchCurrentPrice();
      fetchAlertTypes();
    }
  }, [open, stockSymbol]);
  
  const fetchCurrentPrice = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/stocks/price/${stockSymbol}`);
      setCurrentPrice(response.data.price);
    } catch (error) {
      console.error('Error fetching price:', error);
      setError('Failed to fetch current price');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchAlertTypes = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/alerts/types`);
      setAlertTypes(response.data.alert_types);
    } catch (error) {
      console.error('Error fetching alert types:', error);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setAlertData({
      ...alertData,
      [name]: value
    });
  };
  
  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Validate inputs
      if (!alertData.user_email) {
        setError('Email is required');
        setLoading(false);
        return;
      }
      
      if (!alertData.threshold_value) {
        setError('Threshold value is required');
        setLoading(false);
        return;
      }
      
      // Create alert
      await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/alerts/create`,
        alertData
      );
      
      onClose(true); // Close with success
    } catch (error) {
      console.error('Error creating alert:', error);
      setError(error.response?.data?.detail || 'Failed to create alert');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onClose={() => onClose(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Typography variant="h6" component="div">
          Create Alert for {stockSymbol}
        </Typography>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading && !currentPrice ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={40} />
          </Box>
        ) : (
          <>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {currentPrice !== null && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Current Price
                </Typography>
                <Typography variant="h4" color="primary" sx={{ fontWeight: 'bold' }}>
                  ${currentPrice.toFixed(2)}
                </Typography>
                <Divider sx={{ my: 2 }} />
              </Box>
            )}
            
            <TextField
              margin="dense"
              label="Email"
              type="email"
              fullWidth
              name="user_email"
              value={alertData.user_email}
              onChange={handleChange}
              required
              variant="outlined"
              sx={{ mb: 2 }}
            />
            
            <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
              <InputLabel id="alert-type-label">Alert Type</InputLabel>
              <Select
                labelId="alert-type-label"
                id="alert-type"
                name="alert_type"
                value={alertData.alert_type}
                onChange={handleChange}
                label="Alert Type"
              >
                {alertTypes.map((type) => (
                  <MenuItem key={type.type} value={type.type}>
                    {type.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
              margin="dense"
              label="Threshold Value"
              type="number"
              fullWidth
              name="threshold_value"
              value={alertData.threshold_value}
              onChange={handleChange}
              required
              variant="outlined"
              InputProps={{
                startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>,
              }}
              helperText={
                alertData.alert_type === 'price_above' 
                  ? 'You will be alerted when the price goes above this value'
                  : alertData.alert_type === 'price_below'
                  ? 'You will be alerted when the price goes below this value'
                  : alertData.alert_type === 'volume_above'
                  ? 'You will be alerted when the volume goes above this value'
                  : 'You will be alerted when the percent change exceeds this value'
              }
            />
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button 
          onClick={() => onClose(false)} 
          color="inherit"
          disabled={loading}
        >
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          Create Alert
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateAlertDialog; 