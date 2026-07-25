import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Layers, PlusCircle, MinusCircle, UserCog, Plus, Pencil, Trash2, Loader2, CheckCircle } from 'lucide-react';

const fmtMoney = (v) => (v == null ? '—' : `${Number(v).toLocaleString('vi-VN')} đ`);

const SalaryConfigPage = () => {
  const { authFetch } = useAuth();
  const [tab, setTab] = useState('structures');
  const [loading, setLoading] = useState(true);

  const [structures, setStructures] = useState([]);
  const [allowances, setAllowances] = useState([]);
  const [deductions, setDeductions] = useState([]);
  const [empSalaries, setEmpSalaries] = useState([]);

  const [modal, setModal] = useState(null); // {kind, form, id?}

  const [toasts, setToasts] = useState([]);
  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [s, a, d, e] = await Promise.all([
        authFetch('/api/salary-structures'),
        authFetch('/api/salary-allowances'),
        authFetch('/api/salary-deductions'),
        authFetch('/api/employee-salaries'),
      ]);
      if (s.ok) setStructures(await s.json());
      if (a.ok) setAllowances(await a.json());
      if (d.ok) setDeductions(await d.json());
      if (e.ok) setEmpSalaries(await e.json());
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAll(); /* eslint-disable-next-line */ }, []);

  const save = async (e) => {
    e.preventDefault();
    const { kind, form, id } = modal;
    let url, payload;
    if (kind === 'structure') { url = '/api/salary-structures'; payload = { name: form.name, basic_salary: Number(form.basic_salary) || 0, description: form.description }; }
    else if (kind === 'allowance') { url = '/api/salary-allowances'; payload = { name: form.name, type: form.type, default_amount: Number(form.default_amount) || 0 }; }
    else if (kind === 'deduction') { url = '/api/salary-deductions'; payload = { name: form.name, type: form.type, default_amount: Number(form.default_amount) || 0 }; }
    else if (kind === 'assign') {
      url = '/api/employee-salaries';
      payload = { employee_id: form.employee_id, basic_salary: Number(form.basic_salary), effective_date: form.effective_date, note: form.note };
    }
    const method = id ? 'PUT' : 'POST';
    const finalUrl = id ? `${url}/${id}` : url;
    const res = await authFetch(finalUrl, { method, body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setModal(null); fetchAll(); }
    else showToast(data.error || 'Lưu thất bại.', 'error');
  };

  const del = async (kind, id) => {
    const urls = { structure: 'salary-structures', allowance: 'salary-allowances', deduction: 'salary-deductions' };
    if (!window.confirm('Xóa mục này?')) return;
    const res = await authFetch(`/api/${urls[kind]}/${id}`, { method: 'DELETE' });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) fetchAll();
  };

  const TABS = [
    ['structures', 'Cấu trúc lương', Layers],
    ['allowances', 'Phụ cấp', PlusCircle],
    ['deductions', 'Khấu trừ', MinusCircle],
    ['assign', 'Gán lương NV', UserCog],
  ];

  const amountTable = (rows, kind) => (
    <table className="table table--zebra">
      <thead><tr><th>Tên</th><th>Loại</th><th>Giá trị</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id}>
            <td style={{ fontWeight: 600 }}>{r.name}</td>
            <td>{r.type === 'PERCENT' ? '% lương CB' : 'Cố định'}</td>
            <td>{r.type === 'PERCENT' ? `${r.default_amount}%` : fmtMoney(r.default_amount)}</td>
            <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
              <button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: 12, marginRight: 6 }} onClick={() => setModal({ kind, id: r.id, form: { ...r } })}><Pencil size={13} /></button>
              <button className="btn btn--danger" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => del(kind, r.id)}><Trash2 size={13} /></button>
            </td>
          </tr>
        ))}
        {rows.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', padding: 28, color: 'var(--color-text-muted)' }}>Chưa có dữ liệu.</td></tr>}
      </tbody>
    </table>
  );

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Cấu hình lương</span></div>
      <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)', marginBottom: 16 }}>Cấu hình lương</h2>

      <div className="leave-tabs">
        {TABS.map(([k, label, Icon]) => (
          <button key={k} className={`leave-tabs__tab ${tab === k ? 'leave-tabs__tab--active' : ''}`} onClick={() => setTab(k)}>
            <Icon size={16} style={{ marginRight: 6, verticalAlign: 'middle' }} />{label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div></div>
      ) : (
        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title">{TABS.find((t) => t[0] === tab)[1]}</h3>
            {tab === 'structures' && <button className="btn btn--primary" onClick={() => setModal({ kind: 'structure', form: { name: '', basic_salary: '', description: '' } })}><Plus size={16} /> Thêm</button>}
            {tab === 'allowances' && <button className="btn btn--primary" onClick={() => setModal({ kind: 'allowance', form: { name: '', type: 'FIXED', default_amount: '' } })}><Plus size={16} /> Thêm</button>}
            {tab === 'deductions' && <button className="btn btn--primary" onClick={() => setModal({ kind: 'deduction', form: { name: '', type: 'PERCENT', default_amount: '' } })}><Plus size={16} /> Thêm</button>}
          </div>
          <div className="card__body" style={{ padding: 0 }}>
            <div className="table-responsive">
              {tab === 'structures' && (
                <table className="table table--zebra">
                  <thead><tr><th>Tên</th><th>Lương cơ bản</th><th>Ghi chú</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                  <tbody>
                    {structures.map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontWeight: 600 }}>{r.name}</td>
                        <td>{fmtMoney(r.basic_salary)}</td>
                        <td style={{ color: 'var(--color-text-muted)' }}>{r.description}</td>
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: 12, marginRight: 6 }} onClick={() => setModal({ kind: 'structure', id: r.id, form: { ...r } })}><Pencil size={13} /></button>
                          <button className="btn btn--danger" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => del('structure', r.id)}><Trash2 size={13} /></button>
                        </td>
                      </tr>
                    ))}
                    {structures.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', padding: 28, color: 'var(--color-text-muted)' }}>Chưa có cấu trúc lương.</td></tr>}
                  </tbody>
                </table>
              )}
              {tab === 'allowances' && amountTable(allowances, 'allowance')}
              {tab === 'deductions' && amountTable(deductions, 'deduction')}
              {tab === 'assign' && (
                <table className="table table--zebra">
                  <thead><tr><th>Mã NV</th><th>Nhân viên</th><th>Lương hiện tại</th><th>Hiệu lực từ</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                  <tbody>
                    {empSalaries.map((r) => (
                      <tr key={r.employee_id}>
                        <td>{r.employee_code || '—'}</td>
                        <td style={{ fontWeight: 600 }}>{r.employee_name}</td>
                        <td>{r.current_salary != null ? fmtMoney(r.current_salary) : <span className="status-badge status-badge--rejected">Chưa gán</span>}</td>
                        <td>{r.effective_date ? new Date(r.effective_date).toLocaleDateString('vi-VN') : '—'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="btn btn--primary" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => setModal({ kind: 'assign', form: { employee_id: r.employee_id, basic_salary: r.current_salary || '', effective_date: new Date().toISOString().split('T')[0], note: '' } })}>Gán lương</button>
                        </td>
                      </tr>
                    ))}
                    {empSalaries.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', padding: 28, color: 'var(--color-text-muted)' }}>Chưa có nhân viên đang làm việc.</td></tr>}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {modal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 440 }}>
            <div className="modal__header">
              <h3 className="modal__title">{modal.id ? 'Sửa' : 'Thêm'} {{ structure: 'cấu trúc lương', allowance: 'phụ cấp', deduction: 'khấu trừ', assign: 'mức lương' }[modal.kind]}</h3>
              <button className="modal__close" onClick={() => setModal(null)}>&times;</button>
            </div>
            <form onSubmit={save}>
              <div className="modal__body">
                {modal.kind !== 'assign' && (
                  <div className="form-group">
                    <label className="form-label form-label--required">Tên</label>
                    <input className="input" value={modal.form.name} onChange={(e) => setModal({ ...modal, form: { ...modal.form, name: e.target.value } })} required />
                  </div>
                )}
                {modal.kind === 'structure' && (
                  <>
                    <div className="form-group"><label className="form-label">Lương cơ bản</label><input type="number" className="input" value={modal.form.basic_salary} onChange={(e) => setModal({ ...modal, form: { ...modal.form, basic_salary: e.target.value } })} /></div>
                    <div className="form-group"><label className="form-label">Ghi chú</label><input className="input" value={modal.form.description || ''} onChange={(e) => setModal({ ...modal, form: { ...modal.form, description: e.target.value } })} /></div>
                  </>
                )}
                {(modal.kind === 'allowance' || modal.kind === 'deduction') && (
                  <>
                    <div className="form-group">
                      <label className="form-label">Loại</label>
                      <select className="input" value={modal.form.type} onChange={(e) => setModal({ ...modal, form: { ...modal.form, type: e.target.value } })}>
                        <option value="FIXED">Cố định (đồng)</option>
                        <option value="PERCENT">Phần trăm lương cơ bản (%)</option>
                      </select>
                    </div>
                    <div className="form-group"><label className="form-label form-label--required">{modal.form.type === 'PERCENT' ? 'Phần trăm (%)' : 'Số tiền (đồng)'}</label><input type="number" step="0.1" className="input" value={modal.form.default_amount} onChange={(e) => setModal({ ...modal, form: { ...modal.form, default_amount: e.target.value } })} required /></div>
                  </>
                )}
                {modal.kind === 'assign' && (
                  <>
                    <div className="form-group"><label className="form-label form-label--required">Lương cơ bản (đồng)</label><input type="number" className="input" value={modal.form.basic_salary} onChange={(e) => setModal({ ...modal, form: { ...modal.form, basic_salary: e.target.value } })} required /></div>
                    <div className="form-group"><label className="form-label form-label--required">Hiệu lực từ ngày</label><input type="date" className="input" value={modal.form.effective_date} onChange={(e) => setModal({ ...modal, form: { ...modal.form, effective_date: e.target.value } })} required /></div>
                    <div className="form-group"><label className="form-label">Lý do/Ghi chú</label><input className="input" value={modal.form.note || ''} onChange={(e) => setModal({ ...modal, form: { ...modal.form, note: e.target.value } })} /></div>
                  </>
                )}
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

export default SalaryConfigPage;
