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
import { register } from '../services/auth';

const Register = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [fieldErrors, setFieldErrors] = useState({
        username: false,
        email: false,
        password: false,
        confirmPassword: false
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
            email: !formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email),
            password: !formData.password.trim(),
            confirmPassword: !formData.confirmPassword.trim() || formData.password !== formData.confirmPassword
        };
        
        setFieldErrors(newFieldErrors);
        return !Object.values(newFieldErrors).some(Boolean);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            if (formData.password !== formData.confirmPassword) {
                setError('Passwords do not match');
            } else {
                setError('Please fill in all required fields correctly');
            }
            return;
        }

        setLoading(true);

        try {
            await register(formData.username, formData.email, formData.password);
            navigate('/login', { state: { message: 'Registration successful! Please login.' } });
        } catch (error) {
            // Handle different types of error responses
            if (error.response?.data?.detail) {
                if (typeof error.response.data.detail === 'string') {
                    setError(error.response.data.detail);
                } else if (Array.isArray(error.response.data.detail)) {
                    setError(error.response.data.detail[0]?.msg || 'Registration failed');
                } else if (typeof error.response.data.detail === 'object') {
                    setError(error.response.data.detail.msg || 'Registration failed');
                }
            } else {
                setError('Failed to register. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    const getHelperText = (field) => {
        if (!fieldErrors[field]) return '';
        switch (field) {
            case 'username':
                return 'Username is required';
            case 'email':
                return !formData.email.trim() ? 'Email is required' : 'Please enter a valid email address';
            case 'password':
                return 'Password is required';
            case 'confirmPassword':
                return !formData.confirmPassword.trim() ? 'Please confirm your password' : 'Passwords do not match';
            default:
                return '';
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
                    Register
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
                        helperText={getHelperText('username')}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="email"
                        label="Email Address"
                        name="email"
                        autoComplete="email"
                        value={formData.email}
                        onChange={handleChange}
                        error={fieldErrors.email}
                        helperText={getHelperText('email')}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        name="password"
                        label="Password"
                        type="password"
                        id="password"
                        autoComplete="new-password"
                        value={formData.password}
                        onChange={handleChange}
                        error={fieldErrors.password}
                        helperText={getHelperText('password')}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        name="confirmPassword"
                        label="Confirm Password"
                        type="password"
                        id="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        error={fieldErrors.confirmPassword}
                        helperText={getHelperText('confirmPassword')}
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
                        {loading ? 'Registering...' : 'Register'}
                    </Button>
                </Box>

                <Box sx={{ mt: 2 }}>
                    <Link href="/login" variant="body2" sx={{ color: theme.palette.success.main }}>
                        {"Already have an account? Sign In"}
                    </Link>
                </Box>
            </Paper>
        </Box>
    );
};

export default Register; 