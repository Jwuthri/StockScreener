import React, { useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  InputBase, 
  IconButton, 
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Box,
  useTheme
} from '@mui/material';
import { alpha, styled } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import NotificationsIcon from '@mui/icons-material/Notifications';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import { useNavigate } from 'react-router-dom';

// Custom styled components
const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: 30,
  backgroundColor: alpha(theme.palette.common.black, 0.04),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.black, 0.07),
  },
  marginRight: theme.spacing(2),
  marginLeft: theme.spacing(3),
  width: '100%',
  maxWidth: 380,
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(3),
    width: 'auto',
  },
  transition: 'all 0.2s ease',
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: theme.palette.text.secondary,
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: theme.palette.text.primary,
  width: '100%',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1.2, 1, 1.2, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    fontSize: '0.9rem',
  },
}));

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  minHeight: 64,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: theme.spacing(0, 3),
  [theme.breakpoints.up('lg')]: {
    padding: theme.spacing(0, 5),
  },
}));

const LogoSection = styled('div')({
  display: 'flex',
  alignItems: 'center',
});

const NavbarActions = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
}));

const BrandText = styled(Typography)(({ theme }) => ({
  fontWeight: 700,
  fontSize: '1.25rem',
  letterSpacing: '-0.03em',
  cursor: 'pointer'
}));

const Navbar = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSearchSubmit = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      navigate(`/stock/${searchQuery.trim().toUpperCase()}`);
      setSearchQuery('');
    }
  };
  
  return (
    <AppBar 
      position="fixed" 
      elevation={0}
      sx={{ 
        backgroundColor: 'white',
        borderBottom: `1px solid ${theme.palette.divider}`,
        color: theme.palette.text.primary,
      }}
    >
      <StyledToolbar>
        <LogoSection>
          <BrandText 
            onClick={() => navigate('/')}
          >
            InvestGuru
          </BrandText>
        </LogoSection>
        
        <Search>
          <SearchIconWrapper>
            <SearchIcon fontSize="small" />
          </SearchIconWrapper>
          <StyledInputBase
            placeholder="Search symbols"
            inputProps={{ 'aria-label': 'search' }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleSearchSubmit}
          />
        </Search>
        
        <NavbarActions>
          <Box 
            sx={{ 
              display: 'flex', 
              gap: 1, 
              mr: 2, 
              cursor: 'pointer',
              '&:hover': {
                color: theme.palette.primary.main
              }
            }}
            onClick={() => navigate('/screener')}
          >
            <Typography 
              variant="body2" 
              sx={{ fontWeight: 500 }}
            >
              Screener
            </Typography>
            <KeyboardArrowDownIcon fontSize="small" />
          </Box>
          
          <IconButton 
            color="inherit" 
            size="medium" 
            onClick={() => navigate('/alerts')}
            sx={{ color: theme.palette.text.primary }}
          >
            <Badge badgeContent={2} color="error">
              <NotificationsIcon fontSize="small" />
            </Badge>
          </IconButton>
          
          <IconButton
            edge="end"
            aria-label="account of current user"
            aria-haspopup="true"
            onClick={handleProfileMenuOpen}
            color="inherit"
            size="medium"
          >
            <Avatar 
              sx={{ 
                width: 30, 
                height: 30,
                bgcolor: theme.palette.grey[100],
                color: theme.palette.text.primary
              }}
            >
              <AccountCircleIcon fontSize="small" />
            </Avatar>
          </IconButton>
        </NavbarActions>
        
        <Menu
          anchorEl={anchorEl}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          PaperProps={{
            elevation: 2,
            sx: {
              minWidth: 180,
              borderRadius: 2,
              mt: 1,
              '& .MuiMenuItem-root': {
                fontSize: '0.9rem',
                py: 1.2
              }
            },
          }}
        >
          <MenuItem onClick={handleMenuClose}>Portfolio</MenuItem>
          <MenuItem onClick={handleMenuClose}>Account</MenuItem>
          <Divider sx={{ my: 1 }} />
          <MenuItem onClick={handleMenuClose}>Settings</MenuItem>
          <MenuItem onClick={handleMenuClose}>Sign Out</MenuItem>
        </Menu>
      </StyledToolbar>
    </AppBar>
  );
};

export default Navbar;
