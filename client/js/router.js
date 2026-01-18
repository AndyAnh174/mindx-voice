/**
 * Simple Hash-based Router for SPA
 */

const Router = {
    routes: {},
    currentRoute: null,

    /**
     * Register a route
     */
    on(path, handler) {
        this.routes[path] = handler;
        return this;
    },

    /**
     * Navigate to a route
     */
    navigate(path, params = {}) {
        window.location.hash = `#${path}`;
    },

    /**
     * Get current path from hash
     */
    getPath() {
        const hash = window.location.hash.slice(1) || '/';
        // Extract base path without params
        return hash.split('?')[0];
    },

    /**
     * Get route params (e.g., /session/:id)
     */
    getParams(routePattern, actualPath) {
        const routeParts = routePattern.split('/');
        const pathParts = actualPath.split('/');
        const params = {};

        routeParts.forEach((part, index) => {
            if (part.startsWith(':')) {
                const paramName = part.slice(1);
                params[paramName] = pathParts[index];
            }
        });

        return params;
    },

    /**
     * Match path to route pattern
     */
    matchRoute(path) {
        // Exact match first
        if (this.routes[path]) {
            return { route: path, params: {} };
        }

        // Pattern matching (e.g., /session/:id)
        for (const route in this.routes) {
            if (route.includes(':')) {
                const routeParts = route.split('/');
                const pathParts = path.split('/');

                if (routeParts.length === pathParts.length) {
                    let match = true;
                    for (let i = 0; i < routeParts.length; i++) {
                        if (!routeParts[i].startsWith(':') && routeParts[i] !== pathParts[i]) {
                            match = false;
                            break;
                        }
                    }
                    if (match) {
                        return { route, params: this.getParams(route, path) };
                    }
                }
            }
        }

        return null;
    },

    /**
     * Handle route change
     */
    async handleRoute() {
        const path = this.getPath();
        const matched = this.matchRoute(path);

        // Protected routes check
        const publicRoutes = ['/login', '/register'];
        if (!publicRoutes.includes(path) && !Auth.isLoggedIn()) {
            this.navigate('/login');
            return;
        }

        // Redirect logged in users away from login
        if (path === '/login' && Auth.isLoggedIn()) {
            this.navigate('/dashboard');
            return;
        }

        if (matched) {
            this.currentRoute = matched.route;
            await this.routes[matched.route](matched.params);
        } else {
            // Default to dashboard or login
            if (Auth.isLoggedIn()) {
                this.navigate('/dashboard');
            } else {
                this.navigate('/login');
            }
        }
    },

    /**
     * Initialize router
     */
    init() {
        window.addEventListener('hashchange', () => this.handleRoute());
        window.addEventListener('load', () => {
            // Set default hash if none
            if (!window.location.hash) {
                window.location.hash = Auth.isLoggedIn() ? '#/dashboard' : '#/login';
            }
            this.handleRoute();
        });
        return this;
    },
};

// Make available globally
window.Router = Router;
