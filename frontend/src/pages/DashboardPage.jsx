import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Users, UserCheck, CalendarRange, Landmark, HelpCircle, ArrowRight } from 'lucide-react';

const DashboardPage = () => {
  const { user, getAuthHeaders } = useAuth();
  const [employeeCount, setEmployeeCount] = useState('...');

  useEffect(() => {
    const fetchEmployeeCount = async () => {
      try {
        const response = await fetch('/api/employees', {
          method: 'GET',
          headers: getAuthHeaders(),
        });
        if (response.ok) {
          const data = await response.json();
          setEmployeeCount(String(data.length));
        } else {
          setEmployeeCount('N/A');
        }
      } catch (err) {
        console.error('Fetch employee count error:', err);
        setEmployeeCount('N/A');
      }
    };

    fetchEmployeeCount();
  }, []);

  const widgets = [
    { label: 'Tổng nhân viên', value: employeeCount, icon: Users, variant: 'primary' },
    { label: 'Đang tuyển dụng', value: '4', icon: UserCheck, variant: 'accent' },
    { label: 'Yêu cầu nghỉ phép', value: '3', icon: CalendarRange, variant: 'success' },
  ];

  return (
    <div className="fade-in">
      <div className="breadcrumb">
        <span>GrapeHRM</span>
        <span>&gt;</span>
        <span className="breadcrumb__item">Dashboard</span>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>
          Xin chào, {user ? user.username : 'HR Manager'}!
        </h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', marginTop: '4px' }}>
          Hôm nay là một ngày tuyệt vời để quản lý nguồn lực doanh nghiệp của bạn.
        </p>
      </div>

      {/* Grid widgets thống kê */}
      <div className="dashboard-grid">
        {widgets.map((widget, idx) => {
          const Icon = widget.icon;
          return (
            <div className="widget" key={idx}>
              <div className="widget__info">
                <span className="widget__label">{widget.label}</span>
                <span className="widget__value">{widget.value}</span>
              </div>
              <div className={`widget__icon-wrapper widget__icon-wrapper--${widget.variant}`}>
                <Icon size={24} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Grid 2 cột cho các hoạt động chính */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        
        {/* Cột trái: Quy trình tổng quan HRM */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <Landmark size={18} />
              <span>Quy trình Nhân sự HRM</span>
            </h3>
          </div>
          <div className="card__body">
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: '16px', fontSize: '13px' }}>
              Chuỗi quy trình HRM tích hợp từ Tuyển dụng đến Nghỉ hưu trong GrapeHRM được thiết lập tự động hóa:
            </p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { step: '01', title: 'Tuyển dụng', desc: 'Đăng tuyển vị trí & Thu hút CV ứng viên.' },
                { step: '02', title: 'Onboarding', desc: 'Thiết lập hồ sơ cá nhân & Cấp tài khoản mới.' },
                { step: '03', title: 'Quản lý nhân viên', desc: 'Hồ sơ nhân sự, hợp đồng lao động & thông tin liên hệ.' },
                { step: '04', title: 'Time & Leave', desc: 'Phê duyệt ngày nghỉ, ngày phép & theo dõi chuyên cần.' },
                { step: '05', title: 'Tính lương & Đánh giá', desc: 'Lập bảng lương tự động & theo dõi mục tiêu KPI.' }
              ].map((item, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '14px', borderBottom: '1px solid var(--color-border-light)', paddingBottom: '10px' }}>
                  <div style={{ 
                    backgroundColor: 'var(--color-primary-light)', 
                    color: 'var(--color-primary)', 
                    fontWeight: 700, 
                    width: '32px', 
                    height: '32px', 
                    borderRadius: '50%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    fontSize: '12px',
                    flexShrink: 0
                  }}>
                    {item.step}
                  </div>
                  <div>
                    <h4 style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-primary)' }}>{item.title}</h4>
                    <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Cột phải: Tin tức nội bộ / Phím tắt nhanh */}
        <div className="card">
          <div className="card__header">
            <h3 className="card__title">
              <HelpCircle size={18} />
              <span>Lối tắt & Tiện ích nhanh</span>
            </h3>
          </div>
          <div className="card__body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ padding: '16px', backgroundColor: 'var(--color-secondary-light)', borderRadius: 'var(--radius-md)', borderLeft: '4px solid var(--color-accent)' }}>
                <h4 style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                  Bảo mật Multi-Tenant hoạt động
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  Mọi dữ liệu bạn thao tác trên GrapeHRM đều được mã hóa và cô lập hoàn toàn dưới mã định danh tổ chức riêng của bạn. Đảm bảo an toàn 100%.
                </p>
              </div>

              <div style={{ padding: '16px', backgroundColor: '#F4FAF5', borderRadius: 'var(--radius-md)', borderLeft: '4px solid var(--color-success)' }}>
                <h4 style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
                  Mẹo quản lý nhân sự
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  Hãy cập nhật đầy đủ Ngày vào làm (Joined Date) của nhân viên mới để hệ thống tự động tính lũy kế ngày phép hàng tháng một cách chuẩn xác nhất.
                </p>
              </div>

              <div style={{ marginTop: '8px' }}>
                <h4 style={{ fontWeight: 600, fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: '10px' }}>Hành động gợi ý:</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  <button className="btn btn--secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                    <span>Cấu hình Tenant</span>
                    <ArrowRight size={12} />
                  </button>
                  <button className="btn btn--secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                    <span>Xuất báo cáo PDF</span>
                    <ArrowRight size={12} />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default DashboardPage;
