import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { FileSignature, Plus, Loader2, CheckCircle, Pencil, Trash2, AlertTriangle } from 'lucide-react';

const TYPES = [
  { value: 'PROBATION', label: 'Thử việc' },
  { value: 'FIXED_TERM', label: 'Xác định thời hạn' },
  { value: 'INDEFINITE', label: 'Không xác định thời hạn' },
  { value: 'SEASONAL', label: 'Thời vụ' },
];
const STATUS = {
  ACTIVE: ['status-badge--approved', 'Hiệu lực'],
  EXPIRED: ['status-badge--rejected', 'Hết hạn'],
  TERMINATED: ['status-badge--rejected', 'Chấm dứt'],
};
const fmtMoney = (v) => (v ? `${Number(v).toLocaleString('vi-VN')} đ` : '—');
const empty = { employee_id: '', contract_number: '', contract_type: 'FIXED_TERM', start_date: '', end_date: '', basic_salary: '', status: 'ACTIVE', note: '' };

const ContractsPage = () => {
  const { getAuthHeaders } = useAuth();
  const [items, setItems] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [toasts, setToasts] = useState([]);

  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [cr, er] = await Promise.all([
        fetch('/api/contracts', { headers: getAuthHeaders() }),
        fetch('/api/employees', { headers: getAuthHeaders() }),
      ]);
      if (cr.ok) setItems(await cr.json());
      if (er.ok) { const d = await er.json(); setEmployees(Array.isArray(d) ? d : d.items || []); }
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };
  useEffect(() => { fetchAll(); /* eslint-disable-next-line */ }, []);

  const save = async (e) => {
    e.preventDefault();
    const { form, id } = modal;
    const payload = { ...form, basic_salary: form.basic_salary || null, end_date: form.contract_type === 'INDEFINITE' ? null : form.end_date };
    const url = id ? `/api/contracts/${id}` : '/api/contracts';
    const res = await fetch(url, { method: id ? 'PUT' : 'POST', headers: getAuthHeaders(), body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setModal(null); fetchAll(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };

  const remove = async (c) => {
    if (!window.confirm(`Xóa hợp đồng ${c.contract_number || ''} của ${c.employee_name}?`)) return;
    const res = await fetch(`/api/contracts/${c.id}`, { method: 'DELETE', headers: getAuthHeaders() });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchAll();
  };

  const expiring = items.filter((c) => c.expiring_soon).length;
  const fmtDate = (d) => (d ? d.split('-').reverse().join('/') : '—');

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Hợp đồng lao động</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Hợp đồng lao động</h2>
          {expiring > 0 && <p style={{ color: 'var(--color-warning)', fontSize: 13, marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 }}><AlertTriangle size={15} /> {expiring} hợp đồng sắp hết hạn trong 30 ngày</p>}
        </div>
        <button className="btn btn--primary" onClick={() => setModal({ form: { ...empty } })}><Plus size={16} /> Thêm hợp đồng</button>
      </div>

      <div className="card card--no-hover">
        <div className="card__body" style={{ padding: 0 }}>
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div> : (
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr><th>Số HĐ</th><th>Nhân viên</th><th>Loại</th><th>Từ ngày</th><th>Đến ngày</th><th>Lương</th><th>Trạng thái</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                <tbody>
                  {items.map((c) => {
                    const sb = STATUS[c.status] || STATUS.ACTIVE;
                    return (
                      <tr key={c.id} style={c.expiring_soon ? { background: 'var(--color-warning-bg, #fff8e1)' } : undefined}>
                        <td><code>{c.contract_number || '—'}</code></td>
                        <td style={{ fontWeight: 600 }}>{c.employee_name}</td>
                        <td>{c.contract_type_label}</td>
                        <td style={{ whiteSpace: 'nowrap' }}>{fmtDate(c.start_date)}</td>
                        <td style={{ whiteSpace: 'nowrap' }}>
                          {c.end_date ? fmtDate(c.end_date) : <span style={{ color: 'var(--color-text-muted)' }}>Vô thời hạn</span>}
                          {c.expiring_soon && <span style={{ color: 'var(--color-warning)', fontSize: 11, display: 'block' }}>còn {c.days_left} ngày</span>}
                        </td>
                        <td>{fmtMoney(c.basic_salary)}</td>
                        <td><span className={`status-badge ${sb[0]}`}>{sb[1]}</span></td>
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: 12, marginRight: 6 }} onClick={() => setModal({ id: c.id, form: { employee_id: c.employee_id, contract_number: c.contract_number || '', contract_type: c.contract_type, start_date: c.start_date || '', end_date: c.end_date || '', basic_salary: c.basic_salary || '', status: c.status, note: c.note || '' } })}><Pencil size={13} /></button>
                          <button className="btn btn--danger" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => remove(c)}><Trash2 size={13} /></button>
                        </td>
                      </tr>
                    );
                  })}
                  {items.length === 0 && <tr><td colSpan={8} style={{ textAlign: 'center', padding: 32, color: 'var(--color-text-muted)' }}>Chưa có hợp đồng nào.</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {modal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 480 }}>
            <div className="modal__header">
              <h3 className="modal__title">{modal.id ? 'Sửa hợp đồng' : 'Thêm hợp đồng'}</h3>
              <button className="modal__close" onClick={() => setModal(null)}>&times;</button>
            </div>
            <form onSubmit={save}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Nhân viên</label>
                  <select className="input" value={modal.form.employee_id} onChange={(e) => setModal({ ...modal, form: { ...modal.form, employee_id: e.target.value } })} required disabled={!!modal.id}>
                    <option value="">— Chọn —</option>
                    {employees.map((e) => <option key={e.id} value={e.id}>{e.employee_id} · {e.full_name || `${e.first_name} ${e.last_name}`}</option>)}
                  </select>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="form-group"><label className="form-label">Số hợp đồng</label><input className="input" value={modal.form.contract_number} onChange={(e) => setModal({ ...modal, form: { ...modal.form, contract_number: e.target.value } })} /></div>
                  <div className="form-group"><label className="form-label form-label--required">Loại HĐ</label><select className="input" value={modal.form.contract_type} onChange={(e) => setModal({ ...modal, form: { ...modal.form, contract_type: e.target.value } })}>{TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}</select></div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="form-group"><label className="form-label form-label--required">Từ ngày</label><input type="date" className="input" value={modal.form.start_date} onChange={(e) => setModal({ ...modal, form: { ...modal.form, start_date: e.target.value } })} required /></div>
                  <div className="form-group"><label className="form-label">Đến ngày</label><input type="date" className="input" value={modal.form.end_date} disabled={modal.form.contract_type === 'INDEFINITE'} onChange={(e) => setModal({ ...modal, form: { ...modal.form, end_date: e.target.value } })} /></div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div className="form-group"><label className="form-label">Lương cơ bản</label><input type="number" className="input" value={modal.form.basic_salary} onChange={(e) => setModal({ ...modal, form: { ...modal.form, basic_salary: e.target.value } })} /></div>
                  <div className="form-group"><label className="form-label">Trạng thái</label><select className="input" value={modal.form.status} onChange={(e) => setModal({ ...modal, form: { ...modal.form, status: e.target.value } })}><option value="ACTIVE">Hiệu lực</option><option value="EXPIRED">Hết hạn</option><option value="TERMINATED">Chấm dứt</option></select></div>
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setModal(null)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContractsPage;
