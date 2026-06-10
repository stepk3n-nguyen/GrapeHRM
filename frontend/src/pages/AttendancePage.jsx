import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Download, Plus, Search, Loader2, CheckCircle, AlertTriangle } from 'lucide-react';

const AttendancePage = () => {
  const { user, getAuthHeaders } = useAuth();
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(false);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [employees, setEmployees] = useState([]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: '',
    date: new Date().toISOString().split('T')[0],
    check_in: '08:30',
    check_out: '17:30',
    status: 'PRESENT',
    note: ''
  });

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  const isAdminOrHR = user?.role === 'admin' || user?.role === 'hr_manager';

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const url = isAdminOrHR
        ? `/api/attendance?month=${month}&year=${year}`
        : `/api/attendance?employee_id=${user.employee_id}&month=${month}&year=${year}`;
      const response = await fetch(url, { headers: getAuthHeaders() });
      if (response.ok) {
        setAttendance(await response.json());
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const fetchEmployees = async () => {
    if (!isAdminOrHR) return;
    try {
      const response = await fetch('/api/employees', { headers: getAuthHeaders() });
      if (response.ok) setEmployees(await response.json());
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    fetchAttendance();
    fetchEmployees();
  }, [month, year]);

  const handleExport = async () => {
    try {
      const response = await fetch(`/api/attendance/export?month=${month}&year=${year}`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `attendance_${month}_${year}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) { showToast('Lỗi khi tải file', 'error'); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/attendance', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        showToast('Đã thêm chấm công thủ công');
        setIsModalOpen(false);
        fetchAttendance();
      } else {
        const d = await response.json();
        showToast(d.error || 'Lỗi', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const renderStatus = (status) => {
    switch (status) {
      case 'PRESENT': return <span className="status-badge status-badge--approved">Có mặt</span>;
      case 'ABSENT': return <span className="status-badge status-badge--rejected">Vắng mặt</span>;
      case 'LATE': return <span className="status-badge status-badge--warning">Đi muộn</span>;
      case 'HALF_DAY': return <span className="status-badge status-badge--pending-hr">Nửa ngày</span>;
      case 'ON_LEAVE': return <span className="status-badge status-badge--cancelled">Nghỉ phép</span>;
      default: return <span className="status-badge">{status}</span>;
    }
  };

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
        <span className="breadcrumb__item">Chấm công</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Chấm công & Điểm danh</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Xem thời gian làm việc, xuất báo cáo chấm công hàng tháng.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <select className="input" value={month} onChange={e => setMonth(e.target.value)} style={{ width: '100px' }}>
              {[...Array(12).keys()].map(i => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
            </select>
            <select className="input" value={year} onChange={e => setYear(e.target.value)} style={{ width: '110px' }}>
              {[...Array(5).keys()].map(i => {
                const y = new Date().getFullYear() - 2 + i;
                return <option key={y} value={y}>Năm {y}</option>
              })}
            </select>
          </div>
          {isAdminOrHR && (
            <>
              <button className="btn btn--secondary" onClick={handleExport}>
                <Download size={16} /> Xuất CSV
              </button>
              <button className="btn btn--primary" onClick={() => setIsModalOpen(true)}>
                <Plus size={16} /> Thêm thủ công
              </button>
            </>
          )}
        </div>
      </div>

      <div className="card card--no-hover">
        <div className="card__body" style={{ padding: 0 }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
          ) : attendance.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
              Không có dữ liệu chấm công cho tháng {month}/{year}.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table--zebra attendance-table">
                <thead>
                  <tr>
                    {isAdminOrHR && <th>Nhân viên</th>}
                    <th>Ngày</th>
                    <th>Vào</th>
                    <th>Ra</th>
                    <th>Giờ làm</th>
                    <th>Trạng thái</th>
                    <th>Ghi chú</th>
                  </tr>
                </thead>
                <tbody>
                  {attendance.map(r => (
                    <tr key={r.id}>
                      {isAdminOrHR && <td style={{ fontWeight: 600 }}>{r.employee_name}</td>}
                      <td>{new Date(r.date).toLocaleDateString('vi-VN')}</td>
                      <td style={{ color: 'var(--color-success)' }}>{r.check_in || '---'}</td>
                      <td style={{ color: 'var(--color-error)' }}>{r.check_out || '---'}</td>
                      <td style={{ fontWeight: 600 }}>{r.work_hours}h</td>
                      <td>{renderStatus(r.status)}</td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>{r.note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '500px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Thêm chấm công thủ công</h3>
              <button className="modal__close" onClick={() => setIsModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Nhân viên</label>
                  <select
                    className="input"
                    value={formData.employee_id}
                    onChange={e => setFormData({ ...formData, employee_id: e.target.value })}
                    required
                  >
                    <option value="">-- Chọn nhân viên --</option>
                    {employees.map(emp => (
                      <option key={emp.id} value={emp.id}>{emp.full_name} ({emp.employee_id})</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Ngày</label>
                  <input type="date" className="input" value={formData.date} onChange={e => setFormData({ ...formData, date: e.target.value })} required />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Giờ vào</label>
                    <input type="time" className="input" value={formData.check_in} onChange={e => setFormData({ ...formData, check_in: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Giờ ra</label>
                    <input type="time" className="input" value={formData.check_out} onChange={e => setFormData({ ...formData, check_out: e.target.value })} />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Trạng thái</label>
                  <select className="input" value={formData.status} onChange={e => setFormData({ ...formData, status: e.target.value })} required>
                    <option value="PRESENT">Có mặt</option>
                    <option value="ABSENT">Vắng mặt</option>
                    <option value="LATE">Đi muộn</option>
                    <option value="HALF_DAY">Nửa ngày</option>
                    <option value="ON_LEAVE">Nghỉ phép</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Ghi chú</label>
                  <input type="text" className="input" value={formData.note} onChange={e => setFormData({ ...formData, note: e.target.value })} />
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsModalOpen(false)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu chấm công</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendancePage;
