/**
 * Auth Module - Handles authentication
 */

const Auth = {
    /**
     * Check if user is logged in
     */
    isLoggedIn() {
        return !!API.getToken();
    },

    /**
     * Get current user
     */
    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },

    /**
     * Save user to storage
     */
    setUser(user) {
        localStorage.setItem('user', JSON.stringify(user));
    },

    /**
     * Login
     */
    async login(email, password) {
        const data = await fetch(`${API.BASE_URL}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        }).then(res => {
            if (!res.ok) {
                return res.json().then(err => Promise.reject(err));
            }
            return res.json();
        });

        API.setTokens(data.access, data.refresh);
        this.setUser(data.user);

        return data.user;
    },

    /**
     * Logout
     */
    async logout() {
        try {
            const refreshToken = API.getRefreshToken();
            if (refreshToken) {
                await API.post('/auth/logout/', { refresh: refreshToken });
            }
        } catch (e) {
            // Ignore logout errors
        }
        API.clearTokens();
    },

    /**
     * Register
     */
    async register(email, username, password) {
        const data = await API.post('/auth/register/', {
            email,
            username,
            password,
            password_confirm: password,
        });

        API.setTokens(data.access, data.refresh);
        this.setUser(data.user);

        return data.user;
    },
};

// Make available globally
window.Auth = Auth;
