import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Users, CalendarDays, Clock, Download, Loader2 } from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts';

const COLORS = ['#0A6ED1', '#17A2B8', '#28A745', '#E6A23C', '#DC3545', '#6F42C1', '#6C757D'];
const MONTHS = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'];

const Card = ({ title, children, height = 300 }) => (
  <div className="card card--no-hover">
    <div className="card__header"><h3 className="card__title">{title}</h3></div>
    <div className="card__body" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">{children}</ResponsiveContainer>
    </div>
  </div>
);

const ReportsPage = () => {
  const { getAuthHeaders } = useAuth();
  const [tab, setTab] = useState('employees');
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [loading, setLoading] = useState(true);
  const [emp, setEmp] = useState(null);
  const [leave, setLeave] = useState(null);
  const [att, setAtt] = useState(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [e, l, a] = await Promise.all([
        fetch(`/api/reports/employees?year=${year}`, { headers: getAuthHeaders() }),
        fetch(`/api/reports/leave?year=${year}`, { headers: getAuthHeaders() }),
        fetch(`/api/reports/attendance?year=${year}&month=${month}`, { headers: getAuthHeaders() }),
      ]);
      if (e.ok) setEmp(await e.json());
      if (l.ok) setLeave(await l.json());
      if (a.ok) setAtt(await a.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); /* eslint-disable-next-line */ }, [year, month]);

  const exportEmployees = async () => {
    const res = await fetch(`/api/reports/employees/export?year=${year}`, { headers: getAuthHeaders() });
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'employees.csv'; document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url);
    }
  };

  const genderData = emp ? [
    { name: 'Nam', value: emp.by_gender.male },
    { name: 'Nữ', value: emp.by_gender.female },
    { name: 'Khác', value: emp.by_gender.other },
  ] : [];

  const attSummary = att ? [
    { name: 'Có mặt', value: att.summary.present },
    { name: 'Vắng', value: att.summary.absent },
    { name: 'Đi muộn', value: att.summary.late },
    { name: 'Nghỉ phép', value: att.summary.on_leave },
  ] : [];

  return (
    <div className="fade-in">
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Báo cáo</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Báo cáo & Phân tích</h2>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {tab === 'attendance' && (
            <select className="input" value={month} onChange={e => setMonth(e.target.value)} style={{ width: '100px' }}>
              {MONTHS.map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
            </select>
          )}
          <select className="input" value={year} onChange={e => setYear(e.target.value)} style={{ width: '110px' }}>
            {[...Array(5).keys()].map(i => { const y = new Date().getFullYear() - 2 + i; return <option key={y} value={y}>Năm {y}</option>; })}
          </select>
        </div>
      </div>

      <div className="leave-tabs">
        <button className={`leave-tabs__tab ${tab === 'employees' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab('employees')}><Users size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Nhân sự</button>
        <button className={`leave-tabs__tab ${tab === 'leave' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab('leave')}><CalendarDays size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Nghỉ phép</button>
        <button className={`leave-tabs__tab ${tab === 'attendance' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab('attendance')}><Clock size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />Chấm công</button>
      </div>

      {loading ? (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div></div>
      ) : tab === 'employees' && emp ? (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <button className="btn btn--secondary" onClick={exportEmployees}><Download size={16} /> Xuất CSV</button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 20 }}>
            <Card title="Biến động nhân sự theo tháng">
              <LineChart data={emp.monthly_headcount.map(d => ({ ...d, m: MONTHS[d.month - 1] }))}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="m" /><YAxis allowDecimals={false} /><Tooltip /><Legend />
                <Line type="monotone" dataKey="active" name="Đang làm" stroke="#0A6ED1" strokeWidth={2} />
                <Line type="monotone" dataKey="new" name="Mới tuyển" stroke="#28A745" strokeWidth={2} />
              </LineChart>
            </Card>
            <Card title="Tỷ lệ giới tính">
              <PieChart>
                <Pie data={genderData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} label>
                  {genderData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Pie>
                <Tooltip /><Legend />
              </PieChart>
            </Card>
          </div>
          <Card title="Phân bổ theo phòng ban">
            <BarChart data={emp.by_department} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" allowDecimals={false} /><YAxis type="category" dataKey="name" width={120} /><Tooltip />
              <Bar dataKey="count" name="Số NV" fill="#17A2B8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </Card>
          <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: 12 }}>Thâm niên trung bình: <strong>{emp.avg_tenure_months} tháng</strong></p>
        </>
      ) : tab === 'leave' && leave ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <Card title="Ngày nghỉ theo tháng">
            <BarChart data={leave.by_month.map(d => ({ ...d, m: MONTHS[d.month - 1] }))}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="m" /><YAxis /><Tooltip />
              <Bar dataKey="total_days" name="Số ngày" fill="#0A6ED1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </Card>
          <Card title="Ngày nghỉ theo loại phép">
            <BarChart data={leave.by_type} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="type" width={120} /><Tooltip />
              <Bar dataKey="total_days" name="Số ngày" fill="#17A2B8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </Card>
          <Card title="Top 5 nhân viên nghỉ nhiều nhất">
            <BarChart data={leave.top_users} layout="vertical" margin={{ left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="name" width={120} /><Tooltip />
              <Bar dataKey="total_days" name="Số ngày" fill="#E6A23C" radius={[0, 4, 4, 0]} />
            </BarChart>
          </Card>
        </div>
      ) : tab === 'attendance' && att ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
          <Card title={`Tỷ lệ chấm công tháng ${month}/${year}`}>
            <PieChart>
              <Pie data={attSummary} dataKey="value" nameKey="name" outerRadius={90} label>
                {attSummary.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </Card>
          <Card title="Xu hướng chấm công theo ngày">
            <AreaChart data={att.daily_trend.map(d => ({ ...d, d: d.date.slice(8) }))}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="d" /><YAxis allowDecimals={false} /><Tooltip /><Legend />
              <Area type="monotone" dataKey="present" name="Có mặt" stroke="#28A745" fill="#28A74533" />
              <Area type="monotone" dataKey="late" name="Đi muộn" stroke="#E6A23C" fill="#E6A23C33" />
            </AreaChart>
          </Card>
        </div>
      ) : (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có dữ liệu.</div></div>
      )}
    </div>
  );
};

export default ReportsPage;
