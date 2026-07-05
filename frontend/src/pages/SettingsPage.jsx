import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Building2, Users, Loader2, CheckCircle, Save, Lock, Unlock, KeyRound, Shield,
  History, ChevronLeft, ChevronRight
} from 'lucide-react';

const ROLE_LABELS = {
  super_admin: 'Super Admin',
  admin: 'Admin',
  hr_manager: 'Quản lý NS',
  employee: 'Nhân viên',
};

const SettingsPage = () => {
  const { user, getAuthHeaders } = useAuth();
  const [activeTab, setActiveTab] = useState('org');

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  };

  // ── Tổ chức ──────────────────────────────────────────────────
  const [org, setOrg] = useState(null);
  const [orgLoading, setOrgLoading] = useState(true);
  const [orgSaving, setOrgSaving] = useState(false);

  const fetchOrg = async () => {
    setOrgLoading(true);
    try {
      const res = await fetch('/api/admin/organization', { headers: getAuthHeaders() });
      if (res.ok) setOrg(await res.json());
      else showToast('Không tải được thông tin tổ chức.', 'error');
    } catch {
      showToast('Lỗi kết nối.', 'error');
    } finally {
      setOrgLoading(false);
    }
  };

  const saveOrg = async (e) => {
    e.preventDefault();
    setOrgSaving(true);
    try {
      const res = await fetch('/api/admin/organization', {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(org),
      });
      const data = await res.json();
      if (res.ok) showToast(data.message || 'Đã lưu.');
      else showToast(data.error || 'Lưu thất bại.', 'error');
    } catch {
      showToast('Lỗi kết nối.', 'error');
    } finally {
      setOrgSaving(false);
    }
  };

  // ── Tài khoản ────────────────────────────────────────────────
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);

  const fetchUsers = async () => {
    setUsersLoading(true);
    try {
      const res = await fetch('/api/admin/users', { headers: getAuthHeaders() });
      if (res.ok) setUsers(await res.json());
      else showToast('Không tải được danh sách tài khoản.', 'error');
    } catch {
      showToast('Lỗi kết nối.', 'error');
    } finally {
      setUsersLoading(false);
    }
  };

  const toggleActive = async (u) => {
    try {
      const res = await fetch(`/api/admin/users/${u.id}/toggle-active`, {
        method: 'PUT',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message);
        setUsers((prev) => prev.map((x) => (x.id === u.id ? { ...x, is_active: data.is_active } : x)));
      } else {
        showToast(data.error || 'Thao tác thất bại.', 'error');
      }
    } catch {
      showToast('Lỗi kết nối.', 'error');
    }
  };

  const resetPassword = async (u) => {
    if (!window.confirm(`Reset mật khẩu của "${u.username}" về "123456"?`)) return;
    try {
      const res = await fetch(`/api/admin/users/${u.id}/reset-password`, {
        method: 'PUT',
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      showToast(res.ok ? data.message : (data.error || 'Thất bại.'), res.ok ? 'success' : 'error');
    } catch {
      showToast('Lỗi kết nối.', 'error');
    }
  };

  // ── Nhật ký hoạt động ────────────────────────────────────────
  const [audit, setAudit] = useState({ items: [], total: 0, page: 1, total_pages: 1 });
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditPage, setAuditPage] = useState(1);

  const fetchAudit = async (page = 1) => {
    setAuditLoading(true);
    try {
      const res = await fetch(`/api/admin/audit-logs?page=${page}&per_page=20`, { headers: getAuthHeaders() });
      if (res.ok) setAudit(await res.json());
      else showToast('Không tải được nhật ký.', 'error');
    } catch {
      showToast('Lỗi kết nối.', 'error');
    } finally {
      setAuditLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'org' && org === null) fetchOrg();
    if (activeTab === 'users' && users.length === 0) fetchUsers();
    if (activeTab === 'audit') fetchAudit(auditPage);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, auditPage]);

  const ACTION_LABELS = {
    LOGIN: ['Đăng nhập', 'badge--info'], CREATE: ['Tạo', 'badge--success'],
    UPDATE: ['Cập nhật', 'badge--warning'], DELETE: ['Xóa', 'badge--danger'],
    APPROVE: ['Duyệt', 'badge--success'], REJECT: ['Từ chối', 'badge--danger'],
    RUN: ['Chạy', 'badge--info'],
  };

  const orgField = (key, label, type = 'text') => (
    <div className="form-group">
      <label className="form-label">{label}</label>
      {type === 'textarea' ? (
        <textarea className="input" rows={2} value={org[key] || ''} onChange={(e) => setOrg({ ...org, [key]: e.target.value })} />
      ) : (
        <input type={type} className="input" value={org[key] || ''} onChange={(e) => setOrg({ ...org, [key]: e.target.value })} />
      )}
    </div>
  );

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
        <span>GrapeHRM</span>
        <span>&gt;</span>
        <span className="breadcrumb__item">Hệ thống & Bảo mật</span>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Hệ thống & Bảo mật</h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
          Quản lý thông tin tổ chức và tài khoản người dùng.
        </p>
      </div>

      <div className="leave-tabs">
        <button className={`leave-tabs__tab ${activeTab === 'org' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setActiveTab('org')}>
          <Building2 size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /> Thông tin Tổ chức
        </button>
        <button className={`leave-tabs__tab ${activeTab === 'users' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setActiveTab('users')}>
          <Users size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /> Quản lý Tài khoản
        </button>
        <button className={`leave-tabs__tab ${activeTab === 'audit' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setActiveTab('audit')}>
          <History size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} /> Nhật ký Hoạt động
        </button>
      </div>

      {/* ── TAB: Tổ chức ── */}
      {activeTab === 'org' && (
        <div className="card card--no-hover">
          <div className="card__body">
            {orgLoading || !org ? (
              <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
            ) : (
              <form onSubmit={saveOrg}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0 20px' }}>
                  {orgField('name', 'Tên tổ chức')}
                  <div className="form-group">
                    <label className="form-label">Mã tổ chức (slug)</label>
                    <input type="text" className="input" value={org.slug || ''} disabled style={{ background: 'var(--color-bg)', cursor: 'not-allowed' }} />
                    <small style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>Không đổi được — dùng để đăng nhập.</small>
                  </div>
                  {orgField('tax_id', 'Mã số thuế')}
                  {orgField('reg_number', 'Số ĐKKD')}
                  {orgField('phone', 'Số điện thoại', 'tel')}
                  {orgField('email', 'Email liên hệ', 'email')}
                  {orgField('country', 'Quốc gia')}
                  {orgField('city', 'Thành phố')}
                </div>
                {orgField('address', 'Địa chỉ', 'textarea')}
                <div style={{ marginTop: '8px' }}>
                  <button type="submit" className="btn btn--primary" disabled={orgSaving}>
                    {orgSaving ? <><Loader2 size={16} className="animate-spin" style={{ marginRight: '8px' }} /> Đang lưu...</> : <><Save size={16} /> Lưu thay đổi</>}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: Tài khoản ── */}
      {activeTab === 'users' && (
        <div className="card card--no-hover">
          <div className="card__body" style={{ padding: 0 }}>
            {usersLoading ? (
              <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
            ) : (
              <div className="table-responsive">
                <table className="table table--zebra">
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Nhân viên</th>
                      <th>Email</th>
                      <th>Vai trò</th>
                      <th>Trạng thái</th>
                      <th>Đăng nhập cuối</th>
                      <th style={{ textAlign: 'right' }}>Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr key={u.id}>
                        <td style={{ fontWeight: 600 }}>
                          {u.username}
                          {u.id === user?.id && <span style={{ marginLeft: '6px', fontSize: '11px', color: 'var(--color-text-muted)' }}>(bạn)</span>}
                        </td>
                        <td>{u.employee_name || <span style={{ color: 'var(--color-text-muted)' }}>—</span>}</td>
                        <td style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>{u.email}</td>
                        <td><span className="badge badge--info"><Shield size={12} style={{ marginRight: '4px', verticalAlign: 'middle' }} />{ROLE_LABELS[u.role] || u.role}</span></td>
                        <td>
                          {u.is_active
                            ? <span className="status-badge status-badge--approved">Hoạt động</span>
                            : <span className="status-badge status-badge--rejected">Đã khóa</span>}
                        </td>
                        <td style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>
                          {u.last_login ? new Date(u.last_login).toLocaleString('vi-VN') : 'Chưa từng'}
                        </td>
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <button
                            className={`btn ${u.is_active ? 'btn--danger' : 'btn--secondary'}`}
                            style={{ padding: '4px 10px', fontSize: '12px', marginRight: '6px' }}
                            onClick={() => toggleActive(u)}
                            disabled={u.id === user?.id}
                            title={u.id === user?.id ? 'Không thể tự khóa chính mình' : ''}
                          >
                            {u.is_active ? <><Lock size={13} /> Khóa</> : <><Unlock size={13} /> Mở</>}
                          </button>
                          <button
                            className="btn btn--secondary"
                            style={{ padding: '4px 10px', fontSize: '12px' }}
                            onClick={() => resetPassword(u)}
                          >
                            <KeyRound size={13} /> Reset MK
                          </button>
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr><td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--color-text-muted)' }}>Chưa có tài khoản nào.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB: Nhật ký ── */}
      {activeTab === 'audit' && (
        <div className="card card--no-hover">
          <div className="card__body" style={{ padding: 0 }}>
            {auditLoading ? (
              <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
            ) : (
              <>
                <div className="table-responsive">
                  <table className="table table--zebra">
                    <thead>
                      <tr><th>Thời gian</th><th>Người dùng</th><th>Hành động</th><th>Đối tượng</th><th>Chi tiết</th><th>IP</th></tr>
                    </thead>
                    <tbody>
                      {audit.items.map((l) => {
                        const al = ACTION_LABELS[l.action] || [l.action, 'badge--info'];
                        return (
                          <tr key={l.id}>
                            <td style={{ fontSize: 13, whiteSpace: 'nowrap' }}>{new Date(l.created_at).toLocaleString('vi-VN')}</td>
                            <td style={{ fontWeight: 600 }}>{l.user_name}</td>
                            <td><span className={`badge ${al[1]}`}>{al[0]}</span></td>
                            <td>{l.resource_type}{l.resource_id ? ` #${l.resource_id}` : ''}</td>
                            <td style={{ color: 'var(--color-text-muted)', fontSize: 12, maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{l.details || '—'}</td>
                            <td style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>{l.ip_address || '—'}</td>
                          </tr>
                        );
                      })}
                      {audit.items.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', padding: 32, color: 'var(--color-text-muted)' }}>Chưa có nhật ký nào.</td></tr>}
                    </tbody>
                  </table>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>
                  <span style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>Tổng {audit.total} bản ghi · Trang {audit.page}/{audit.total_pages || 1}</span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn--secondary" style={{ padding: '4px 10px' }} disabled={auditPage <= 1} onClick={() => setAuditPage((p) => p - 1)}><ChevronLeft size={14} /></button>
                    <button className="btn btn--secondary" style={{ padding: '4px 10px' }} disabled={auditPage >= (audit.total_pages || 1)} onClick={() => setAuditPage((p) => p + 1)}><ChevronRight size={14} /></button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
