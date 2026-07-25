import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Building2, Plus, Pencil, Lock, Unlock, Loader2, CheckCircle, Users } from 'lucide-react';

const PLAN_BADGE = { FREE: 'badge--info', PRO: 'badge--success', ENTERPRISE: 'badge--warning' };

const SuperAdminPage = () => {
  const { authFetch, activeTenant, switchTenant } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // {kind:'create'|'edit', form, id?}

  const [toasts, setToasts] = useState([]);
  const showToast = (m, type = 'success') => {
    const id = Date.now();
    setToasts((p) => [...p, { id, message: m, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
  };

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const res = await authFetch('/api/super-admin/tenants');
      if (res.ok) { const d = await res.json(); setTenants(d.items); }
      else showToast('Không tải được danh sách tổ chức.', 'error');
    } catch { showToast('Lỗi kết nối.', 'error'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTenants(); /* eslint-disable-next-line */ }, []);

  const save = async (e) => {
    e.preventDefault();
    const { kind, form, id } = modal;
    let url, method, payload;
    if (kind === 'create') {
      url = '/api/super-admin/tenants'; method = 'POST';
      payload = { organization_name: form.organization_name, slug: form.slug, admin_username: form.admin_username, admin_email: form.admin_email, admin_password: form.admin_password };
    } else {
      url = `/api/super-admin/tenants/${id}`; method = 'PUT';
      payload = { name: form.name, plan: form.plan, max_employees: Number(form.max_employees) };
    }
    const res = await authFetch(url, { method, body: JSON.stringify(payload) });
    const data = await res.json();
    if (res.ok) { showToast(data.message || 'Đã lưu.'); setModal(null); fetchTenants(); }
    else showToast(data.error || 'Thất bại.', 'error');
  };

  const toggle = async (t) => {
    const res = await authFetch(`/api/super-admin/tenants/${t.id}/toggle-active`, { method: 'PUT' });
    const data = await res.json();
    if (res.ok) { showToast(data.message); fetchTenants(); }
    else showToast(data.error, 'error');
  };

  const handleManage = async (t) => {
    const res = await switchTenant(t.id, { id: t.id, name: t.name, slug: t.slug });
    if (res.success) {
      showToast(`Đã chuyển sang quản lý ${t.name}`);
    } else {
      showToast(res.error, 'error');
    }
  };

  const total = tenants.length;
  const active = tenants.filter((t) => t.is_active).length;

  return (
    <div className="fade-in">
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast toast--${t.type}`}><CheckCircle size={18} style={{ color: t.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }} /><span>{t.message}</span></div>)}
      </div>
      <div className="breadcrumb"><span>GrapeHRM</span><span>&gt;</span><span className="breadcrumb__item">Super Admin</span></div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
        <h2 style={{ fontSize: 24, fontWeight: 600, color: 'var(--color-primary-dark)' }}>Quản lý Tổ chức (Tenant)</h2>
        <button className="btn btn--primary" onClick={() => setModal({ kind: 'create', form: { organization_name: '', slug: '', admin_username: 'admin', admin_email: '', admin_password: '' } })}><Plus size={16} /> Tạo tổ chức</button>
      </div>

      <div className="dashboard-grid" style={{ marginBottom: 24 }}>
        <div className="widget"><div className="widget__info"><span className="widget__label">Tổng tổ chức</span><span className="widget__value">{total}</span></div><div className="widget__icon-wrapper widget__icon-wrapper--primary"><Building2 size={24} /></div></div>
        <div className="widget"><div className="widget__info"><span className="widget__label">Đang hoạt động</span><span className="widget__value">{active}</span></div><div className="widget__icon-wrapper widget__icon-wrapper--success"><CheckCircle size={24} /></div></div>
        <div className="widget"><div className="widget__info"><span className="widget__label">Bị vô hiệu hóa</span><span className="widget__value">{total - active}</span></div><div className="widget__icon-wrapper widget__icon-wrapper--accent"><Lock size={24} /></div></div>
      </div>

      <div className="card card--no-hover">
        <div className="card__body" style={{ padding: 0 }}>
          {loading ? <div style={{ padding: 40, textAlign: 'center' }}><Loader2 className="animate-spin" /></div> : (
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead><tr><th>Tên</th><th>Slug</th><th>Gói</th><th>NV</th><th>User</th><th>Trạng thái</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                <tbody>
                  {tenants.map((t) => (
                    <tr key={t.id} style={{ backgroundColor: activeTenant?.id === t.id ? 'rgba(79, 70, 229, 0.05)' : undefined }}>
                      <td style={{ fontWeight: 600 }}>
                        <Building2 size={14} style={{ marginRight: 6, verticalAlign: 'middle', color: 'var(--color-primary)' }} />
                        {t.name}
                        {activeTenant?.id === t.id && <span style={{ marginLeft: 8, fontSize: 10, backgroundColor: 'var(--color-primary)', color: 'white', padding: '2px 6px', borderRadius: 10 }}>Đang chọn</span>}
                      </td>
                      <td><code>{t.slug}</code></td>
                      <td><span className={`badge ${PLAN_BADGE[t.plan] || 'badge--info'}`}>{t.plan}</span></td>
                      <td><Users size={13} style={{ verticalAlign: 'middle', marginRight: 3 }} />{t.total_employees}</td>
                      <td>{t.total_users}</td>
                      <td>{t.is_active ? <span className="status-badge status-badge--approved">Hoạt động</span> : <span className="status-badge status-badge--rejected">Đã khóa</span>}</td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                        {t.is_active && (
                          <button 
                            className="btn btn--primary" 
                            style={{ padding: '4px 9px', fontSize: 12, marginRight: 6, opacity: activeTenant?.id === t.id ? 0.6 : 1 }} 
                            onClick={() => handleManage(t)}
                            disabled={activeTenant?.id === t.id}
                          >
                            {activeTenant?.id === t.id ? 'Đang quản lý' : 'Quản lý'}
                          </button>
                        )}
                        <button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: 12, marginRight: 6 }} onClick={() => setModal({ kind: 'edit', id: t.id, form: { name: t.name, plan: t.plan, max_employees: t.max_employees } })}><Pencil size={13} /></button>
                        <button className={`btn ${t.is_active ? 'btn--danger' : 'btn--secondary'}`} style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => toggle(t)}>{t.is_active ? <Lock size={13} /> : <Unlock size={13} />}</button>
                      </td>
                    </tr>
                  ))}
                  {tenants.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', padding: 32, color: 'var(--color-text-muted)' }}>Chưa có tổ chức nào.</td></tr>}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {modal && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: 460 }}>
            <div className="modal__header">
              <h3 className="modal__title">{modal.kind === 'create' ? 'Tạo tổ chức mới' : 'Sửa tổ chức'}</h3>
              <button className="modal__close" onClick={() => setModal(null)}>&times;</button>
            </div>
            <form onSubmit={save}>
              <div className="modal__body">
                {modal.kind === 'create' ? (
                  <>
                    <div className="form-group"><label className="form-label form-label--required">Tên tổ chức</label><input className="input" value={modal.form.organization_name} onChange={(e) => setModal({ ...modal, form: { ...modal.form, organization_name: e.target.value } })} required /></div>
                    <div className="form-group"><label className="form-label form-label--required">Mã (slug)</label><input className="input" value={modal.form.slug} onChange={(e) => setModal({ ...modal, form: { ...modal.form, slug: e.target.value.toLowerCase() } })} placeholder="vd: techcorp" required /></div>
                    <div className="form-group"><label className="form-label form-label--required">Tài khoản admin</label><input className="input" value={modal.form.admin_username} onChange={(e) => setModal({ ...modal, form: { ...modal.form, admin_username: e.target.value } })} required /></div>
                    <div className="form-group"><label className="form-label">Email admin</label><input type="email" className="input" value={modal.form.admin_email} onChange={(e) => setModal({ ...modal, form: { ...modal.form, admin_email: e.target.value } })} /></div>
                    <div className="form-group"><label className="form-label form-label--required">Mật khẩu admin</label><input type="password" className="input" value={modal.form.admin_password} onChange={(e) => setModal({ ...modal, form: { ...modal.form, admin_password: e.target.value } })} required /></div>
                  </>
                ) : (
                  <>
                    <div className="form-group"><label className="form-label">Tên tổ chức</label><input className="input" value={modal.form.name} onChange={(e) => setModal({ ...modal, form: { ...modal.form, name: e.target.value } })} /></div>
                    <div className="form-group"><label className="form-label">Gói dịch vụ</label><select className="input" value={modal.form.plan} onChange={(e) => setModal({ ...modal, form: { ...modal.form, plan: e.target.value } })}><option value="FREE">FREE</option><option value="PRO">PRO</option><option value="ENTERPRISE">ENTERPRISE</option></select></div>
                    <div className="form-group"><label className="form-label">Giới hạn nhân viên</label><input type="number" className="input" value={modal.form.max_employees} onChange={(e) => setModal({ ...modal, form: { ...modal.form, max_employees: e.target.value } })} /></div>
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

export default SuperAdminPage;
