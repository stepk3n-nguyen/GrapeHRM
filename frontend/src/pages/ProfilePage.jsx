import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  User, Phone, Mail, MapPin, Calendar, Briefcase, Award, Loader2,
  Lock, Eye, EyeOff, KeyRound, CheckCircle, ShieldAlert, Edit, X
} from 'lucide-react';

const ProfilePage = () => {
  const { authFetch } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // ── Đổi mật khẩu ──────────────────────────────────────────────
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [showPw, setShowPw] = useState({ current: false, next: false, confirm: false });
  const [pwLoading, setPwLoading] = useState(false);

  // ── Chỉnh sửa hồ sơ ───────────────────────────────────────────
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    first_name: '',
    last_name: '',
    gender: '1',
    marital_status: 'Single',
    birthday: '',
    mobile: '',
    address: '',
    profile_pic_url: ''
  });
  const [editLoading, setEditLoading] = useState(false);

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  };

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

  useEffect(() => {
    fetchProfile();
  }, [authFetch]);

  // Vô hiệu hóa cuộn trang của body khi Modal đang mở
  useEffect(() => {
    if (isEditModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isEditModalOpen]);

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

  const handleOpenEditModal = () => {
    if (!profile) return;
    setEditForm({
      first_name: profile.first_name || '',
      last_name: profile.last_name || '',
      gender: profile.gender !== null ? String(profile.gender) : '1',
      marital_status: profile.marital_status || 'Single',
      birthday: profile.birthday ? profile.birthday.split('T')[0] : '',
      mobile: profile.mobile || '',
      address: profile.address || '',
      profile_pic_url: profile.profile_pic_url || '',
      num_dependents: profile.num_dependents || 0
    });
    setIsEditModalOpen(true);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!editForm.first_name.trim() || !editForm.last_name.trim()) {
      showToast('Họ và Tên là bắt buộc.', 'error');
      return;
    }

    setEditLoading(true);
    try {
      const res = await authFetch(`/api/employees/${profile.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          ...editForm,
          gender: parseInt(editForm.gender)
        }),
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Cập nhật hồ sơ thành công.');
        setIsEditModalOpen(false);
        fetchProfile(); // Tải lại thông tin mới
      } else {
        showToast(data.error || 'Cập nhật thất bại.', 'error');
      }
    } catch (err) {
      showToast('Lỗi kết nối. Vui lòng thử lại.', 'error');
    } finally {
      setEditLoading(false);
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
          <div className="card__header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
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
            
            <button className="btn btn--secondary" onClick={handleOpenEditModal}>
              <Edit size={16} />
              <span>Chỉnh sửa</span>
            </button>
          </div>

          <div className="card__body" style={{ padding: '0 24px 24px 24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
              <InfoRow icon={Briefcase} label="Mã nhân viên" value={profile.employee_id} />
              <InfoRow icon={Mail} label="Email công việc" value={profile.work_email || 'Chưa cập nhật'} />
              <InfoRow icon={Phone} label="Số điện thoại" value={profile.mobile || 'Chưa cập nhật'} />
              <InfoRow icon={User} label="Giới tính" value={profile.gender === 1 ? 'Nam' : profile.gender === 2 ? 'Nữ' : 'Khác'} />
              <InfoRow icon={Award} label="Tình trạng hôn nhân" value={profile.marital_status === 'Single' ? 'Độc thân' : profile.marital_status === 'Married' ? 'Đã kết hôn' : profile.marital_status === 'Divorced' ? 'Đã ly hôn' : 'Chưa cập nhật'} />
              <InfoRow icon={Award} label="Số người phụ thuộc" value={profile.num_dependents || 0} />
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

      {/* Modal Chỉnh sửa hồ sơ */}
      {isEditModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '600px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Cập nhật thông tin cá nhân</h3>
              <button className="modal__close" type="button" onClick={() => setIsEditModalOpen(false)}>&times;</button>
            </div>
            
            <form onSubmit={handleSaveProfile}>
              <div className="modal__body" style={{ maxHeight: '75vh', overflowY: 'auto' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required">Họ & Tên đệm</label>
                    <input 
                      type="text" 
                      className="input" 
                      value={editForm.first_name}
                      onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required">Tên chính</label>
                    <input 
                      type="text" 
                      className="input" 
                      value={editForm.last_name}
                      onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required">Giới tính</label>
                    <select 
                      className="input" 
                      value={editForm.gender}
                      onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                      required
                    >
                      <option value="1">Nam</option>
                      <option value="2">Nữ</option>
                      <option value="3">Khác</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Tình trạng hôn nhân</label>
                    <select 
                      className="input" 
                      value={editForm.marital_status}
                      onChange={(e) => setEditForm({ ...editForm, marital_status: e.target.value })}
                    >
                      <option value="Single">Độc thân</option>
                      <option value="Married">Đã kết hôn</option>
                      <option value="Divorced">Đã ly hôn</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Số người phụ thuộc</label>
                    <input 
                      type="number" 
                      min="0"
                      className="input" 
                      value={editForm.num_dependents}
                      onChange={(e) => setEditForm({ ...editForm, num_dependents: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Ngày sinh</label>
                    <input 
                      type="date" 
                      className="input" 
                      value={editForm.birthday}
                      onChange={(e) => setEditForm({ ...editForm, birthday: e.target.value })}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Số điện thoại</label>
                    <input 
                      type="tel" 
                      className="input" 
                      value={editForm.mobile}
                      onChange={(e) => setEditForm({ ...editForm, mobile: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label className="form-label">Địa chỉ</label>
                  <input 
                    type="text" 
                    className="input" 
                    value={editForm.address}
                    onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                    placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành phố"
                  />
                </div>

                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label className="form-label" htmlFor="profile_pic_file">Ảnh đại diện</label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ 
                      width: '42px', height: '42px', borderRadius: '50%', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', fontWeight: '700', fontSize: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', border: '2px solid var(--color-border-light)', flexShrink: 0
                    }}>
                      {editForm.profile_pic_url ? (
                        <img src={editForm.profile_pic_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : (
                        editForm.first_name && editForm.last_name ? `${editForm.first_name[0]}${editForm.last_name[0]}` : '?'
                      )}
                    </div>
                    <div style={{ flex: 1 }}>
                      <input 
                        type="file" 
                        id="profile_pic_file" 
                        accept="image/*"
                        className="input" 
                        onChange={(e) => {
                          const file = e.target.files[0];
                          if (file) {
                            if (file.size > 2 * 1024 * 1024) {
                              showToast('Kích thước ảnh đại diện không được vượt quá 2MB.', 'error');
                              e.target.value = '';
                            } else {
                              const reader = new FileReader();
                              reader.onload = (e) => {
                                setEditForm({ ...editForm, profile_pic_url: e.target.result });
                              };
                              reader.readAsDataURL(file);
                            }
                          }
                        }}
                      />
                      <small style={{ color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
                        Hỗ trợ định dạng ảnh (.jpg, .png...). Kích thước tối đa 2MB.
                      </small>
                    </div>
                  </div>
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsEditModalOpen(false)}>Hủy</button>
                <button type="submit" className="btn btn--primary" disabled={editLoading}>
                  {editLoading ? <Loader2 size={16} className="animate-spin" /> : 'Lưu thay đổi'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
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
