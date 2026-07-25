import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Save, Send, CheckCircle, Loader2 } from 'lucide-react';

const EmailSettingsPage = () => {
  const { authFetch, user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [toasts, setToasts] = useState([]);
  
  const [form, setForm] = useState({
    MAIL_SERVER: '',
    MAIL_PORT: '',
    MAIL_USE_TLS: true,
    MAIL_USERNAME: '',
    MAIL_PASSWORD: '',
    MAIL_DEFAULT_SENDER: ''
  });
  const [isPasswordSet, setIsPasswordSet] = useState(false);
  const [testEmail, setTestEmail] = useState('');

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  };

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/admin/smtp-config');
      if (res.ok) {
        const result = await res.json();
        const data = result.data || {};
        setForm({
          MAIL_SERVER: data.MAIL_SERVER || '',
          MAIL_PORT: data.MAIL_PORT || '',
          MAIL_USE_TLS: data.MAIL_USE_TLS ?? true,
          MAIL_USERNAME: data.MAIL_USERNAME || '',
          MAIL_PASSWORD: '', // Trống để người dùng tự nhập nếu muốn đổi
          MAIL_DEFAULT_SENDER: data.MAIL_DEFAULT_SENDER || ''
        });
        setIsPasswordSet(data.MAIL_PASSWORD_SET);
      } else {
        const d = await res.json();
        showToast(d.error || 'Không thể tải cấu hình', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      fetchConfig();
    }
  }, [isAdmin]);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authFetch('/api/admin/smtp-config', {
        method: 'PUT',
        body: JSON.stringify(form)
      });
      if (res.ok) {
        showToast('Lưu cấu hình SMTP thành công');
        fetchConfig(); // Reload
      } else {
        const d = await res.json();
        showToast(d.error || 'Lỗi lưu cấu hình', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleTestEmail = async (e) => {
    e.preventDefault();
    if (!testEmail) {
      return showToast('Vui lòng nhập email để gửi thư thử nghiệm', 'error');
    }
    setTesting(true);
    try {
      const res = await authFetch('/api/admin/smtp-test', {
        method: 'POST',
        body: JSON.stringify({ email: testEmail })
      });
      if (res.ok) {
        showToast('Email test đã được xếp hàng gửi! Vui lòng kiểm tra hòm thư.', 'success');
      } else {
        const d = await res.json();
        showToast(d.error || 'Lỗi gửi email', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    } finally {
      setTesting(false);
    }
  };

  if (!isAdmin) {
    return <div style={{ padding: '24px' }}>Bạn không có quyền truy cập trang này.</div>;
  }

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast toast--${t.type}`}>
            <CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} />
            <span>{t.message}</span>
          </div>
        ))}
      </div>

      <div className="breadcrumb">
        <span>GrapeHRM</span>
        <span>&gt;</span>
        <span className="breadcrumb__item">Cấu hình Hệ thống</span>
        <span>&gt;</span>
        <span className="breadcrumb__item">Cấu hình Email (SMTP)</span>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Cấu hình Email SMTP</h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Quản lý máy chủ gửi email để thông báo nghỉ phép, chấm công, bảng lương.
        </p>
      </div>

      {loading && !form.MAIL_SERVER ? (
        <div style={{ textAlign: 'center', padding: '40px' }}><Loader2 className="animate-spin" /></div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', alignItems: 'start' }}>
          <div className="card card--no-hover">
            <div className="card__header">
              <h3 className="card__title">Thông số máy chủ SMTP</h3>
            </div>
            <div className="card__body">
              <form onSubmit={handleSave}>
                <div className="form-group">
                  <label className="form-label form-label--required">SMTP Server</label>
                  <input type="text" className="input" placeholder="smtp.gmail.com" value={form.MAIL_SERVER} onChange={e => setForm({...form, MAIL_SERVER: e.target.value})} required />
                </div>
                
                <div style={{ display: 'flex', gap: '16px' }}>
                  <div className="form-group" style={{ flex: 1 }}>
                    <label className="form-label form-label--required">Port</label>
                    <input type="number" className="input" placeholder="587" value={form.MAIL_PORT} onChange={e => setForm({...form, MAIL_PORT: e.target.value})} required />
                  </div>
                  <div className="form-group" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <label className="form-label">Sử dụng TLS</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
                      <input type="checkbox" id="use_tls" checked={form.MAIL_USE_TLS} onChange={e => setForm({...form, MAIL_USE_TLS: e.target.checked})} />
                      <label htmlFor="use_tls">Có</label>
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label form-label--required">Tên đăng nhập (Email)</label>
                  <input type="text" className="input" placeholder="your-email@gmail.com" value={form.MAIL_USERNAME} onChange={e => setForm({...form, MAIL_USERNAME: e.target.value})} required />
                </div>

                <div className="form-group">
                  <label className="form-label">Mật khẩu (App Password)</label>
                  <input type="password" className="input" placeholder={isPasswordSet ? "******** (Đã thiết lập)" : "Nhập mật khẩu..."} value={form.MAIL_PASSWORD} onChange={e => setForm({...form, MAIL_PASSWORD: e.target.value})} />
                  {isPasswordSet && <small style={{ color: 'var(--color-text-muted)' }}>Để trống nếu bạn không muốn thay đổi mật khẩu hiện tại.</small>}
                </div>

                <div className="form-group">
                  <label className="form-label form-label--required">Tên người gửi mặc định</label>
                  <input type="text" className="input" placeholder="GrapeHRM <noreply@grapehrm.com>" value={form.MAIL_DEFAULT_SENDER} onChange={e => setForm({...form, MAIL_DEFAULT_SENDER: e.target.value})} required />
                </div>

                <div style={{ marginTop: '24px', textAlign: 'right' }}>
                  <button type="submit" className="btn btn--primary" disabled={loading}>
                    {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                    Lưu cấu hình
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div className="card card--no-hover">
            <div className="card__header">
              <h3 className="card__title">Gửi thư kiểm tra (Test Email)</h3>
            </div>
            <div className="card__body">
              <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginBottom: '16px' }}>
                Sau khi lưu cấu hình, bạn có thể gửi một email kiểm tra để xác nhận xem máy chủ SMTP đã hoạt động chính xác hay chưa.
              </p>
              <form onSubmit={handleTestEmail}>
                <div className="form-group">
                  <label className="form-label form-label--required">Email người nhận</label>
                  <input type="email" className="input" placeholder="admin@example.com" value={testEmail} onChange={e => setTestEmail(e.target.value)} required />
                </div>
                <div style={{ textAlign: 'right' }}>
                  <button type="submit" className="btn btn--secondary" disabled={testing}>
                    {testing ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                    Gửi thư kiểm tra
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailSettingsPage;
