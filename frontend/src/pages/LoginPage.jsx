import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Lock, User, AlertCircle, Loader2 } from 'lucide-react';
import logoFull from '../assets/img/logo-full.svg';

const LoginPage = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const trimmedUsername = username.trim();
    if (!trimmedUsername || !password) {
      setError('Vui lòng nhập tên tài khoản và mật khẩu.');
      return;
    }

    setLoading(true);
    const result = await login(trimmedUsername, password);
    setLoading(false);

    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__brand">
          <img 
            src={logoFull} 
            alt="GrapeHRM Logo" 
            style={{ height: '48px', marginBottom: '8px' }} 
            onError={(e) => {
              // Fallback if svg fails to load
              e.target.style.display = 'none';
              e.target.nextSibling.style.display = 'block';
            }}
          />
          <div style={{ display: 'none' }}>
            <h2 className="login-card__title">GrapeHRM</h2>
          </div>
          <p className="login-card__subtitle">Quản trị nhân sự thế hệ mới</p>
        </div>

        {error && (
          <div className="alert alert--error" role="alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="username">Tên tài khoản</label>
            <div style={{ position: 'relative' }}>
              <User 
                size={16} 
                style={{ 
                  position: 'absolute', 
                  left: '12px', 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: 'var(--color-text-muted)' 
                }} 
              />
              <input
                id="username"
                type="text"
                className="input"
                placeholder="Nhập username (ví dụ: admin)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{ paddingLeft: '38px' }}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '24px' }}>
            <label className="form-label" htmlFor="password">Mật khẩu</label>
            <div style={{ position: 'relative' }}>
              <Lock 
                size={16} 
                style={{ 
                  position: 'absolute', 
                  left: '12px', 
                  top: '50%', 
                  transform: 'translateY(-50%)',
                  color: 'var(--color-text-muted)' 
                }} 
              />
              <input
                id="password"
                type="password"
                className="input"
                placeholder="Nhập mật khẩu (ví dụ: admin123)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: '38px' }}
                disabled={loading}
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="btn btn--primary" 
            style={{ width: '100%', padding: '12px', fontSize: '14px' }}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" style={{ marginRight: '8px' }} />
                <span>Đang đăng nhập...</span>
              </>
            ) : (
              <span>Đăng nhập</span>
            )}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '12px', color: 'var(--color-text-muted)' }}>
          <p>Tài khoản mẫu: <strong>admin</strong> / <strong>admin123</strong></p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
