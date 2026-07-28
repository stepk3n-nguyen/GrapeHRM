import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Clock4, Plus, Loader2, CheckCircle, Check, X, Trash2, Edit2 } from 'lucide-react';

const OT_TYPES = [
  { value: 'WEEKDAY', label: 'Ngày thường (150%)' },
  { value: 'WEEKEND', label: 'Cuối tuần (200%)' },
  { value: 'HOLIDAY', label: 'Ngày lễ (300%)' },
];
const STATUS_BADGE = {
  PENDING: { cls: 'status-badge--warning', text: 'Chờ duyệt' },
  APPROVED: { cls: 'status-badge--approved', text: 'Đã duyệt' },
  REJECTED: { cls: 'status-badge--rejected', text: 'Từ chối' },
};

const OvertimePage = () => {
  const { user, authFetch } = useAuth();
  const isHR = ['admin', 'super_admin', 'hr_manager'].includes(user?.role);

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // null | { form }
  const [toasts, setToasts] = useState([]);
  const [employees, setEmployees] = useState([]);

  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/overtime');
      if (res.ok) setItems(await res.json());
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };

  const fetchEmployees = async () => {
    if (!isHR) return;
    try {
      const res = await authFetch('/api/employees');
      if (res.ok) {
        const data = await res.json();
        setEmployees(data.filter(e => e.state === 'ACTIVE'));
      }
    } catch { }
  };

  useEffect(() => { 
    fetchItems(); 
    if (isHR) fetchEmployees();
    /* eslint-disable-next-line */ 
  }, [isHR]);

  const submit = async (e) => {
    e.preventDefault();
    const isEdit = !!modal.form.id;
    const url = isEdit ? `/api/overtime/${modal.form.id}` : '/api/overtime';
    const method = isEdit ? 'PUT' : 'POST';
    const res = await authFetch(url, { method, body: JSON.stringify(modal.form) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setModal(null); fetchItems(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };

  const act = async (id, action) => {
    if (action === 'delete') {
      if (!window.confirm('Bạn có chắc chắn muốn hủy đơn này?')) return;
    }
    const method = action === 'delete' ? 'DELETE' : 'PUT';
    const url = action === 'delete' ? `/api/overtime/${id}` : `/api/overtime/${id}/${action}`;
    const res = await authFetch(url, { method });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchItems();
  };

  const pending = items.filter((o) => o.status === 'PENDING').length;

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>

      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Tăng ca</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Tăng ca (Overtime)</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: 13, marginTop: 4 }}>
            {isHR ? `Duyệt đơn tăng ca — ${pending} đơn chờ. Tiền OT tự cộng vào bảng lương tháng.` : 'Đăng ký tăng ca; tiền OT sẽ cộng vào phiếu lương sau khi HR duyệt.'}
          </p>
        </div>
        <button className="btn btn--primary" onClick={() => setModal({ form: { date: '', hours: 2, ot_type: 'WEEKDAY', reason: '', employee_id: '' } })}><Plus size={16} /> Đăng ký tăng ca</button>
      </div>

      <div className="card card--no-hover">
        <div className="card__body" style={{ padding: 0 }}>
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div> : (
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr>{isHR && <th>Nhân viên</th>}<th>Ngày</th><th>Số giờ</th><th>Loại</th><th>Lý do</th><th>Trạng thái</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                <tbody>
                  {items.map((o) => {
                    const sb = STATUS_BADGE[o.status] || STATUS_BADGE.PENDING;
                    return (
                      <tr key={o.id}>
                        {isHR && <td style={{ fontWeight: 600 }}>{o.employee_name}</td>}
                        <td style={{ whiteSpace: 'nowrap' }}>{o.date.split('-').reverse().join('/')}</td>
                        <td>{o.hours} giờ</td>
                        <td><span className="badge badge--info">{o.ot_type_label}</span></td>
                        <td style={{ color: 'var(--color-text-muted)', maxWidth: 200 }}>{o.reason || '—'}</td>
                        <td><span className={`status-badge ${sb.cls}`}>{sb.text}</span></td>
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', alignItems: 'center' }}>
                            {isHR && o.status === 'PENDING' && (
                              <>
                                <button className="btn btn--primary" style={{ padding: '6px 10px', fontSize: 12 }} onClick={() => act(o.id, 'approve')}><Check size={14} /></button>
                                <button className="btn btn--danger" style={{ padding: '6px 10px', fontSize: 12 }} onClick={() => act(o.id, 'reject')}><X size={14} /></button>
                              </>
                            )}
                            {isHR && (
                              <button 
                                className="btn" 
                                style={{ padding: '6px 10px', backgroundColor: '#fff', border: '1px solid var(--color-primary)', color: 'var(--color-primary)', borderRadius: '6px' }} 
                                onClick={() => setModal({ form: { id: o.id, date: o.date.split('T')[0], hours: o.hours, ot_type: o.ot_type, reason: o.reason || '', employee_id: o.employee_id } })}
                                title="Sửa"
                              >
                                <Edit2 size={14} />
                              </button>
                            )}
                            {(isHR || o.status === 'PENDING') && (
                              <button 
                                className="btn btn--danger" 
                                style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid transparent' }} 
                                onClick={() => act(o.id, 'delete')}
                                title="Xóa"
                              >
                                <Trash2 size={14} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {items.length === 0 && <tr><td colSpan={isHR ? 7 : 6} style={{ textAlign: 'center', padding: 32, color: 'var(--color-text-muted)' }}>Chưa có đơn tăng ca nào.</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {modal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 440 }}>
            <div className="modal__header">
              <h3 className="modal__title">{modal.form.id ? 'Sửa đơn tăng ca' : 'Đăng ký tăng ca'}</h3>
              <button className="modal__close" onClick={() => setModal(null)}>&times;</button>
            </div>
            <form onSubmit={submit}>
              <div className="modal__body">
                {isHR && (
                  <div className="form-group">
                    <label className="form-label form-label--required">Nhân viên</label>
                    <select className="input" value={modal.form.employee_id || ''} onChange={(e) => setModal({ form: { ...modal.form, employee_id: e.target.value } })} required>
                      <option value="">-- Chọn nhân viên --</option>
                      {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.employee_id} - {emp.full_name}</option>)}
                    </select>
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label form-label--required">Ngày tăng ca</label>
                  <input type="date" className="input" value={modal.form.date} onChange={(e) => setModal({ form: { ...modal.form, date: e.target.value } })} required />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="form-group">
                    <label className="form-label form-label--required">Số giờ</label>
                    <input type="number" min="0.5" max="12" step="0.5" className="input" value={modal.form.hours} onChange={(e) => setModal({ form: { ...modal.form, hours: e.target.value } })} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required">Loại ngày</label>
                    <select className="input" value={modal.form.ot_type} onChange={(e) => setModal({ form: { ...modal.form, ot_type: e.target.value } })}>
                      {OT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Lý do</label>
                  <textarea className="input" rows={2} value={modal.form.reason} onChange={(e) => setModal({ form: { ...modal.form, reason: e.target.value } })} placeholder="Vd: hoàn thành tính năng gấp" />
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setModal(null)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Gửi đơn</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default OvertimePage;
