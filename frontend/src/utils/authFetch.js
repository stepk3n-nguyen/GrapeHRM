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
    // 1. lấy accsess token hiện tại
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

    // 3. tạo initial request
    let response = await fetch(url, config);

    // 4. nếu 401 Unauthorized, xử lý token refresh
    if (response.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');

      // nếu không có refresh token, không thể làm gì khác ngoài logout
      if (!refreshToken) {
        logout();
        return response;
      }

      if (isRefreshing) {
        // nếu đã có refresh, chờ nó hoàn thành
        try {
          const newToken = await new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          });

          // retry request ban đầu với token mới
          config.headers['Authorization'] = `Bearer ${newToken}`;
          return await fetch(url, config);
        } catch (err) {
          // nếu refresh bị lỗi, trả về 401 response ban đầu
          return response;
        }
      }

      // bắt đầu quá trình refresh
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

          // lưu token mới
          localStorage.setItem('access_token', newAccessToken);
          setToken(newAccessToken);

          // xử lý queue trước khi retry request này, để các request khác cũng có thể proceed
          processQueue(null, newAccessToken);

          // retry request ban đầu với token mới
          config.headers['Authorization'] = `Bearer ${newAccessToken}`;
          response = await fetch(url, config);
        } else {
          // refresh failed (e.g. refresh token expired)
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
