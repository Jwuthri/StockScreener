import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import theme from './theme';

// Layout components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import NotificationCenter from './components/NotificationCenter';

// Pages
import Dashboard from './pages/Dashboard';
import StockDetail from './pages/StockDetail';
import StockScreener from './pages/StockScreener';
import Alerts from './pages/Alerts';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          <Navbar />
          <Sidebar />
          <NotificationCenter />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 4,
              mt: 8,
              ml: { sm: '240px' },
              width: { sm: `calc(100% - 240px)` },
              backgroundColor: theme.palette.background.default,
              minHeight: '100vh',
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stock/:symbol" element={<StockDetail />} />
              <Route path="/screener" element={<StockScreener />} />
              <Route path="/alerts" element={<Alerts />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
