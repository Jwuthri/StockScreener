import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Box,
  Divider,
  Typography,
  useTheme
} from '@mui/material';
import { styled } from '@mui/material/styles';
import { useNavigate, useLocation } from 'react-router-dom';
import { Link } from 'react-router-dom';

// Icons
import HomeOutlinedIcon from '@mui/icons-material/HomeOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import NotificationsNoneOutlinedIcon from '@mui/icons-material/NotificationsNoneOutlined';
import ShowChartOutlinedIcon from '@mui/icons-material/ShowChartOutlined';
import TrendingUpOutlinedIcon from '@mui/icons-material/TrendingUpOutlined';
import TrendingDownOutlinedIcon from '@mui/icons-material/TrendingDownOutlined';
import AccountBalanceWalletOutlinedIcon from '@mui/icons-material/AccountBalanceWalletOutlined';
import StarOutlineOutlinedIcon from '@mui/icons-material/StarOutlineOutlined';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

const drawerWidth = 220;

const StyledListItem = styled(ListItem)(({ theme, active }) => ({
  padding: theme.spacing(1.2, 2),
  margin: theme.spacing(0.5, 1),
  borderRadius: 8,
  transition: 'all 0.2s ease',
  backgroundColor: active ? theme.palette.grey[100] : 'transparent',
  '&:hover': {
    backgroundColor: active
      ? theme.palette.grey[100]
      : theme.palette.grey[50],
  },
}));

const SectionLabel = styled(Typography)(({ theme }) => ({
  fontSize: '0.75rem',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: theme.palette.text.secondary,
  padding: theme.spacing(2, 3, 1),
}));

const Sidebar = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: drawerWidth,
          boxSizing: 'border-box',
          border: 'none',
          borderRight: `1px solid ${theme.palette.divider}`,
          boxShadow: 'none',
          backgroundColor: theme.palette.background.paper,
        },
        display: { xs: 'none', sm: 'block' }
      }}
    >
      <Box sx={{ mt: 8, overflow: 'auto', px: 1, py: 2 }}>
        <List component="nav" disablePadding>
          <StyledListItem
            button
            onClick={() => navigate('/')}
            active={isActive('/') ? 1 : 0}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: isActive('/') ? theme.palette.text.primary : theme.palette.text.secondary
            }}>
              <HomeOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Home"
              primaryTypographyProps={{
                fontWeight: isActive('/') ? 600 : 500,
                color: isActive('/') ? theme.palette.text.primary : theme.palette.text.secondary,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>

          <StyledListItem
            button
            onClick={() => navigate('/screener')}
            active={isActive('/screener') ? 1 : 0}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: isActive('/screener') ? theme.palette.text.primary : theme.palette.text.secondary
            }}>
              <SearchOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Browse"
              primaryTypographyProps={{
                fontWeight: isActive('/screener') ? 600 : 500,
                color: isActive('/screener') ? theme.palette.text.primary : theme.palette.text.secondary,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>

          <StyledListItem
            button
            onClick={() => navigate('/alerts')}
            active={isActive('/alerts') ? 1 : 0}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: isActive('/alerts') ? theme.palette.text.primary : theme.palette.text.secondary
            }}>
              <NotificationsNoneOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Alerts"
              primaryTypographyProps={{
                fontWeight: isActive('/alerts') ? 600 : 500,
                color: isActive('/alerts') ? theme.palette.text.primary : theme.palette.text.secondary,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>
        </List>

        <Divider sx={{ my: 2 }} />

        <SectionLabel>Lists</SectionLabel>
        <List component="nav" disablePadding>
          <StyledListItem
            button
            onClick={() => navigate('/?filter=watchlist')}
            active={location.pathname === '/' && location.search.includes('watchlist') ? 1 : 0}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: theme.palette.text.secondary
            }}>
              <StarOutlineOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Watchlist"
              primaryTypographyProps={{
                fontWeight: 500,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>

          <StyledListItem
            button
            onClick={() => navigate('/?filter=portfolio')}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: theme.palette.text.secondary
            }}>
              <AccountBalanceWalletOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Portfolio"
              primaryTypographyProps={{
                fontWeight: 500,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>
        </List>

        <Divider sx={{ my: 2 }} />

        <SectionLabel>Market Trends</SectionLabel>
        <List component="nav" disablePadding>
          <StyledListItem
            button
            onClick={() => navigate('/?filter=gainers')}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: theme.palette.success.main
            }}>
              <TrendingUpOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Top Gainers"
              primaryTypographyProps={{
                fontWeight: 500,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>

          <StyledListItem
            button
            onClick={() => navigate('/?filter=losers')}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: theme.palette.error.main
            }}>
              <TrendingDownOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Top Losers"
              primaryTypographyProps={{
                fontWeight: 500,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>

          <StyledListItem
            button
            onClick={() => navigate('/?filter=mostActive')}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: theme.palette.text.secondary
            }}>
              <ShowChartOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Most Active"
              primaryTypographyProps={{
                fontWeight: 500,
                fontSize: '0.95rem'
              }}
            />
          </StyledListItem>

          <StyledListItem
            button
            onClick={() => navigate('/stocks/crossing-prev-high')}
          >
            <ListItemIcon sx={{
              minWidth: 36,
              color: theme.palette.common.black
            }}>
              <ShowChartOutlinedIcon />
            </ListItemIcon>
            <ListItemText
              primary="Cross Prev High"
              primaryTypographyProps={{
                fontWeight: 500,
                fontSize: '0.95rem'
              }}
            />

          </StyledListItem>
          {/* <ListItem
            button
            component={Link}
            to="/stocks/crossing-prev-high"
            sx={{
              pl: 2,
              py: 1,
              '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' }
            }}
          >
            <ListItemIcon>
              <TrendingUpIcon color="success" />
            </ListItemIcon>
            <ListItemText primary="Cross High" />
          </ListItem> */}
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
