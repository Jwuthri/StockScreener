import React, { useState } from 'react';
import { 
  Box, Typography, Paper, Button, List, ListItem, 
  ListItemText, Collapse, IconButton, Chip 
} from '@mui/material';
import { useStockData } from '../context/StockDataContext';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const CacheDebugger = () => {
  const { cachedData, clearCache, clearCacheForKey } = useStockData();
  const [open, setOpen] = useState(false);
  
  // Get formatted date and time difference
  const getTimeInfo = (timestamp) => {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffSeconds = Math.floor((diffMs % 60000) / 1000);
    
    return `${date.toLocaleTimeString()} (${diffMinutes}m ${diffSeconds}s ago)`;
  };
  
  const cacheEntries = Object.entries(cachedData);
  
  if (cacheEntries.length === 0) {
    return null; // Don't show anything if cache is empty
  }
  
  return (
    <Box sx={{ position: 'fixed', bottom: 20, right: 20, zIndex: 1000, maxWidth: 400 }}>
      <Paper sx={{ p: 2, boxShadow: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
            Cache Status {cacheEntries.length > 0 && 
              <Chip 
                label={cacheEntries.length} 
                size="small" 
                color="primary" 
                sx={{ ml: 1 }} 
              />
            }
          </Typography>
          <Box>
            <IconButton size="small" onClick={() => setOpen(!open)}>
              {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
            <IconButton size="small" color="error" onClick={clearCache} title="Clear all cache">
              <DeleteIcon />
            </IconButton>
          </Box>
        </Box>
        
        <Collapse in={open}>
          <List dense sx={{ mt: 1, maxHeight: 300, overflowY: 'auto' }}>
            {cacheEntries.map(([key, { timestamp, expiryMinutes, data }]) => (
              <ListItem key={key} divider sx={{ display: 'block' }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <ListItemText
                    primary={key}
                    secondary={`Updated: ${getTimeInfo(timestamp)}`}
                    primaryTypographyProps={{ 
                      variant: 'body2', 
                      fontWeight: 'medium',
                      noWrap: true,
                      sx: { maxWidth: 280 }
                    }}
                    secondaryTypographyProps={{ 
                      variant: 'caption',
                      display: 'block'
                    }}
                  />
                  <IconButton 
                    size="small" 
                    onClick={() => clearCacheForKey(key)}
                    sx={{ mt: -0.5 }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
                <Box sx={{ display: 'flex', mt: 0.5 }}>
                  <Chip 
                    size="small" 
                    label={`Items: ${Array.isArray(data) ? data.length : 'N/A'}`}
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  <Chip 
                    size="small" 
                    label={`Expiry: ${expiryMinutes}m`}
                    variant="outlined"
                  />
                </Box>
              </ListItem>
            ))}
          </List>
        </Collapse>
      </Paper>
    </Box>
  );
};

export default CacheDebugger; 