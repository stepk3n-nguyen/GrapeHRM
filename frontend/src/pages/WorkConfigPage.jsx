import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  MapPin, Clock, Plus, Loader2, CheckCircle, Crosshair, Pencil, Trash2, Star,
  CalendarDays, CalendarPlus
} from 'lucide-react';

const emptyLoc = { name: '', is_active: true, allowed_ips: '' };
const emptyShift = { name: '', start_time: '08:30', end_time: '17:30', late_threshold_minutes: 15, break_minutes: 60, is_default: false };
const currentYear = new Date().getFullYear();
const emptyHoliday = { name: '', date: '', is_paid: true, is_recurring: false };

const WorkConfigPage = () => {
  const { authFetch, user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const [tab, setTab] = useState(isAdmin ? 'locations' : 'shifts');

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const [locations, setLocations] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [holidays, setHolidays] = useState([]);
  const [holidayYear, setHolidayYear] = useState(currentYear);
  const [loading, setLoading] = useState(true);

  const [locModal, setLocModal] = useState(null); // null | {form, id?}
  const [shiftModal, setShiftModal] = useState(null);
  const [holidayModal, setHolidayModal] = useState(null);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [lr, sr] = await Promise.all([
        authFetch('/api/work-locations'),
        authFetch('/api/work-shifts'),
      ]);
      if (lr.ok) setLocations(await lr.json());
      if (sr.ok) setShifts(await sr.json());
    } catch {
      showToast('Lỗi kết nối.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchHolidays = async (year = holidayYear) => {
    try {
      const res = await authFetch(`/api/holidays?year=${year}`);
      if (res.ok) setHolidays(await res.json());
    } catch { showToast('Lỗi tải ngày lễ.', 'error'); }
  };

  useEffect(() => { fetchAll(); /* eslint-disable-next-line */ }, []);
  useEffect(() => { fetchHolidays(holidayYear); /* eslint-disable-next-line */ }, [holidayYear]);

  // ── Địa điểm ────────────────────────────────────────────────
  const saveLocation = async (e) => {
    e.preventDefault();
    const { form, id } = locModal;
    const payload = {
      name: form.name,
      is_active: form.is_active,
      allowed_ips: form.allowed_ips || '',
    };
    const url = id ? `/api/work-locations/${id}` : '/api/work-locations';
    const res = await authFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setLocModal(null); fetchAll(); }
    else showToast(data.error || 'Lưu thất bại.', 'error');
  };

  const deleteLocation = async (loc) => {
    if (!window.confirm(`Xóa địa điểm "${loc.name}"?`)) return;
    const res = await authFetch(`/api/work-locations/${loc.id}`, { method: 'DELETE' });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchAll();
  };

  // ── Ca làm ──────────────────────────────────────────────────
  const saveShift = async (e) => {
    e.preventDefault();
    const { form, id } = shiftModal;
    const payload = {
      name: form.name,
      start_time: form.start_time,
      end_time: form.end_time,
      late_threshold_minutes: parseInt(form.late_threshold_minutes, 10),
      break_minutes: parseInt(form.break_minutes, 10),
      is_default: form.is_default,
    };
    const url = id ? `/api/work-shifts/${id}` : '/api/work-shifts';
    const res = await authFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setShiftModal(null); fetchAll(); }
    else showToast(data.error || 'Lưu thất bại.', 'error');
  };

  const deleteShift = async (s) => {
    if (!window.confirm(`Xóa ca làm "${s.name}"?`)) return;
    const res = await authFetch(`/api/work-shifts/${s.id}`, { method: 'DELETE' });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchAll();
  };

  // ── Ngày lễ ─────────────────────────────────────────────────
  const saveHoliday = async (e) => {
    e.preventDefault();
    const { form, id } = holidayModal;
    const url = id ? `/api/holidays/${id}` : '/api/holidays';
    const res = await authFetch(url, { method: id ? 'PUT' : 'POST', body: JSON.stringify(form) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setHolidayModal(null); fetchHolidays(); }
    else showToast(data.error || 'Lưu thất bại.', 'error');
  };

  const deleteHoliday = async (h) => {
    if (!window.confirm(`Xóa ngày lễ "${h.name}" (${h.date})?`)) return;
    const res = await authFetch(`/api/holidays/${h.id}`, { method: 'DELETE' });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchHolidays();
  };

  const seedVnHolidays = async () => {
    if (!window.confirm(`Nạp các ngày lễ pháp định Việt Nam cho năm ${holidayYear}?`)) return;
    const res = await authFetch('/api/holidays/seed-vn', { method: 'POST', body: JSON.stringify({ year: holidayYear }) });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchHolidays();
  };

  const weekdayVN = (iso) => ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'][new Date(iso + 'T00:00:00').getDay()];

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
        <span className="breadcrumb__item">Cấu hình chấm công</span>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Cấu hình chấm công</h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Khai báo mạng văn phòng (IP whitelist) và ca làm để hệ thống xác thực kết nối & tính đi muộn.
        </p>
      </div>

      <div className="leave-tabs">
        {isAdmin && (
          <button className={`leave-tabs__tab ${tab === 'locations' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab('locations')}>
            <MapPin size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /> Địa điểm làm việc
          </button>
        )}
        <button className={`leave-tabs__tab ${tab === 'shifts' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab('shifts')}>
          <Clock size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /> Ca làm việc
        </button>
        <button className={`leave-tabs__tab ${tab === 'holidays' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab('holidays')}>
          <CalendarDays size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /> Ngày lễ
        </button>
      </div>

      {loading ? (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div></div>
      ) : tab === 'locations' ? (
        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title"><MapPin size={18} /><span>Địa điểm ({locations.length})</span></h3>
            {isAdmin && (
              <button className="btn btn--primary" onClick={() => setLocModal({ form: { ...emptyLoc } })}><Plus size={16} /> Thêm địa điểm</button>
            )}
          </div>
          <div className="card__body" style={{ padding: 0 }}>
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr><th>Tên</th><th>IP cho phép</th><th>Trạng thái</th>{isAdmin && <th style={{ textAlign: 'right' }}>Thao tác</th>}</tr></thead>
                <tbody>
                  {locations.map((l) => (
                    <tr key={l.id}>
                      <td style={{ fontWeight: 600 }}>{l.name}</td>
                      <td><code style={{ fontSize: '12px' }}>{l.allowed_ips || '—'}</code></td>
                      <td>{l.is_active ? <span className="status-badge status-badge--approved">Bật</span> : <span className="status-badge status-badge--rejected">Tắt</span>}</td>
                      {isAdmin && (
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <button className="btn btn--secondary" style={{ padding: '4px 10px', fontSize: '12px', marginRight: '6px' }} onClick={() => setLocModal({ id: l.id, form: { ...l } })}><Pencil size={13} /></button>
                          <button className="btn btn--danger" style={{ padding: '4px 10px', fontSize: '12px' }} onClick={() => deleteLocation(l)}><Trash2 size={13} /></button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {locations.length === 0 && <tr><td colSpan={isAdmin ? 4 : 3} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)' }}>Chưa có địa điểm nào. Nhân viên sẽ không chấm công được cho tới khi bạn thêm ít nhất 1 địa điểm.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : tab === 'shifts' ? (
        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title"><Clock size={18} /><span>Ca làm ({shifts.length})</span></h3>
            <button className="btn btn--primary" onClick={() => setShiftModal({ form: { ...emptyShift } })}><Plus size={16} /> Thêm ca</button>
          </div>
          <div className="card__body" style={{ padding: 0 }}>
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr><th>Tên ca</th><th>Vào</th><th>Ra</th><th>Trễ tối đa</th><th>Nghỉ trưa</th><th>Mặc định</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                <tbody>
                  {shifts.map((s) => (
                    <tr key={s.id}>
                      <td style={{ fontWeight: 600 }}>{s.name}</td>
                      <td>{s.start_time}</td>
                      <td>{s.end_time}</td>
                      <td>{s.late_threshold_minutes} phút</td>
                      <td>{s.break_minutes} phút</td>
                      <td>{s.is_default ? <span className="status-badge status-badge--approved"><Star size={12} style={{ marginRight: '3px', verticalAlign: 'middle' }} />Mặc định</span> : '—'}</td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <button className="btn btn--secondary" style={{ padding: '4px 10px', fontSize: '12px', marginRight: '6px' }} onClick={() => setShiftModal({ id: s.id, form: { ...s } })}><Pencil size={13} /></button>
                        <button className="btn btn--danger" style={{ padding: '4px 10px', fontSize: '12px' }} onClick={() => deleteShift(s)}><Trash2 size={13} /></button>
                      </td>
                    </tr>
                  ))}
                  {shifts.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)' }}>Chưa có ca làm nào.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <h3 className="card__title"><CalendarDays size={18} /><span>Ngày lễ năm {holidayYear} ({holidays.length})</span></h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
              <select className="input" style={{ width: 'auto', padding: '6px 10px' }} value={holidayYear} onChange={(e) => setHolidayYear(Number(e.target.value))}>
                {[currentYear - 1, currentYear, currentYear + 1].map((y) => <option key={y} value={y}>Năm {y}</option>)}
              </select>
              <button className="btn btn--secondary" onClick={seedVnHolidays}><CalendarPlus size={15} /> Nạp lễ VN</button>
              <button className="btn btn--primary" onClick={() => setHolidayModal({ form: { ...emptyHoliday } })}><Plus size={16} /> Thêm ngày lễ</button>
            </div>
          </div>
          <div className="card__body" style={{ padding: 0 }}>
            {/* <div style={{ padding: '10px 16px', fontSize: '12.5px', color: 'var(--color-text-muted)', borderBottom: '1px solid var(--color-border)' }}>
              Lịch nghỉ lễ là <b>của riêng công ty bạn</b> — có thể theo đúng lịch nhà nước, ít hơn, nhiều hơn, hoặc bỏ trống.
              Bấm "Nạp lễ VN" để lấy nhanh lịch nhà nước rồi tự chỉnh. Ngày lễ được loại khỏi <b>ngày công chuẩn</b> khi
              tính lương và <b>không bị trừ</b> vào quỹ phép nếu đơn nghỉ trùng ngày lễ.
            </div> */}
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr><th>Ngày</th><th>Thứ</th><th>Tên ngày lễ</th><th>Hưởng lương</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                <tbody>
                  {holidays.map((h) => (
                    <tr key={h.id}>
                      <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{h.date.split('-').reverse().join('/')}</td>
                      <td style={{ color: 'var(--color-text-muted)' }}>{weekdayVN(h.date)}</td>
                      <td>{h.name}</td>
                      <td>{h.is_paid ? <span className="status-badge status-badge--approved">Có lương</span> : <span className="status-badge status-badge--pending">Không lương</span>}</td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <button className="btn btn--secondary" style={{ padding: '4px 10px', fontSize: '12px', marginRight: '6px' }} onClick={() => setHolidayModal({ id: h.id, form: { name: h.name, date: h.date, is_paid: h.is_paid, is_recurring: h.is_recurring } })}><Pencil size={13} /></button>
                        <button className="btn btn--danger" style={{ padding: '4px 10px', fontSize: '12px' }} onClick={() => deleteHoliday(h)}><Trash2 size={13} /></button>
                      </td>
                    </tr>
                  ))}
                  {holidays.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)' }}>Chưa có ngày lễ nào cho năm {holidayYear}. Bấm "Nạp lễ VN" để thêm nhanh các ngày lễ pháp định.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Modal địa điểm */}
      {locModal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '480px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{locModal.id ? 'Sửa địa điểm' : 'Thêm địa điểm'}</h3>
              <button className="modal__close" onClick={() => setLocModal(null)}>&times;</button>
            </div>
            <form onSubmit={saveLocation}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Tên địa điểm</label>
                  <input className="input" value={locModal.form.name} onChange={(e) => setLocModal({ ...locModal, form: { ...locModal.form, name: e.target.value } })} required />
                </div>
                <div className="form-group">
                  <label className="form-label">IP cho phép (Public IP văn phòng)</label>
                  <input className="input" value={locModal.form.allowed_ips || ''} onChange={(e) => setLocModal({ ...locModal, form: { ...locModal.form, allowed_ips: e.target.value } })} placeholder="vd: 113.23.45.67, 113.23.45.68" />
                  <small style={{ color: 'var(--color-text-muted)', fontSize: '11px', display: 'block', marginTop: '4px' }}>
                    Nhiều IP cách nhau bằng dấu phẩy. Để trống nếu chỉ dùng định vị.
                  </small>
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
                  <input type="checkbox" checked={locModal.form.is_active} onChange={(e) => setLocModal({ ...locModal, form: { ...locModal.form, is_active: e.target.checked } })} />
                  Đang sử dụng
                </label>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setLocModal(null)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal ca làm */}
      {shiftModal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '480px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{shiftModal.id ? 'Sửa ca làm' : 'Thêm ca làm'}</h3>
              <button className="modal__close" onClick={() => setShiftModal(null)}>&times;</button>
            </div>
            <form onSubmit={saveShift}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Tên ca</label>
                  <input className="input" value={shiftModal.form.name} onChange={(e) => setShiftModal({ ...shiftModal, form: { ...shiftModal.form, name: e.target.value } })} required />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className="form-group">
                    <label className="form-label form-label--required">Giờ vào</label>
                    <input type="time" className="input" value={shiftModal.form.start_time} onChange={(e) => setShiftModal({ ...shiftModal, form: { ...shiftModal.form, start_time: e.target.value } })} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required">Giờ ra</label>
                    <input type="time" className="input" value={shiftModal.form.end_time} onChange={(e) => setShiftModal({ ...shiftModal, form: { ...shiftModal.form, end_time: e.target.value } })} required />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className="form-group">
                    <label className="form-label">Trễ tối đa (phút)</label>
                    <input type="number" min="0" className="input" value={shiftModal.form.late_threshold_minutes} onChange={(e) => setShiftModal({ ...shiftModal, form: { ...shiftModal.form, late_threshold_minutes: e.target.value } })} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Nghỉ trưa (phút)</label>
                    <input type="number" min="0" className="input" value={shiftModal.form.break_minutes} onChange={(e) => setShiftModal({ ...shiftModal, form: { ...shiftModal.form, break_minutes: e.target.value } })} />
                  </div>
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
                  <input type="checkbox" checked={shiftModal.form.is_default} onChange={(e) => setShiftModal({ ...shiftModal, form: { ...shiftModal.form, is_default: e.target.checked } })} />
                  Đặt làm ca mặc định (dùng để tính đi muộn)
                </label>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setShiftModal(null)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal ngày lễ */}
      {holidayModal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '440px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{holidayModal.id ? 'Sửa ngày lễ' : 'Thêm ngày lễ'}</h3>
              <button className="modal__close" onClick={() => setHolidayModal(null)}>&times;</button>
            </div>
            <form onSubmit={saveHoliday}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Tên ngày lễ</label>
                  <input className="input" value={holidayModal.form.name} onChange={(e) => setHolidayModal({ ...holidayModal, form: { ...holidayModal.form, name: e.target.value } })} placeholder="vd: Quốc khánh" required />
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Ngày</label>
                  <input type="date" className="input" value={holidayModal.form.date} onChange={(e) => setHolidayModal({ ...holidayModal, form: { ...holidayModal.form, date: e.target.value } })} required />
                </div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', marginBottom: '10px' }}>
                  <input type="checkbox" checked={holidayModal.form.is_paid} onChange={(e) => setHolidayModal({ ...holidayModal, form: { ...holidayModal.form, is_paid: e.target.checked } })} />
                  Nghỉ có hưởng lương (loại khỏi ngày công chuẩn)
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
                  <input type="checkbox" checked={holidayModal.form.is_recurring} onChange={(e) => setHolidayModal({ ...holidayModal, form: { ...holidayModal.form, is_recurring: e.target.checked } })} />
                  Lặp lại hằng năm (lễ dương lịch cố định)
                </label>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setHolidayModal(null)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkConfigPage;
