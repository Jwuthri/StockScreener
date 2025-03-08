import React, { useState } from 'react';
import {
    Box,
    Typography,
    TextField,
    Button,
    Paper,
    Alert,
    Link,
    useTheme
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { login } from '../services/auth';

const Login = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({
        username: false,
        password: false
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Clear field error when user types
        setFieldErrors(prev => ({
            ...prev,
            [name]: false
        }));
        // Clear general error when user types
        if (error) setError('');
    };

    const validateForm = () => {
        const newFieldErrors = {
            username: !formData.username.trim(),
            password: !formData.password.trim()
        };

        setFieldErrors(newFieldErrors);
        return !Object.values(newFieldErrors).some(Boolean);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            setError('Please fill in all required fields');
            return;
        }

        setError('');
        setLoading(true);

        try {
            await login(formData.username, formData.password);
            navigate('/screener'); // Redirect to main page after login
        } catch (error) {
            // Handle different types of error responses
            if (error.response?.data?.detail) {
                if (typeof error.response.data.detail === 'string') {
                    setError(error.response.data.detail);
                } else if (Array.isArray(error.response.data.detail)) {
                    setError(error.response.data.detail[0]?.msg || 'Invalid credentials');
                } else if (typeof error.response.data.detail === 'object') {
                    setError(error.response.data.detail.msg || 'Invalid credentials');
                }
            } else {
                setError('Failed to login. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box
            sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '100vh',
                bgcolor: theme.palette.background.default,
                p: 3
            }}
        >
            <Paper
                elevation={3}
                sx={{
                    p: 4,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    maxWidth: 400,
                    width: '100%'
                }}
            >
                <Typography component="h1" variant="h4" gutterBottom>
                    Login
                </Typography>

                {error && (
                    <Alert severity="error" sx={{ mb: 2, width: '100%' }}>
                        {error}
                    </Alert>
                )}

                <Box
                    component="form"
                    onSubmit={handleSubmit}
                    sx={{ width: '100%' }}
                    noValidate // Disable browser's HTML5 validation
                >
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="username"
                        label="Username"
                        name="username"
                        autoComplete="username"
                        autoFocus
                        value={formData.username}
                        onChange={handleChange}
                        error={fieldErrors.username}
                        helperText={fieldErrors.username ? 'Username is required' : ''}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        name="password"
                        label="Password"
                        type="password"
                        id="password"
                        autoComplete="current-password"
                        value={formData.password}
                        onChange={handleChange}
                        error={fieldErrors.password}
                        helperText={fieldErrors.password ? 'Password is required' : ''}
                    />
                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        sx={{
                            mt: 3,
                            mb: 2,
                            bgcolor: theme.palette.success.main,
                            '&:hover': {
                                bgcolor: theme.palette.success.dark
                            }
                        }}
                        disabled={loading}
                    >
                        {loading ? 'Logging in...' : 'Login'}
                    </Button>
                </Box>

                <Box sx={{ mt: 2 }}>
                    <Link href="/register" variant="body2" sx={{ color: theme.palette.success.main }}>
                        {"Don't have an account? Sign Up"}
                    </Link>
                </Box>
            </Paper>
        </Box>
    );
};

export default Login;
