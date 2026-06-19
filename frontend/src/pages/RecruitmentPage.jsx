import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Briefcase, Plus, Loader2, CheckCircle, UserPlus, Trash2, UserCheck } from 'lucide-react';

const STAGES = [
  { value: 'APPLIED', label: 'Nộp hồ sơ' },
  { value: 'INTERVIEW', label: 'Phỏng vấn' },
  { value: 'OFFERED', label: 'Mời nhận việc' },
  { value: 'HIRED', label: 'Trúng tuyển' },
  { value: 'REJECTED', label: 'Đã loại' },
];
const STAGE_CLS = { APPLIED: 'badge--info', INTERVIEW: 'badge--warning', OFFERED: 'badge--info', HIRED: 'badge--success', REJECTED: 'badge--danger' };

const RecruitmentPage = () => {
  const { getAuthHeaders } = useAuth();
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [selJob, setSelJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [jobModal, setJobModal] = useState(null);
  const [candModal, setCandModal] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [toasts, setToasts] = useState([]);

  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const [jr, dr] = await Promise.all([
        fetch('/api/job-postings', { headers: getAuthHeaders() }),
        fetch('/api/departments', { headers: getAuthHeaders() }),
      ]);
      if (jr.ok) { const d = await jr.json(); setJobs(d); if (!selJob && d.length) setSelJob(d[0].id); }
      if (dr.ok) { const d = await dr.json(); setDepartments(Array.isArray(d) ? d : d.items || []); }
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };
  const fetchCandidates = async (jobId) => {
    if (!jobId) { setCandidates([]); return; }
    const res = await fetch(`/api/candidates?job_posting_id=${jobId}`, { headers: getAuthHeaders() });
    if (res.ok) setCandidates(await res.json());
  };
  useEffect(() => { fetchJobs(); /* eslint-disable-next-line */ }, []);
  useEffect(() => { fetchCandidates(selJob); /* eslint-disable-next-line */ }, [selJob]);

  const saveJob = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/job-postings', { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(jobModal.form) });
    const data = await res.json();
    if (res.ok) { showToast(data.message); setJobModal(null); fetchJobs(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };
  const saveCand = async (e) => {
    e.preventDefault();
    const res = await fetch('/api/candidates', { method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ ...candModal.form, job_posting_id: selJob }) });
    const data = await res.json();
    if (res.ok) { showToast(data.message); setCandModal(null); fetchCandidates(selJob); fetchJobs(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };
  const moveStage = async (c, stage) => {
    const res = await fetch(`/api/candidates/${c.id}/stage`, { method: 'PUT', headers: getAuthHeaders(), body: JSON.stringify({ stage }) });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) { fetchCandidates(selJob); fetchJobs(); }
  };
  const hire = async (c) => {
    if (!window.confirm(`Tuyển "${c.full_name}" thành nhân viên chính thức?`)) return;
    const res = await fetch(`/api/candidates/${c.id}/hire`, { method: 'POST', headers: getAuthHeaders() });
    const data = await res.json();
    showToast(res.ok ? data.message : data.error, res.ok ? 'success' : 'error');
    if (res.ok) { fetchCandidates(selJob); fetchJobs(); }
  };
  const delCand = async (c) => {
    if (!window.confirm(`Xóa ứng viên "${c.full_name}"?`)) return;
    const res = await fetch(`/api/candidates/${c.id}`, { method: 'DELETE', headers: getAuthHeaders() });
    if (res.ok) { showToast('Đã xóa'); fetchCandidates(selJob); fetchJobs(); }
  };

  const job = jobs.find((j) => j.id === selJob);

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Tuyển dụng</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Tuyển dụng</h2>
        <button className="btn btn--primary" onClick={() => setJobModal({ form: { title: '', department_id: '', quantity: 1, description: '', status: 'OPEN' } })}><Plus size={16} /> Tạo tin tuyển dụng</button>
      </div>

      {loading ? <div className="card card--no-hover"><div className="card__body" style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div></div> : (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16, alignItems: 'start' }}>
          {/* Danh sách tin */}
          <div className="card card--no-hover">
            <div className="card__header"><h3 className="card__title"><Briefcase size={18} /><span>Tin ({jobs.length})</span></h3></div>
            <div className="card__body" style={{ padding: 8 }}>
              {jobs.map((j) => (
                <div key={j.id} onClick={() => setSelJob(j.id)} style={{ padding: 12, borderRadius: 8, cursor: 'pointer', marginBottom: 6, background: selJob === j.id ? 'var(--color-primary-light, #eef2ff)' : 'transparent', border: '1px solid var(--color-border)' }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{j.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 3 }}>{j.department_name || 'Chưa rõ phòng ban'} · {j.total_candidates} ứng viên · {j.hired_count}/{j.quantity} tuyển</div>
                  <span className={`badge ${j.status === 'OPEN' ? 'badge--success' : 'badge--info'}`} style={{ marginTop: 6, display: 'inline-block' }}>{j.status === 'OPEN' ? 'Đang tuyển' : 'Đã đóng'}</span>
                </div>
              ))}
              {jobs.length === 0 && <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 13 }}>Chưa có tin tuyển dụng.</div>}
            </div>
          </div>

          {/* Ứng viên của tin được chọn */}
          <div className="card card--no-hover">
            <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 className="card__title"><span>Ứng viên {job ? `— ${job.title}` : ''}</span></h3>
              {job && <button className="btn btn--secondary" onClick={() => setCandModal({ form: { full_name: '', email: '', phone: '', stage: 'APPLIED', note: '' } })}><UserPlus size={15} /> Thêm ứng viên</button>}
            </div>
            <div className="card__body" style={{ padding: 0 }}>
              <div className="table-responsive">
                <table className="table table--zebra">
                  <thead><tr><th>Họ tên</th><th>Liên hệ</th><th>Giai đoạn</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                  <tbody>
                    {candidates.map((c) => (
                      <tr key={c.id}>
                        <td style={{ fontWeight: 600 }}>{c.full_name}</td>
                        <td style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{c.email || ''}{c.phone ? ` · ${c.phone}` : ''}</td>
                        <td>
                          <select className="input" style={{ padding: '4px 8px', fontSize: 12, width: 'auto' }} value={c.stage} onChange={(e) => moveStage(c, e.target.value)} disabled={c.stage === 'HIRED'}>
                            {STAGES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                          </select>
                        </td>
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          {c.stage === 'OFFERED' && <button className="btn btn--primary" style={{ padding: '4px 9px', fontSize: 12, marginRight: 6 }} onClick={() => hire(c)}><UserCheck size={13} /> Tuyển</button>}
                          {c.stage === 'HIRED' ? <span className={`badge ${STAGE_CLS.HIRED}`}>Đã tuyển</span> : <button className="btn btn--danger" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => delCand(c)}><Trash2 size={13} /></button>}
                        </td>
                      </tr>
                    ))}
                    {candidates.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', padding: 28, color: 'var(--color-text-muted)' }}>{job ? 'Chưa có ứng viên cho tin này.' : 'Chọn một tin tuyển dụng.'}</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {jobModal && (
        <div className="modal-overlay"><div className="modal" style={{ maxWidth: 480 }}>
          <div className="modal__header"><h3 className="modal__title">Tạo tin tuyển dụng</h3><button className="modal__close" onClick={() => setJobModal(null)}>&times;</button></div>
          <form onSubmit={saveJob}><div className="modal__body">
            <div className="form-group"><label className="form-label form-label--required">Tiêu đề</label><input className="input" value={jobModal.form.title} onChange={(e) => setJobModal({ form: { ...jobModal.form, title: e.target.value } })} required /></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 100px', gap: 12 }}>
              <div className="form-group"><label className="form-label">Phòng ban</label><select className="input" value={jobModal.form.department_id} onChange={(e) => setJobModal({ form: { ...jobModal.form, department_id: e.target.value } })}><option value="">—</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>
              <div className="form-group"><label className="form-label">Số lượng</label><input type="number" min="1" className="input" value={jobModal.form.quantity} onChange={(e) => setJobModal({ form: { ...jobModal.form, quantity: e.target.value } })} /></div>
            </div>
            <div className="form-group"><label className="form-label">Mô tả</label><textarea className="input" rows={3} value={jobModal.form.description} onChange={(e) => setJobModal({ form: { ...jobModal.form, description: e.target.value } })} /></div>
          </div><div className="modal__footer"><button type="button" className="btn btn--secondary" onClick={() => setJobModal(null)}>Hủy</button><button type="submit" className="btn btn--primary">Lưu</button></div></form>
        </div></div>
      )}

      {candModal && (
        <div className="modal-overlay"><div className="modal" style={{ maxWidth: 440 }}>
          <div className="modal__header"><h3 className="modal__title">Thêm ứng viên</h3><button className="modal__close" onClick={() => setCandModal(null)}>&times;</button></div>
          <form onSubmit={saveCand}><div className="modal__body">
            <div className="form-group"><label className="form-label form-label--required">Họ tên</label><input className="input" value={candModal.form.full_name} onChange={(e) => setCandModal({ form: { ...candModal.form, full_name: e.target.value } })} required /></div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="form-group"><label className="form-label">Email</label><input type="email" className="input" value={candModal.form.email} onChange={(e) => setCandModal({ form: { ...candModal.form, email: e.target.value } })} /></div>
              <div className="form-group"><label className="form-label">Điện thoại</label><input className="input" value={candModal.form.phone} onChange={(e) => setCandModal({ form: { ...candModal.form, phone: e.target.value } })} /></div>
            </div>
          </div><div className="modal__footer"><button type="button" className="btn btn--secondary" onClick={() => setCandModal(null)}>Hủy</button><button type="submit" className="btn btn--primary">Lưu</button></div></form>
        </div></div>
      )}
    </div>
  );
};

export default RecruitmentPage;
