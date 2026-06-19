import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Play, Eye, CheckCircle2, Lock, Loader2, CheckCircle, FileText, X } from 'lucide-react';

const fmtMoney = (v) => `${Number(v || 0).toLocaleString('vi-VN')} đ`;
const STATUS = {
  DRAFT: ['Nháp', 'status-badge--pending-hr'],
  CONFIRMED: ['Đã xác nhận', 'status-badge--warning'],
  LOCKED: ['Đã khóa', 'status-badge--approved'],
};

const PayrollPage = () => {
  const { getAuthHeaders } = useAuth();
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [detail, setDetail] = useState(null);

  const [toasts, setToasts] = useState([]);
  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/payroll', { headers: getAuthHeaders() });
      if (res.ok) setRuns(await res.json());
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchRuns(); /* eslint-disable-next-line */ }, []);

  const runPayroll = async () => {
    setRunning(true);
    try {
      const res = await fetch('/api/payroll/run', { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ month, year }) });
      const data = await res.json();
      if (res.ok) { showToast(`Đã tính lương cho ${data.payslip_count} nhân viên`); fetchRuns(); openDetail(data.id); }
      else showToast(data.error || 'Chạy lương thất bại.', 'error');
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setRunning(false); }
  };

  const openDetail = async (id) => {
    const res = await fetch(`/api/payroll/${id}`, { headers: getAuthHeaders() });
    if (res.ok) setDetail(await res.json());
  };

  const act = async (id, action) => {
    const res = await fetch(`/api/payroll/${id}/${action}`, { method: 'PUT', headers: getAuthHeaders() });
    const data = await res.json();
    if (res.ok) { showToast(data.message); fetchRuns(); if (detail?.id === id) openDetail(id); }
    else showToast(data.error || 'Thất bại.', 'error');
  };

  const downloadPdf = async (psId, label) => {
    const res = await fetch(`/api/payslips/${psId}/export-pdf`, { headers: getAuthHeaders() });
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `payslip_${label}.pdf`;
      document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url);
    } else { const d = await res.json(); showToast(d.error || 'Không tải được PDF', 'error'); }
  };

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Bảng lương</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Bảng lương</h2>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <select className="input" value={month} onChange={(e) => setMonth(e.target.value)} style={{ width: 100 }}>
            {[...Array(12).keys()].map((i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select className="input" value={year} onChange={(e) => setYear(e.target.value)} style={{ width: 110 }}>
            {[...Array(5).keys()].map((i) => { const y = new Date().getFullYear() - 2 + i; return <option key={y} value={y}>Năm {y}</option>; })}
          </select>
          <button className="btn btn--primary" onClick={runPayroll} disabled={running}>
            {running ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />} Chạy lương
          </button>
        </div>
      </div>

      <div className="card card--no-hover">
        <div className="card__body" style={{ padding: 0 }}>
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div> : (
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr><th>Kỳ lương</th><th>Trạng thái</th><th>Số phiếu</th><th>Tổng chi</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                <tbody>
                  {runs.map((r) => (
                    <tr key={r.id}>
                      <td style={{ fontWeight: 600 }}>Tháng {r.month}/{r.year}</td>
                      <td><span className={`status-badge ${STATUS[r.status][1]}`}>{STATUS[r.status][0]}</span></td>
                      <td>{r.payslip_count}</td>
                      <td style={{ fontWeight: 600 }}>{fmtMoney(r.total_amount)}</td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <button className="btn btn--secondary" style={{ padding: '4px 10px', fontSize: 12, marginRight: 6 }} onClick={() => openDetail(r.id)}><Eye size={13} /> Xem</button>
                        {r.status === 'DRAFT' && <button className="btn btn--primary" style={{ padding: '4px 10px', fontSize: 12, marginRight: 6 }} onClick={() => act(r.id, 'confirm')}><CheckCircle2 size={13} /> Xác nhận</button>}
                        {r.status === 'CONFIRMED' && <button className="btn btn--danger" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => act(r.id, 'lock')}><Lock size={13} /> Khóa</button>}
                      </td>
                    </tr>
                  ))}
                  {runs.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', padding: 32, color: 'var(--color-text-muted)' }}>Chưa có đợt lương nào. Chọn tháng/năm và nhấn "Chạy lương".</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {detail && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 900 }}>
            <div className="modal__header">
              <h3 className="modal__title">Bảng lương tháng {detail.month}/{detail.year} — <span className={`status-badge ${STATUS[detail.status][1]}`}>{STATUS[detail.status][0]}</span></h3>
              <button className="modal__close" onClick={() => setDetail(null)}><X size={18} /></button>
            </div>
            <div className="modal__body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <div className="table-responsive">
                <table className="table table--zebra">
                  <thead><tr><th>Nhân viên</th><th>Công</th><th>Lương CB</th><th>Phụ cấp</th><th>Tăng ca</th><th>BH</th><th>Thuế TNCN</th><th>Thực nhận</th><th></th></tr></thead>
                  <tbody>
                    {detail.payslips.map((p) => (
                      <tr key={p.id}>
                        <td style={{ fontWeight: 600 }}>{p.employee_name}</td>
                        <td>{p.total_work_days}/{p.standard_work_days}{p.total_leave_days ? ` (+${p.total_leave_days} phép)` : ''}</td>
                        <td>{fmtMoney(p.basic_salary)}</td>
                        <td style={{ color: 'var(--color-success)' }}>+{fmtMoney(p.total_allowances)}</td>
                        <td style={{ color: 'var(--color-success)' }}>{p.overtime_pay > 0 ? `+${fmtMoney(p.overtime_pay)}` : '—'}</td>
                        <td style={{ color: 'var(--color-error)' }}>−{fmtMoney(p.total_deductions)}</td>
                        <td style={{ color: 'var(--color-error)' }}>{p.personal_income_tax > 0 ? `−${fmtMoney(p.personal_income_tax)}` : '—'}</td>
                        <td style={{ fontWeight: 700, color: 'var(--color-primary-dark)' }}>{fmtMoney(p.net_salary)}</td>
                        <td><button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => downloadPdf(p.id, `${p.employee_code || p.employee_id}_${detail.month}_${detail.year}`)}><FileText size={13} /> PDF</button></td>
                      </tr>
                    ))}
                    {detail.payslips.length === 0 && <tr><td colSpan={9} style={{ textAlign: 'center', padding: 24, color: 'var(--color-text-muted)' }}>Không có phiếu lương. Hãy chắc chắn nhân viên đã được gán mức lương.</td></tr>}
                  </tbody>
                </table>
              </div>
              <div style={{ textAlign: 'right', marginTop: 12, fontSize: 16, fontWeight: 700 }}>
                Tổng chi: <span style={{ color: 'var(--color-primary)' }}>{fmtMoney(detail.total_amount)}</span>
              </div>
            </div>
            <div className="modal__footer">
              {detail.status === 'DRAFT' && <button className="btn btn--primary" onClick={() => act(detail.id, 'confirm')}><CheckCircle2 size={16} /> Xác nhận</button>}
              {detail.status === 'CONFIRMED' && <button className="btn btn--danger" onClick={() => act(detail.id, 'lock')}><Lock size={16} /> Khóa đợt</button>}
              <button className="btn btn--secondary" onClick={() => setDetail(null)}>Đóng</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PayrollPage;
