import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
import Login from './pages/Login';
import Register from './pages/Register';
import StocksCrossingPrevHighPage from './pages/StocksCrossingPrevHighPage';

// Auth
import { isAuthenticated } from './services/auth';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  return children;
};

// Layout wrapper for authenticated pages
const AuthenticatedLayout = ({ children }) => (
  <Box sx={{ display: 'flex' }}>
    <Navbar />
    <Sidebar />
    <NotificationCenter />
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: { xs: 2, sm: 3, md: 4 },
        mt: 8,
        ml: { sm: '20px' },
        width: { sm: `calc(100% - 20px)` },
        backgroundColor: theme.palette.background.default,
        minHeight: '100vh',
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}
    >
      <Box
        sx={{
          width: '100%',
          maxWidth: '1200px',
          px: { xs: 1, sm: 2 }
        }}
      >
        {children}
      </Box>
    </Box>
  </Box>
);

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <Dashboard />
              </AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/stock/:symbol" element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <StockDetail />
              </AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/screener" element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <StockScreener />
              </AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/alerts" element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <Alerts />
              </AuthenticatedLayout>
            </ProtectedRoute>
          } />
          <Route path="/stocks/crossing-prev-high" element={<StocksCrossingPrevHighPage />} />

          {/* Redirect all other routes to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
