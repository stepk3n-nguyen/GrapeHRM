import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Target, Plus, Loader2, CheckCircle, Trash2, Star } from 'lucide-react';

const scoreColor = (s) => (s >= 8 ? 'var(--color-success)' : s >= 6.5 ? 'var(--color-warning)' : 'var(--color-error)');

const PerformancePage = () => {
  const { user, getAuthHeaders } = useAuth();
  const isHR = ['admin', 'super_admin', 'hr_manager'].includes(user?.role);

  const [cycles, setCycles] = useState([]);
  const [selCycle, setSelCycle] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [cycleModal, setCycleModal] = useState(null);
  const [reviewModal, setReviewModal] = useState(null);
  const [toasts, setToasts] = useState([]);

  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchCycles = async () => {
    setLoading(true);
    try {
      const reqs = [fetch('/api/review-cycles', { headers: getAuthHeaders() })];
      if (isHR) reqs.push(fetch('/api/employees', { headers: getAuthHeaders() }));
      const [cr, er] = await Promise.all(reqs);
      if (cr.ok) { const d = await cr.json(); setCycles(d); if (!selCycle && d.length) setSelCycle(d[0].id); }
      if (er && er.ok) { const d = await er.json(); setEmployees(Array.isArray(d) ? d : d.items || []); }
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };
  const fetchReviews = async (cycleId) => {
    const url = cycleId ? `/api/performance-reviews?cycle_id=${cycleId}` : '/api/performance-reviews';
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) setReviews(await res.json());
  };
  useEffect(() => { fetchCycles(); /* eslint-disable-next-line */ }, []);
  useEffect(() => { if (isHR) fetchReviews(selCycle); else fetchReviews(null); /* eslint-disable-next-line */ }, [selCycle]);

  const saveCycle = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/review-cycles', { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(cycleModal.form) });
    const data = await res.json();
    if (res.ok) { showToast(data.message); setCycleModal(null); fetchCycles(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };

  const openReviewModal = () => setReviewModal({ form: { employee_id: '', comments: '', status: 'SUBMITTED' }, scores: [{ criterion: 'Chất lượng công việc', score: 8, weight: 2 }, { criterion: 'Tiến độ', score: 8, weight: 1 }, { criterion: 'Thái độ', score: 8, weight: 1 }] });
  const setScore = (i, field, val) => setReviewModal((m) => { const s = [...m.scores]; s[i] = { ...s[i], [field]: val }; return { ...m, scores: s }; });
  const addCriterion = () => setReviewModal((m) => ({ ...m, scores: [...m.scores, { criterion: '', score: 8, weight: 1 }] }));
  const delCriterion = (i) => setReviewModal((m) => ({ ...m, scores: m.scores.filter((_, k) => k !== i) }));

  const saveReview = async (e) => {
    e.preventDefault();
    const payload = { ...reviewModal.form, cycle_id: selCycle, scores: reviewModal.scores.filter((s) => s.criterion.trim()).map((s) => ({ criterion: s.criterion, score: Number(s.score), weight: Number(s.weight) })) };
    const res = await fetch('/api/performance-reviews', { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok) { showToast(data.message); setReviewModal(null); fetchReviews(selCycle); fetchCycles(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };
  const delReview = async (r) => {
    if (!window.confirm(`Xóa phiếu đánh giá của ${r.employee_name}?`)) return;
    const res = await fetch(`/api/performance-reviews/${r.id}`, { method: 'DELETE', headers: getAuthHeaders() });
    if (res.ok) { showToast('Đã xóa'); fetchReviews(selCycle); fetchCycles(); }
  };

  const previewAvg = reviewModal ? (() => {
    const valid = reviewModal.scores.filter((s) => s.criterion.trim());
    const tw = valid.reduce((a, s) => a + Number(s.weight || 1), 0);
    return tw ? (valid.reduce((a, s) => a + Number(s.score) * Number(s.weight || 1), 0) / tw).toFixed(1) : '—';
  })() : null;

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Đánh giá hiệu suất</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Đánh giá hiệu suất</h2>
        {isHR && <button className="btn btn--primary" onClick={() => setCycleModal({ form: { name: '', start_date: '', end_date: '', status: 'OPEN' } })}><Plus size={16} /> Tạo kỳ đánh giá</button>}
      </div>

      {loading ? <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div></div> : !isHR ? (
        <div className="card card--no-hover"><div className="card__body" style={{ padding: 0 }}>
          <ReviewTable reviews={reviews} isHR={false} />
        </div></div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 16, alignItems: 'start' }}>
          <div className="card card--no-hover">
            <div className="card__header"><h3 className="card__title"><Target size={18} /><span>Kỳ ({cycles.length})</span></h3></div>
            <div className="card__body" style={{ padding: 8 }}>
              {cycles.map((c) => (
                <div key={c.id} onClick={() => setSelCycle(c.id)} style={{ padding: 12, borderRadius: 8, cursor: 'pointer', marginBottom: 6, background: selCycle === c.id ? 'var(--color-primary-light, #eef2ff)' : 'transparent', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{c.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 3 }}>{c.review_count} phiếu · {c.status === 'OPEN' ? 'Đang mở' : 'Đã đóng'}</div>
                </div>
              ))}
              {cycles.length === 0 && <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 13 }}>Chưa có kỳ đánh giá.</div>}
            </div>
          </div>

          <div className="card card--no-hover">
            <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 className="card__title"><span>Phiếu đánh giá</span></h3>
              {selCycle && <button className="btn btn--secondary" onClick={openReviewModal}><Plus size={15} /> Đánh giá nhân viên</button>}
            </div>
            <div className="card__body" style={{ padding: 0 }}><ReviewTable reviews={reviews} isHR onDelete={delReview} /></div>
          </div>
        </div>
      )}

      {cycleModal && (
        <div className="modal-overlay"><div className="modal" style={{ maxWidth: 440 }}>
          <div className="modal__header"><h3 className="modal__title">Tạo kỳ đánh giá</h3><button className="modal__close" onClick={() => setCycleModal(null)}>&times;</button></div>
          <form onSubmit={saveCycle}><div className="modal__body">
            <div className="form-group"><label className="form-label form-label--required">Tên kỳ</label><input className="input" placeholder="vd: Đánh giá Quý 3/2026" value={cycleModal.form.name} onChange={(e) => setCycleModal({ form: { ...cycleModal.form, name: e.target.value } })} required /></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group"><label className="form-label">Từ ngày</label><input type="date" className="input" value={cycleModal.form.start_date} onChange={(e) => setCycleModal({ form: { ...cycleModal.form, start_date: e.target.value } })} /></div>
              <div className="form-group"><label className="form-label">Đến ngày</label><input type="date" className="input" value={cycleModal.form.end_date} onChange={(e) => setCycleModal({ form: { ...cycleModal.form, end_date: e.target.value } })} /></div>
            </div>
          </div><div className="modal__footer"><button type="button" className="btn btn--secondary" onClick={() => setCycleModal(null)}>Hủy</button><button type="submit" className="btn btn--primary">Lưu</button></div></form>
        </div></div>
      )}

      {reviewModal && (
        <div className="modal-overlay"><div className="modal" style={{ maxWidth: 540 }}>
          <div className="modal__header"><h3 className="modal__title">Đánh giá nhân viên</h3><button className="modal__close" onClick={() => setReviewModal(null)}>&times;</button></div>
          <form onSubmit={saveReview}><div className="modal__body">
            <div className="form-group"><label className="form-label form-label--required">Nhân viên</label>
              <select className="input" value={reviewModal.form.employee_id} onChange={(e) => setReviewModal({ ...reviewModal, form: { ...reviewModal.form, employee_id: e.target.value } })} required>
                <option value="">— Chọn —</option>
                {employees.map((e) => <option key={e.id} value={e.id}>{e.employee_id} · {e.full_name || `${e.first_name} ${e.last_name}`}</option>)}
              </select>
            </div>
            <label className="form-label">Tiêu chí (điểm 0–10 · trọng số)</label>
            {reviewModal.scores.map((s, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 70px 70px 32px', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <input className="input" placeholder="Tiêu chí" value={s.criterion} onChange={(e) => setScore(i, 'criterion', e.target.value)} />
                <input type="number" min="0" max="10" step="0.5" className="input" value={s.score} onChange={(e) => setScore(i, 'score', e.target.value)} />
                <input type="number" min="1" className="input" value={s.weight} onChange={(e) => setScore(i, 'weight', e.target.value)} />
                <button type="button" className="btn btn--danger" style={{ padding: '6px 8px' }} onClick={() => delCriterion(i)}><Trash2 size={13} /></button>
              </div>
            ))}
            <button type="button" className="btn btn--secondary" style={{ fontSize: 12, padding: '5px 10px' }} onClick={addCriterion}><Plus size={13} /> Thêm tiêu chí</button>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, padding: '8px 0' }}>
              <span style={{ fontWeight: 500 }}>Điểm tổng (theo trọng số)</span>
              <span style={{ fontWeight: 700, fontSize: 20, color: scoreColor(Number(previewAvg) || 0) }}>{previewAvg}</span>
            </div>
            <div className="form-group"><label className="form-label">Nhận xét</label><textarea className="input" rows={2} value={reviewModal.form.comments} onChange={(e) => setReviewModal({ ...reviewModal, form: { ...reviewModal.form, comments: e.target.value } })} /></div>
          </div><div className="modal__footer"><button type="button" className="btn btn--secondary" onClick={() => setReviewModal(null)}>Hủy</button><button type="submit" className="btn btn--primary">Lưu phiếu</button></div></form>
        </div></div>
      )}
    </div>
  );
};

