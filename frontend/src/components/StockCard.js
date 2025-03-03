import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Chip,
  IconButton,
  Divider,
  Skeleton
} from '@mui/material';
import { 
  TrendingUp as TrendingUpIcon, 
  TrendingDown as TrendingDownIcon,
  Notifications as NotificationsIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const StockCard = ({ symbol, name, onAddAlert }) => {
  const navigate = useNavigate();
  const [stockData, setStockData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFavorite, setIsFavorite] = useState(false);
  
  useEffect(() => {
    const fetchStockData = async () => {
      try {
        setIsLoading(true);
        // Replace with your actual API endpoint
        const response = await axios.get(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/stocks/price/${symbol}`);
        setStockData({
          price: response.data.price,
          // Mock data for demonstration
          change: (Math.random() * 5 - 2.5).toFixed(2),
          changePercent: (Math.random() * 5 - 2.5).toFixed(2)
        });
      } catch (error) {
        console.error('Error fetching stock data:', error);
        setStockData({
          price: 0,
          change: 0,
          changePercent: 0
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchStockData();
  }, [symbol]);
  
  const handleAddToFavorites = (e) => {
    e.stopPropagation();
    setIsFavorite(!isFavorite);
    // Logic to add/remove from favorites would go here
  };
  
  const handleAddAlert = (e) => {
    e.stopPropagation();
    if (onAddAlert) {
      onAddAlert(symbol);
    }
  };
  
  const handleCardClick = () => {
    navigate(`/stock/${symbol}`);
  };
  
  const isPositive = stockData && parseFloat(stockData.change) >= 0;
  
  return (
    <Card 
      sx={{ 
        height: '100%', 
        cursor: 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 40px 0 rgba(0, 0, 0, 0.5)',
        }
      }}
      onClick={handleCardClick}
    >
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Box>
            <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
              {symbol}
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: '120px' }}>
              {name}
            </Typography>
          </Box>
          
          <Box>
            <IconButton 
              size="small" 
              color={isFavorite ? 'warning' : 'default'}
              onClick={handleAddToFavorites}
            >
              {isFavorite ? <StarIcon /> : <StarBorderIcon />}
            </IconButton>
            <IconButton 
              size="small" 
              color="primary"
              onClick={handleAddAlert}
            >
              <NotificationsIcon />
            </IconButton>
          </Box>
        </Box>
        
        <Divider sx={{ my: 1 }} />
        
        <Box sx={{ mt: 1, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          {isLoading ? (
            <>
              <Skeleton variant="text" width="80%" height={48} />
              <Skeleton variant="text" width="60%" />
            </>
          ) : (
            <>
              <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
                ${stockData?.price?.toFixed(2)}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Chip
                  icon={isPositive ? <TrendingUpIcon /> : <TrendingDownIcon />}
                  label={`${isPositive ? '+' : ''}${stockData?.change} (${stockData?.changePercent}%)`}
                  color={isPositive ? 'success' : 'error'}
                  size="small"
                  sx={{ fontWeight: 'bold', borderRadius: 1 }}
                />
              </Box>
            </>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default StockCard; 