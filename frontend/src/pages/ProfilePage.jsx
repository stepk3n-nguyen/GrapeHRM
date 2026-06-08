import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Phone, Mail, MapPin, Calendar, Briefcase, Award, Loader2 } from 'lucide-react';

const ProfilePage = () => {
  const { getAuthHeaders } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await fetch('/api/employees/me', {
          headers: getAuthHeaders()
        });
        if (res.ok) {
          const data = await res.json();
          setProfile(data);
        } else {
          setError('Không thể tải thông tin hồ sơ.');
        }
      } catch (err) {
        setError('Lỗi kết nối. Vui lòng thử lại sau.');
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [getAuthHeaders]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Loader2 className="animate-spin" size={40} style={{ color: 'var(--color-primary)' }} />
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--color-error)' }}>
        <h3>{error || 'Không tìm thấy hồ sơ cá nhân.'}</h3>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="breadcrumb">
        <span>GrapeHRM</span>
        <span>&gt;</span>
        <span className="breadcrumb__item">Thông tin cá nhân</span>
      </div>

      <div className="card" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div className="card__header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '24px', padding: '24px' }}>
          <div style={{
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-primary-light)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-primary)',
            overflow: 'hidden'
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
              display: 'inline-block',
              marginTop: '8px',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: 500,
              backgroundColor: profile.state === 'ACTIVE' ? 'rgba(23, 162, 184, 0.1)' : 'rgba(108, 117, 125, 0.1)',
              color: profile.state === 'ACTIVE' ? 'var(--color-accent)' : 'var(--color-text-muted)'
            }}>
              {profile.state === 'ACTIVE' ? 'Đang làm việc' : 'Đã nghỉ việc'}
            </span>
          </div>
        </div>

        <div className="card__body" style={{ padding: '0 24px 24px 24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: 600, borderBottom: '1px solid var(--color-border)', marginBottom: '16px' }}>
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Briefcase size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Mã nhân viên</div>
                <div style={{ fontWeight: 500 }}>{profile.employee_id}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Mail size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Email công việc</div>
                <div style={{ fontWeight: 500 }}>{profile.work_email || 'Chưa cập nhật'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Phone size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Số điện thoại</div>
                <div style={{ fontWeight: 500 }}>{profile.mobile || 'Chưa cập nhật'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <User size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Giới tính</div>
                <div style={{ fontWeight: 500 }}>{profile.gender === 1 ? 'Nam' : profile.gender === 2 ? 'Nữ' : 'Khác'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Award size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Tình trạng hôn nhân</div>
                <div style={{ fontWeight: 500 }}>{profile.marital_status === 'Single' ? 'Độc thân' : 'Đã kết hôn'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Calendar size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Ngày sinh</div>
                <div style={{ fontWeight: 500 }}>{profile.birthday ? new Date(profile.birthday).toLocaleDateString('vi-VN') : 'Chưa cập nhật'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <Calendar size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Ngày gia nhập</div>
                <div style={{ fontWeight: 500 }}>{profile.joined_date ? new Date(profile.joined_date).toLocaleDateString('vi-VN') : 'Chưa cập nhật'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
              <MapPin size={20} style={{ color: 'var(--color-text-muted)', marginTop: '2px' }} />
              <div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Địa chỉ</div>
                <div style={{ fontWeight: 500 }}>{profile.address || 'Chưa cập nhật'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