const ReviewTable = ({ reviews, isHR, onDelete }) => (
  <div className="table-responsive">
    <table className="table table--zebra">
      <thead><tr>{isHR && <th>Nhân viên</th>}{!isHR && <th>Kỳ đánh giá</th>}<th>Tiêu chí</th><th>Điểm tổng</th><th>Nhận xét</th>{isHR && <th></th>}</tr></thead>
      <tbody>
        {reviews.map((r) => (
          <tr key={r.id}>
            {isHR ? <td style={{ fontWeight: 600 }}>{r.employee_name}</td> : <td style={{ fontWeight: 600 }}>{r.cycle_name}</td>}
            <td style={{ fontSize: 12 }}>{(r.scores || []).map((s) => `${s.criterion}: ${s.score}`).join(' · ') || '—'}</td>
            <td><span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 700, color: scoreColor(r.overall_score || 0) }}><Star size={13} />{r.overall_score ?? '—'}</span></td>
            <td style={{ fontSize: 13, color: 'var(--color-text-muted)', maxWidth: 220 }}>{r.comments || '—'}</td>
            {isHR && <td style={{ textAlign: 'right' }}><button className="btn btn--danger" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => onDelete(r)}><Trash2 size={13} /></button></td>}
          </tr>
        ))}
        {reviews.length === 0 && <tr><td colSpan={isHR ? 5 : 4} style={{ textAlign: 'center', padding: 28, color: 'var(--color-text-muted)' }}>Chưa có phiếu đánh giá.</td></tr>}
      </tbody>
    </table>
  </div>
);

export default PerformancePage;
