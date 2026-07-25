let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

export function createAuthFetch(getToken, setToken, logout) {
  return async function authFetch(url, options = {}) {
    // 1. Get current access token
    const accessToken = getToken();
    
    // 2. Setup headers
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const config = {
      ...options,
      headers
    };

    // 3. Make the initial request
    let response = await fetch(url, config);

    // 4. If 401 Unauthorized, handle token refresh
    if (response.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      
      // If no refresh token, we can't do anything but logout
      if (!refreshToken) {
        logout();
        return response;
      }

      if (isRefreshing) {
        // If already refreshing, wait for it to finish
        try {
          const newToken = await new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });
          
          // Retry the original request with the new token
          config.headers['Authorization'] = `Bearer ${newToken}`;
          return await fetch(url, config);
        } catch (err) {
          // If the queued refresh failed, return the original 401 response
          return response;
        }
      }

      // Start the refresh process
      isRefreshing = true;
      try {
        const refreshResponse = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${refreshToken}`
          }
        });

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          const newAccessToken = data.access_token;
          
          // Save new token
          localStorage.setItem('access_token', newAccessToken);
          setToken(newAccessToken);
          
          // Process queue before retrying this request, so others can proceed
          processQueue(null, newAccessToken);
          
          // Retry the original request with the new token
          config.headers['Authorization'] = `Bearer ${newAccessToken}`;
          response = await fetch(url, config);
        } else {
          // Refresh failed (e.g. refresh token expired)
          processQueue(new Error('Refresh failed'));
          logout();
        }
      } catch (err) {
        processQueue(err);
        logout();
      } finally {
        isRefreshing = false;
      }
    }

    return response;
  };
}
