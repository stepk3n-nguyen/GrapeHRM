import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Loader2, FileText, Download } from 'lucide-react';

const fmtMoney = (v) => `${Number(v || 0).toLocaleString('vi-VN')} đ`;

const MyPayslipPage = () => {
  const { authFetch } = useAuth();
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [slip, setSlip] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchSlip = async () => {
    setLoading(true); setError(''); setSlip(null);
    try {
      const res = await authFetch(`/api/payslips/me?month=${month}&year=${year}`);
      const data = await res.json();
      if (res.ok) setSlip(data);
      else setError(data.error || 'Không có dữ liệu.');
    } catch { setError('Lỗi kết nối.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchSlip(); /* eslint-disable-next-line */ }, [month, year]);

  const downloadPdf = async () => {
    const res = await authFetch(`/api/payslips/${slip.id}/export-pdf`);
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `payslip_${month}_${year}.pdf`;
      document.body.appendChild(a); a.click(); window.URL.revokeObjectURL(url);
    }
  };

  const prorated = slip ? slip.basic_salary * Math.min((slip.total_work_days + slip.total_leave_days) / (slip.standard_work_days || 1), 1) : 0;

  return (
    <div className="fade-in">
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Phiếu lương</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Phiếu lương của tôi</h2>
        <div style={{ display: 'flex', gap: 10 }}>
          <select className="input" value={month} onChange={(e) => setMonth(e.target.value)} style={{ width: 135 }}>
            {[...Array(12).keys()].map((i) => <option key={i + 1} value={i + 1}>Tháng {i + 1}</option>)}
          </select>
          <select className="input" value={year} onChange={(e) => setYear(e.target.value)} style={{ width: 130 }}>
            {[...Array(5).keys()].map((i) => { const y = new Date().getFullYear() - 2 + i; return <option key={y} value={y}>Năm {y}</option>; })}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div></div>
      ) : error ? (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}><FileText size={40} style={{ marginBottom: 12, opacity: 0.4 }} /><div>{error}</div></div></div>
      ) : slip ? (
        <div className="card" style={{ maxWidth: 600, margin: '0 auto' }}>
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title"><FileText size={18} /><span>Phiếu lương tháng {month}/{year}</span></h3>
            <button className="btn btn--secondary" onClick={downloadPdf}><Download size={16} /> Tải PDF</button>
          </div>
          <div className="card__body">
            <Row label={`Ngày công (chuẩn ${slip.standard_work_days})`} value={`${slip.total_work_days}${slip.total_leave_days ? ` + ${slip.total_leave_days} phép` : ''}`} />
            {slip.overtime_hours > 0 && <Row label="Giờ tăng ca" value={`${slip.overtime_hours} giờ`} />}
            <Row label="Lương cơ bản (theo ngày công)" value={fmtMoney(prorated)} />
            <div style={{ borderTop: '1px dashed var(--color-border)', margin: '8px 0' }} />
            {slip.items.filter((i) => i.item_type === 'ALLOWANCE').map((i, k) => <Row key={`a${k}`} label={`(+) ${i.name}`} value={fmtMoney(i.amount)} color="var(--color-success)" />)}
            {slip.items.filter((i) => i.item_type === 'DEDUCTION').map((i, k) => <Row key={`d${k}`} label={`(−) ${i.name}`} value={`−${fmtMoney(i.amount)}`} color="var(--color-error)" />)}
            <div style={{ borderTop: '1px dashed var(--color-border)', margin: '8px 0' }} />
            <Row label="Tổng thu nhập (gross)" value={fmtMoney(slip.gross_salary)} />
            <Row label={`Thu nhập chịu thuế (${slip.num_dependents} người phụ thuộc)`} value={fmtMoney(slip.taxable_income)} />
            <div style={{ borderTop: '2px solid var(--color-border)', margin: '12px 0 8px' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 700, fontSize: 16 }}>Thực nhận</span>
              <span style={{ fontWeight: 700, fontSize: 22, color: 'var(--color-primary)' }}>{fmtMoney(slip.net_salary)}</span>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

const Row = ({ label, value, color }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', fontSize: 14 }}>
    <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
    <span style={{ fontWeight: 500, color: color || 'var(--color-text-primary)' }}>{value}</span>
  </div>
);

export default MyPayslipPage;
