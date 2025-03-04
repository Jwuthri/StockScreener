import api from './api';

const AUTH_TOKEN_KEY = 'auth_token';

export const login = async (username, password) => {
    try {
        // Use URLSearchParams for x-www-form-urlencoded format
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await api.post('/api/auth/token', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        const { access_token } = response.data;
        
        // Store the token
        localStorage.setItem(AUTH_TOKEN_KEY, access_token);
        
        // Update axios default headers
        api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
};

export const register = async (username, email, password) => {
    try {
        const response = await api.post('/api/auth/register', {
            username,
            email,
            password
        });
        return response.data;
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
};

export const logout = () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    delete api.defaults.headers.common['Authorization'];
};

export const getCurrentUser = async () => {
    try {
        const response = await api.get('/api/auth/me');
        return response.data;
    } catch (error) {
        console.error('Error getting current user:', error);
        return null;
    }
};

export const isAuthenticated = () => {
    return !!localStorage.getItem(AUTH_TOKEN_KEY);
};

// Initialize auth header if token exists
const token = localStorage.getItem(AUTH_TOKEN_KEY);
if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
} 