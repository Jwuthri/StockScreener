import React from 'react';
import {
  List, ListItem, ListItemText, Divider,
  Typography, Box, CircularProgress, Chip
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

const StockList = ({ stocks, loading, emptyMessage }) => {
  const navigate = useNavigate();

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress size={30} />
      </Box>
    );
  }

  if (!stocks || stocks.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary">{emptyMessage}</Typography>
      </Box>
    );
  }

  return (
    <List disablePadding>
      {stocks.map((stock, index) => (
        <React.Fragment key={stock.symbol || `stock-${index}`}>
          {index > 0 && <Divider />}
          <ListItem
            button
            onClick={() => navigate(`/stock/${stock.symbol}`)}
            sx={{ py: 1.5 }}
          >
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body1" fontWeight="bold">
                    {stock.symbol}
                  </Typography>
                  <Typography variant="body1">
                    {stock.price}
                  </Typography>
                </Box>
              }
              secondary={
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                  <Typography variant="body2" noWrap sx={{ maxWidth: '60%' }}>
                    {stock.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      color: stock.change_percent?.includes('-')
                        ? 'error.main'
                        : 'success.main'
                    }}
                  >
                    {stock.change_percent}
                  </Typography>
                </Box>
              }
            />
          </ListItem>
        </React.Fragment>
      ))}
    </List>
  );
};

export default StockList;
