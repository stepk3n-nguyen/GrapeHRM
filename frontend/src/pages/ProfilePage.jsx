import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  User, Phone, Mail, MapPin, Calendar, Briefcase, Award, Loader2,
  Lock, Eye, EyeOff, KeyRound, CheckCircle, ShieldAlert
} from 'lucide-react';

const ProfilePage = () => {
  const { authFetch } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // ── Đổi mật khẩu ──────────────────────────────────────────────
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [showPw, setShowPw] = useState({ current: false, next: false, confirm: false });
  const [pwLoading, setPwLoading] = useState(false);

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  };

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await authFetch('/api/employees/me');
        if (res.ok) setProfile(await res.json());
        else setProfile(null);
      } catch (err) {
        setProfile(null);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, [authFetch]);

  // Đánh giá độ mạnh mật khẩu mới theo cùng quy tắc với backend
  const pwScore = (() => {
    const p = pwForm.new_password;
    let s = 0;
    if (p.length >= 8) s++;
    if (/[A-Z]/.test(p)) s++;
    if (/[a-z]/.test(p)) s++;
    if (/[0-9]/.test(p)) s++;
    return s;
  })();
  const strengthLabel = pwScore <= 1 ? 'Yếu' : pwScore <= 3 ? 'Trung bình' : 'Mạnh';
  const strengthColor = pwScore <= 1 ? 'var(--color-error)' : pwScore <= 3 ? 'var(--color-warning, #E6A23C)' : 'var(--color-success)';

  const handleChangePassword = async (e) => {
    e.preventDefault();
    const { current_password, new_password, confirm_password } = pwForm;

    if (!current_password || !new_password || !confirm_password) {
      showToast('Vui lòng nhập đầy đủ các trường mật khẩu.', 'error');
      return;
    }
    if (new_password !== confirm_password) {
      showToast('Mật khẩu xác nhận không khớp.', 'error');
      return;
    }
    if (pwScore < 4) {
      showToast('Mật khẩu mới phải ≥ 8 ký tự, có chữ hoa, chữ thường và số.', 'error');
      return;
    }
    if (current_password === new_password) {
      showToast('Mật khẩu mới không được trùng mật khẩu cũ.', 'error');
      return;
    }

    setPwLoading(true);
    try {
      const res = await authFetch('/api/auth/change-password', {
        method: 'PUT',
        body: JSON.stringify(pwForm),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || 'Đổi mật khẩu thành công.');
        setPwForm({ current_password: '', new_password: '', confirm_password: '' });
      } else {
        showToast(data.error || 'Đổi mật khẩu thất bại.', 'error');
      }
    } catch (err) {
      showToast('Lỗi kết nối. Vui lòng thử lại.', 'error');
    } finally {
      setPwLoading(false);
    }
  };

  const pwField = (key, label, toggleKey) => (
    <div className="form-group">
      <label className="form-label form-label--required">{label}</label>
      <div style={{ position: 'relative' }}>
        <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
        <input
          type={showPw[toggleKey] ? 'text' : 'password'}
          className="input"
          value={pwForm[key]}
          onChange={(e) => setPwForm({ ...pwForm, [key]: e.target.value })}
          style={{ paddingLeft: '38px', paddingRight: '38px' }}
          autoComplete={key === 'current_password' ? 'current-password' : 'new-password'}
        />
        <button
          type="button"
          onClick={() => setShowPw({ ...showPw, [toggleKey]: !showPw[toggleKey] })}
          style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', display: 'flex' }}
          tabIndex={-1}
        >
          {showPw[toggleKey] ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} style={{ color: 'var(--color-primary)' }} />
      </div>
    );
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
        <span className="breadcrumb__item">Thông tin cá nhân</span>
      </div>

      {profile ? (
        <div className="card card--no-hover" style={{ maxWidth: '800px', margin: '0 auto 24px auto' }}>
          <div className="card__header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '24px', padding: '24px' }}>
            <div style={{
              width: '80px', height: '80px', borderRadius: '50%',
              backgroundColor: 'var(--color-primary-light)', display: 'flex',
              alignItems: 'center', justifyContent: 'center', color: 'var(--color-primary)', overflow: 'hidden'
            }}>
              {profile.profile_pic_url ? (
                <img src={profile.profile_pic_url} alt={profile.full_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : (
                <User size={40} />
              )}
            </div>
            <div>
              <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-text-primary)' }}>{profile.full_name}</h2>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '15px' }}>{profile.title_name || 'Chưa có chức danh'} • {profile.department_name || 'Chưa có phòng ban'}</p>
              <span style={{
                display: 'inline-block', marginTop: '8px', padding: '4px 12px', borderRadius: '20px',
                fontSize: '12px', fontWeight: 500,
                backgroundColor: profile.state === 'ACTIVE' ? 'rgba(23, 162, 184, 0.1)' : 'rgba(108, 117, 125, 0.1)',
                color: profile.state === 'ACTIVE' ? 'var(--color-accent)' : 'var(--color-text-muted)'
              }}>
                {profile.state === 'ACTIVE' ? 'Đang làm việc' : 'Đã nghỉ việc'}
              </span>
            </div>
          </div>

          <div className="card__body" style={{ padding: '0 24px 24px 24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
              <InfoRow icon={Briefcase} label="Mã nhân viên" value={profile.employee_id} />
              <InfoRow icon={Mail} label="Email công việc" value={profile.work_email || 'Chưa cập nhật'} />
              <InfoRow icon={Phone} label="Số điện thoại" value={profile.mobile || 'Chưa cập nhật'} />
              <InfoRow icon={User} label="Giới tính" value={profile.gender === 1 ? 'Nam' : profile.gender === 2 ? 'Nữ' : 'Khác'} />
              <InfoRow icon={Award} label="Tình trạng hôn nhân" value={profile.marital_status === 'Single' ? 'Độc thân' : 'Đã kết hôn'} />
              <InfoRow icon={Calendar} label="Ngày sinh" value={profile.birthday ? new Date(profile.birthday).toLocaleDateString('vi-VN') : 'Chưa cập nhật'} />
              <InfoRow icon={Calendar} label="Ngày gia nhập" value={profile.joined_date ? new Date(profile.joined_date).toLocaleDateString('vi-VN') : 'Chưa cập nhật'} />
              <InfoRow icon={MapPin} label="Địa chỉ" value={profile.address || 'Chưa cập nhật'} />
            </div>
          </div>
        </div>
      ) : (
        <div className="card card--no-hover" style={{ maxWidth: '800px', margin: '0 auto 24px auto' }}>
          <div className="card__body" style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-text-muted)' }}>
            <ShieldAlert size={20} />
            <span>Tài khoản này chưa được liên kết với hồ sơ nhân viên. Bạn vẫn có thể đổi mật khẩu bên dưới.</span>
          </div>
        </div>
      )}

      {/* ── Đổi mật khẩu ─────────────────────────────────────────── */}
      <div className="card card--no-hover" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div className="card__header">
          <h3 className="card__title"><KeyRound size={18} /><span>Đổi mật khẩu</span></h3>
        </div>
        <div className="card__body">
          <form onSubmit={handleChangePassword} style={{ maxWidth: '420px' }}>
            {pwField('current_password', 'Mật khẩu hiện tại', 'current')}
            {pwField('new_password', 'Mật khẩu mới', 'next')}

            {pwForm.new_password && (
              <div style={{ marginTop: '-8px', marginBottom: '16px' }}>
                <div style={{ height: '6px', borderRadius: '3px', background: 'var(--color-border)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${(pwScore / 4) * 100}%`, background: strengthColor, transition: 'width .2s' }} />
                </div>
                <small style={{ color: strengthColor, fontWeight: 600 }}>Độ mạnh: {strengthLabel}</small>
              </div>
            )}

            {pwField('confirm_password', 'Nhập lại mật khẩu mới', 'confirm')}

            <div style={{ marginTop: '8px' }}>
              <button type="submit" className="btn btn--primary" disabled={pwLoading}>
                {pwLoading ? <><Loader2 size={16} className="animate-spin" style={{ marginRight: '8px' }} /> Đang xử lý...</> : 'Đổi mật khẩu'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

const InfoRow = ({ icon: Icon, label, value }) => (
  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
    <Icon size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
    <div>
      <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{label}</div>
      <div style={{ fontWeight: 500 }}>{value}</div>
    </div>
  </div>
);

export default ProfilePage;
