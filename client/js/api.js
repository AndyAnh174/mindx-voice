/**
 * API Module - Handles all HTTP requests to backend
 */

const API = {
    BASE_URL: '/api',

    /**
     * Get stored access token
     */
    getToken() {
        return localStorage.getItem('access_token');
    },

    /**
     * Get refresh token
     */
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },

    /**
     * Store tokens
     */
    setTokens(access, refresh) {
        localStorage.setItem('access_token', access);
        if (refresh) {
            localStorage.setItem('refresh_token', refresh);
        }
    },

    /**
     * Clear tokens
     */
    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
    },

    /**
     * Make API request with auth
     */
    async request(endpoint, options = {}) {
        const url = `${this.BASE_URL}${endpoint}`;
        const token = this.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            let response = await fetch(url, {
                ...options,
                headers,
            });

            // If 401, try to refresh token
            if (response.status === 401 && this.getRefreshToken()) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getToken()}`;
                    response = await fetch(url, { ...options, headers });
                }
            }

            // Parse response
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw { status: response.status, data };
            }

            return data;
        } catch (error) {
            if (error.status === 401) {
                this.clearTokens();
                window.location.hash = '#/login';
            }
            throw error;
        }
    },

    /**
     * Refresh access token
     */
    async refreshToken() {
        try {
            const response = await fetch(`${this.BASE_URL}/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh: this.getRefreshToken() }),
            });

            if (response.ok) {
                const data = await response.json();
                this.setTokens(data.access);
                return true;
            }
            return false;
        } catch {
            return false;
        }
    },

    /**
     * GET request
     */
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },

    /**
     * PATCH request
     */
    patch(endpoint, body) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(body),
        });
    },

    /**
     * DELETE request
     */
    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },
};

// Make available globally
window.API = API;
