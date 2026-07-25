import React, { createContext, useState, useEffect, useContext, useRef, useCallback } from 'react';
import { createAuthFetch } from '../utils/authFetch';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true);
  const [activeTenant, setActiveTenant] = useState(null); // {id, name, slug} for super admin context

  // Keep a stable ref to the current token for the authFetch wrapper
  const tokenRef = useRef(token);
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('active_tenant');
    setToken(null);
    setUser(null);
    setActiveTenant(null);
  }, []);

  const updateToken = useCallback((newToken) => {
    setToken(newToken);
  }, []);

  // Create the stable authFetch instance
  const authFetchRef = useRef(null);
  if (!authFetchRef.current) {
    authFetchRef.current = createAuthFetch(
      () => tokenRef.current,
      updateToken,
      logout
    );
  }

  const authFetch = useCallback((url, options) => {
    return authFetchRef.current(url, options);
  }, []);

  // Hàm khôi phục thông tin user từ JWT đang lưu
  const checkSession = async (accessToken) => {
    try {
      // Use authFetch here so it can auto-refresh if the token is already expired
      const response = await authFetch('/api/auth/me');

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token không hợp lệ hoặc hết hạn và refresh thất bại
        logout();
      }
    } catch (err) {
      console.error('Lỗi kiểm tra session:', err);
      // Lỗi mạng hoặc server, giữ nguyên trạng thái local tạm thời hoặc logout tùy ý
      logout();
    } finally {
      setLoading(false);
    }
  };

  // Đồng bộ token real-time giữa các tab
  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    if (savedToken) {
      setToken(savedToken);
      checkSession(savedToken);
    } else {
      setLoading(false);
    }

    // Lắng nghe sự thay đổi của localStorage từ các tab khác
    const handleStorageChange = (e) => {
      if (e.key === 'access_token') {
        const newToken = e.newValue;
        if (newToken) {
          // Có người đăng nhập ở tab khác (hoặc đổi tài khoản)
          setToken(newToken);
          checkSession(newToken);
        } else {
          // Tab khác đã đăng xuất
          setToken(null);
          setUser(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const login = async (username, password, tenantSlug) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password, tenant_slug: tenantSlug }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        setToken(data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        return { success: false, error: data.error || 'Sai thông tin đăng nhập' };
      }
    } catch (err) {
      console.error('Lỗi khi gửi yêu cầu login:', err);
      return { success: false, error: 'Không thể kết nối đến máy chủ. Vui lòng thử lại sau.' };
    }
  };

  const switchTenant = async (tenantId, tenantObj = null) => {
    try {
      const response = await authFetch('/api/auth/switch-tenant', {
        method: 'POST',
        body: JSON.stringify({ tenant_id: tenantId }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        setToken(data.access_token);
        
        setUser(prevUser => ({
          ...prevUser,
          tenant_id: data.tenant_id
        }));

        if (tenantObj) {
           setActiveTenant(tenantObj);
           localStorage.setItem('active_tenant', JSON.stringify(tenantObj));
        } else if (tenantId === null) {
           setActiveTenant(null);
           localStorage.removeItem('active_tenant');
        }

        return { success: true };
      } else {
        return { success: false, error: data.error || 'Đổi tổ chức thất bại' };
      }
    } catch (err) {
      console.error('Lỗi khi gửi yêu cầu switch-tenant:', err);
      return { success: false, error: 'Không thể kết nối đến máy chủ.' };
    }
  };

  // Khôi phục activeTenant từ localStorage khi reload
  useEffect(() => {
    if (user && user.role === 'super_admin' && user.tenant_id) {
       const saved = localStorage.getItem('active_tenant');
       if (saved) {
           setActiveTenant(JSON.parse(saved));
       }
    }
  }, [user]);

  // Trả về custom headers tiện dụng cho các request API tiếp theo (Deprecated)
  const getAuthHeaders = useCallback(() => {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, loading, activeTenant, setActiveTenant, login, logout, getAuthHeaders, authFetch, switchTenant }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth phải được sử dụng bên trong AuthProvider');
  }
  return context;
};
