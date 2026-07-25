import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Download, Plus, Loader2, CheckCircle, MapPin, LogIn, LogOut,
  Pencil, Trash2, ShieldCheck, AlertTriangle, Table2, ListChecks, Wifi
} from 'lucide-react';



const STATUS_OPTS = [
  ['', 'Tự xác định theo ca'], ['PRESENT', 'Có mặt'], ['ABSENT', 'Vắng mặt'],
  ['LATE', 'Đi muộn'], ['EARLY_LEAVE', 'Về sớm'], ['HALF_DAY', 'Nửa ngày'],
  ['ON_LEAVE', 'Nghỉ phép'],
];

const AttendancePage = () => {
  const { user, authFetch } = useAuth();
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(false);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [employees, setEmployees] = useState([]);
  const [view, setView] = useState('log'); // 'log' | 'summary'
  const [summary, setSummary] = useState([]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    employee_id: '', date: new Date().toISOString().split('T')[0],
    check_in: '08:30', check_out: '17:30', status: '', note: ''
  });

  // ── Tự chấm công ──────────────────────────────────────────────
  const [today, setToday] = useState(null);
  const [hasLocation, setHasLocation] = useState(true);
  const [ipMatch, setIpMatch] = useState(false);
  const [clientIp, setClientIp] = useState('');
  const [punching, setPunching] = useState(false);

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  };

  const isAdminOrHR = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'hr_manager';
  const canSelfPunch = !!user?.employee_id;

  const fetchAttendance = async () => {
    setLoading(true);
    try {
      const url = isAdminOrHR
        ? `/api/attendance?month=${month}&year=${year}`
        : `/api/attendance?employee_id=${user.employee_id}&month=${month}&year=${year}`;
      const response = await authFetch(url);
      if (response.ok) setAttendance(await response.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const fetchEmployees = async () => {
    if (!isAdminOrHR) return;
    try {
      const response = await authFetch('/api/employees');
      if (response.ok) setEmployees(await response.json());
    } catch (err) { console.error(err); }
  };

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`/api/attendance/summary?month=${month}&year=${year}`);
      if (res.ok) setSummary((await res.json()).rows || []);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const fetchToday = async () => {
    if (!canSelfPunch) return;
    try {
      const res = await authFetch('/api/attendance/today');
      if (res.ok) {
        const data = await res.json();
        setToday(data.attendance);
        setHasLocation(data.has_work_location);
        setIpMatch(data.ip_match);
        setClientIp(data.client_ip || '');
      }
    } catch (err) { console.error(err); }
  };

  useEffect(() => {
    if (view === 'summary') fetchSummary(); else fetchAttendance();
    fetchEmployees();
    /* eslint-disable-next-line */
  }, [month, year, view]);
  useEffect(() => { fetchToday(); /* eslint-disable-next-line */ }, []);

  const punch = async (kind) => {
    setPunching(true);
    try {
      const res = await authFetch(`/api/attendance/${kind}`, {
        method: 'POST', body: JSON.stringify({}),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message);
        setToday(data.attendance);
        fetchAttendance();
        fetchToday();
      } else {
        showToast(data.error || 'Chấm công thất bại.', 'error');
      }
    } catch (e) {
      showToast(e.message || 'Lỗi kết nối.', 'error');
    } finally {
      setPunching(false);
    }
  };

  const handleExportSummary = async () => {
    try {
      const response = await authFetch(`/api/attendance/summary/export?month=${month}&year=${year}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `tong_cong_${month}_${year}.csv`;
        document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url);
      }
    } catch (err) { showToast('Lỗi khi tải file', 'error'); }
  };

  const handleExport = async () => {
    try {
      const response = await authFetch(`/api/attendance/export?month=${month}&year=${year}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `attendance_${month}_${year}.csv`;
        document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url);
      }
    } catch (err) { showToast('Lỗi khi tải file', 'error'); }
  };

  const openCreate = () => {
    setEditingId(null);
    setFormData({ employee_id: '', date: new Date().toISOString().split('T')[0], check_in: '08:30', check_out: '17:30', status: '', note: '' });
    setIsModalOpen(true);
  };

  const openEdit = (r) => {
    setEditingId(r.id);
    setFormData({ employee_id: r.employee_id, date: r.date, check_in: r.check_in || '', check_out: r.check_out || '', status: r.status, note: r.note || '' });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const url = editingId ? `/api/attendance/${editingId}` : '/api/attendance';
    try {
      const response = await authFetch(url, { method: editingId ? 'PUT' : 'POST', body: JSON.stringify(formData) });
      const d = await response.json();
      if (response.ok) {
        showToast(editingId ? 'Đã cập nhật chấm công' : 'Đã thêm chấm công thủ công');
        setIsModalOpen(false);
        if (view === 'summary') fetchSummary(); else fetchAttendance();
      } else {
        showToast(d.error || 'Lỗi', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const handleDelete = async (r) => {
    if (!window.confirm(`Xóa chấm công ngày ${new Date(r.date).toLocaleDateString('vi-VN')} của ${r.employee_name}?`)) return;
    try {
      const res = await authFetch(`/api/attendance/${r.id}`, { method: 'DELETE' });
      const d = await res.json();
      showToast(res.ok ? d.message : d.error, res.ok ? 'success' : 'error');
      if (res.ok) fetchAttendance();
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const renderStatus = (status) => {
    switch (status) {
      case 'PRESENT': return <span className="status-badge status-badge--approved">Có mặt</span>;
      case 'ABSENT': return <span className="status-badge status-badge--rejected">Vắng mặt</span>;
      case 'LATE': return <span className="status-badge status-badge--warning">Đi muộn</span>;
      case 'EARLY_LEAVE': return <span className="status-badge status-badge--warning">Về sớm</span>;
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
        <span>GrapeHRM</span><span>&gt;</span>
        <span className="breadcrumb__item">Chấm công</span>
      </div>

      {/* ── Thẻ tự chấm công (geofence) ── */}
      {canSelfPunch && (
        <div className="card card--no-hover" style={{ marginBottom: '20px' }}>
          <div className="card__header">
            <h3 className="card__title"><MapPin size={18} /><span>Chấm công hôm nay</span></h3>
          </div>
          <div className="card__body">
            {!hasLocation && (
              <div className="alert alert--error" style={{ marginBottom: '12px' }}>
                <AlertTriangle size={16} />
                <span>Công ty chưa cấu hình địa điểm làm việc — chưa thể chấm công. Liên hệ quản trị viên.</span>
              </div>
            )}
            {hasLocation && !ipMatch && (
              <div className="alert alert--error" style={{ marginBottom: '12px' }}>
                <Wifi size={16} />
                <span>IP của bạn (<b>{clientIp}</b>) không nằm trong mạng văn phòng. Hãy kết nối Wi-Fi/mạng LAN công ty để chấm công.</span>
              </div>
            )}
            {hasLocation && ipMatch && (
              <div className="alert alert--success" style={{ marginBottom: '12px' }}>
                <ShieldCheck size={16} />
                <span>IP của bạn (<b>{clientIp}</b>) đã được xác thực — mạng văn phòng hợp lệ.</span>
              </div>
            )}
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '24px' }}>
              <div style={{ display: 'flex', gap: '32px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Giờ vào</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-success)' }}>{today?.check_in || '--:--'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Giờ ra</div>
                  <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-error)' }}>{today?.check_out || '--:--'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Trạng thái</div>
                  <div style={{ marginTop: '4px' }}>{today ? renderStatus(today.status) : <span style={{ color: 'var(--color-text-muted)' }}>Chưa chấm</span>}</div>
                </div>
                {today?.ip_verified && (
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Xác thực</div>
                    <div style={{ marginTop: '4px', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: 600 }}>
                      <ShieldCheck size={15} /> IP văn phòng
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', gap: '12px', marginLeft: 'auto' }}>
                <button
                  className="btn btn--primary"
                  onClick={() => punch('check-in')}
                  disabled={punching || !hasLocation || !!today?.check_in}
                >
                  {punching ? <Loader2 size={16} className="animate-spin" /> : <LogIn size={16} />} Chấm vào
                </button>
                <button
                  className="btn btn--secondary"
                  onClick={() => punch('check-out')}
                  disabled={punching || !hasLocation || !today?.check_in || !!today?.check_out}
                >
                  {punching ? <Loader2 size={16} className="animate-spin" /> : <LogOut size={16} />} Chấm ra
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>
            {view === 'summary' ? 'Tổng công tháng' : (isAdminOrHR ? 'Bảng chấm công' : 'Lịch sử chấm công')}
          </h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
            {view === 'summary'
              ? 'Tự động tính từ dữ liệu chấm công + nghỉ phép + tăng ca — không nhập tay.'
              : 'Xem thời gian làm việc, xuất báo cáo chấm công hàng tháng.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', border: '1px solid var(--color-border, #dee2e6)', borderRadius: '6px', overflow: 'hidden' }}>
            <button className={`btn ${view === 'log' ? 'btn--primary' : 'btn--secondary'}`} style={{ borderRadius: 0 }} onClick={() => setView('log')}>
              <ListChecks size={15} /> Nhật ký
            </button>
            <button className={`btn ${view === 'summary' ? 'btn--primary' : 'btn--secondary'}`} style={{ borderRadius: 0 }} onClick={() => setView('summary')}>
              <Table2 size={15} /> Tổng công tháng
            </button>
          </div>
          <select className="input" value={month} onChange={e => setMonth(e.target.value)} style={{ width: '100px' }}>
            {[...Array(12).keys()].map(i => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select className="input" value={year} onChange={e => setYear(e.target.value)} style={{ width: '110px' }}>
            {[...Array(5).keys()].map(i => { const y = new Date().getFullYear() - 2 + i; return <option key={y} value={y}>Năm {y}</option>; })}
          </select>
          {isAdminOrHR && (
            <>
              <button className="btn btn--secondary" onClick={view === 'summary' ? handleExportSummary : handleExport}>
                <Download size={16} /> Xuất CSV
              </button>
              {view === 'log' && (
                <button className="btn btn--primary" onClick={openCreate}><Plus size={16} /> Thêm thủ công</button>
              )}
            </>
          )}
        </div>
      </div>

      {view === 'summary' && (
        <div className="card card--no-hover">
          <div className="card__body" style={{ padding: 0 }}>
            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
            ) : summary.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                Không có dữ liệu tổng công cho tháng {month}/{year}.
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table--zebra">
                  <thead>
                    <tr>
                      <th>Mã NV</th><th>Nhân viên</th><th>Phòng ban</th>
                      <th title="Số ngày làm việc chuẩn của tháng">Công chuẩn</th>
                      <th>Đủ công</th><th>Nửa công</th>
                      <th title="Có chấm vào nhưng quên chấm ra — tạm tính 0.5 công">Thiếu ra</th>
                      <th>Muộn (lần)</th><th>Phép</th><th>Không lương</th><th>Vắng</th><th>OT (giờ)</th>
                      <th style={{ fontWeight: 700 }}>TỔNG CÔNG</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.map(r => (
                      <tr key={r.employee_id}>
                        <td>{r.employee_code}</td>
                        <td style={{ fontWeight: 600 }}>{r.employee_name}</td>
                        <td style={{ color: 'var(--color-text-muted)' }}>{r.department || '—'}</td>
                        <td>{r.standard_days}</td>
                        <td>{r.full_days}</td>
                        <td>{r.half_days || ''}</td>
                        <td style={{ color: r.missing_checkout ? 'var(--color-error)' : undefined }}>
                          {r.missing_checkout ? `⚠ ${r.missing_checkout}` : ''}
                        </td>
                        <td style={{ color: r.late_count ? '#b8860b' : undefined }}>
                          {r.late_count ? `${r.late_count} (${r.late_minutes}p)` : ''}
                        </td>
                        <td>{r.paid_leave || ''}</td>
                        <td>{r.unpaid_leave || ''}</td>
                        <td style={{ color: r.absent_days ? 'var(--color-error)' : undefined }}>{r.absent_days || ''}</td>
                        <td>{r.ot_hours || ''}</td>
                        <td style={{ fontWeight: 700, color: 'var(--color-primary-dark)' }}>{r.total_workdays}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {view === 'log' && (
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
                    <th>Ngày</th><th>Vào</th><th>Ra</th><th>Giờ làm</th><th>Trạng thái</th><th>Nguồn</th><th>Ghi chú</th>
                    {isAdminOrHR && <th style={{ textAlign: 'right' }}>Thao tác</th>}
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
                      <td>
                        {r.source === 'SELF'
                          ? <span className="badge badge--info">Tự chấm</span>
                          : <span className="badge badge--warning">Nhập tay</span>}
                      </td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>{r.note}</td>
                      {isAdminOrHR && (
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: '12px', marginRight: '6px' }} onClick={() => openEdit(r)}><Pencil size={13} /></button>
                          <button className="btn btn--danger" style={{ padding: '4px 9px', fontSize: '12px' }} onClick={() => handleDelete(r)}><Trash2 size={13} /></button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      )}

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '500px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{editingId ? 'Sửa chấm công' : 'Thêm chấm công thủ công'}</h3>
              <button className="modal__close" onClick={() => setIsModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Nhân viên</label>
                  <select className="input" value={formData.employee_id} onChange={e => setFormData({ ...formData, employee_id: e.target.value })} required disabled={!!editingId}>
                    <option value="">-- Chọn nhân viên --</option>
                    {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.full_name} ({emp.employee_id})</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Ngày</label>
                  <input type="date" className="input" value={formData.date} onChange={e => setFormData({ ...formData, date: e.target.value })} required disabled={!!editingId} />
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
                  <label className="form-label">Trạng thái</label>
                  <select className="input" value={formData.status} onChange={e => setFormData({ ...formData, status: e.target.value })}>
                    {STATUS_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Ghi chú</label>
                  <input type="text" className="input" value={formData.note} onChange={e => setFormData({ ...formData, note: e.target.value })} />
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsModalOpen(false)}>Hủy</button>
                <button type="submit" className="btn btn--primary">{editingId ? 'Cập nhật' : 'Lưu chấm công'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttendancePage;
