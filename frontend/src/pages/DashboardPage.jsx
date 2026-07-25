import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Users, UserCheck, UserX, CalendarRange, Activity, AlarmClock,
  ArrowRight, BarChart3, CalendarCheck2,
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';

// Dashboard xoay quanh CHẤM CÔNG: hôm nay ai đi làm / muộn / nghỉ / vắng
// và tổng công tháng hiện tại (tính động từ dữ liệu chấm công).
const DashboardPage = () => {
  const { user, authFetch } = useAuth();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await authFetch('/api/reports/dashboard-stats');
        if (res.ok) setStats(await res.json());
      } catch (err) { console.error(err); }
    };
    fetchStats();
  }, []);

  const today = stats?.today || {};
  const month = stats?.month || {};
  const v = (n) => (stats ? String(n ?? 0) : '...');

  // Hàng 1 — HÔM NAY (nguồn: chấm công)
  const todayWidgets = [
    { label: 'Đi làm hôm nay', value: v(today.present), icon: UserCheck, variant: 'success' },
    { label: 'Đi muộn hôm nay', value: v(today.late), icon: AlarmClock, variant: 'primary' },
    { label: 'Nghỉ phép hôm nay', value: v(today.on_leave), icon: CalendarRange, variant: 'accent' },
    { label: today.is_working_day === false ? 'Hôm nay nghỉ' : 'Vắng / chưa chấm', value: v(today.absent), icon: UserX, variant: 'primary' },
  ];

  // Hàng 2 — nhân sự & tháng này
  const monthWidgets = [
    { label: 'Nhân viên đang làm', value: v(stats?.active_employees), icon: Users, variant: 'primary' },
    { label: `Tổng công T${month.month || ''}`, value: stats ? `${month.total_workdays ?? 0}` : '...', icon: CalendarCheck2, variant: 'success' },
    { label: 'Đơn phép chờ duyệt', value: v(stats?.pending_leave_requests), icon: CalendarRange, variant: 'accent' },
    { label: 'Giờ OT tháng này', value: stats ? `${month.ot_hours ?? 0}h` : '...', icon: Activity, variant: 'primary' },
  ];

  const rate = today.attendance_rate || 0;
  const rateData = [{ name: 'Đi làm', value: rate }, { name: 'Còn lại', value: Math.max(100 - rate, 0) }];

  return (
    <div className="fade-in">
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Dashboard</span></div>

      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Xin chào, {user ? (user.employee_full_name || user.username) : 'HR Manager'}!</h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', marginTop: '4px' }}>
          Tình hình chấm công hôm nay {today.date ? `(${new Date(today.date).toLocaleDateString('vi-VN')})` : ''} và tổng công tháng hiện tại.
        </p>
      </div>

      <div className="dashboard-grid">
        {todayWidgets.map((w, idx) => {
          const Icon = w.icon;
          return (
            <div className="widget" key={idx}>
              <div className="widget__info">
                <span className="widget__label">{w.label}</span>
                <span className="widget__value">{w.value}</span>
              </div>
              <div className={`widget__icon-wrapper widget__icon-wrapper--${w.variant}`}><Icon size={24} /></div>
            </div>
          );
        })}
      </div>

      <div className="dashboard-grid" style={{ marginTop: '16px' }}>
        {monthWidgets.map((w, idx) => {
          const Icon = w.icon;
          return (
            <div className="widget" key={idx}>
              <div className="widget__info">
                <span className="widget__label">{w.label}</span>
                <span className="widget__value">{w.value}</span>
              </div>
              <div className={`widget__icon-wrapper widget__icon-wrapper--${w.variant}`}><Icon size={24} /></div>
            </div>
          );
        })}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px', marginTop: '24px' }}>
        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title"><BarChart3 size={18} /><span>Nhân sự theo phòng ban</span></h3>
            <Link to="/reports" className="btn btn--secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>Xem báo cáo <ArrowRight size={12} /></Link>
          </div>
          <div className="card__body" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats?.departments_summary || []} layout="vertical" margin={{ left: 30 }}>
                <XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="name" width={110} /><Tooltip />
                <Bar dataKey="count" name="Số NV" fill="#0A6ED1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title"><Activity size={18} /><span>Tỷ lệ đi làm hôm nay</span></h3>
            <Link to="/attendance" className="btn btn--secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>Bảng chấm công <ArrowRight size={12} /></Link>
          </div>
          <div className="card__body" style={{ height: 260, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={rateData} dataKey="value" innerRadius={60} outerRadius={85} startAngle={90} endAngle={-270}>
                  <Cell fill="#28A745" /><Cell fill="#E9ECEF" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ marginTop: '-150px', textAlign: 'center', pointerEvents: 'none' }}>
              <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--color-success)' }}>{rate}%</div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                {today.present ?? 0}/{today.total_active_employees ?? 0} nhân viên
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
