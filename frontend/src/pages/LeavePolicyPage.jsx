import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Plus, CheckCircle, Trash2, Edit, Loader2 } from 'lucide-react';

const LeavePolicyPage = () => {
  const { getAuthHeaders, user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
  const [activeTab, setActiveTab] = useState('types'); // 'types', 'policies'

  const [leaveTypes, setLeaveTypes] = useState([]);
  const [policies, setPolicies] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3000);
  };

  // State Modals
  const [isTypeModalOpen, setIsTypeModalOpen] = useState(false);
  const [editType, setEditType] = useState(null);
  const [typeForm, setTypeForm] = useState({ name: '', code: '', is_paid: true, max_days: 0, description: '' });

  const [isPolicyModalOpen, setIsPolicyModalOpen] = useState(false);
  const [editPolicy, setEditPolicy] = useState(null);
  const [policyForm, setPolicyForm] = useState({ name: '', is_default: false, details: [] });
  // details format: [{ type_id: 1, entitlement: 12 }]

  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignForm, setAssignForm] = useState({ policy_id: '', employee_ids: [], effective_year: new Date().getFullYear() });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [typesRes, policiesRes, empRes] = await Promise.all([
        fetch('/api/leave-types', { headers: getAuthHeaders() }),
        fetch('/api/leave-policies', { headers: getAuthHeaders() }),
        fetch('/api/employees', { headers: getAuthHeaders() })
      ]);
      if (typesRes.ok) setLeaveTypes(await typesRes.json());
      if (policiesRes.ok) setPolicies(await policiesRes.json());
      if (empRes.ok) setEmployees(await empRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --- Leave Types ---
  const handleSaveType = async (e) => {
    e.preventDefault();
    const isEdit = !!editType;
    const url = isEdit ? `/api/leave-types/${editType.id}` : '/api/leave-types';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method, headers: getAuthHeaders(), body: JSON.stringify(typeForm)
      });
      if (res.ok) {
        showToast(isEdit ? 'Cập nhật thành công' : 'Thêm mới thành công');
        setIsTypeModalOpen(false);
        fetchData();
      } else {
        const d = await res.json();
        showToast(d.error || 'Lỗi hệ thống', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const handleDeleteType = async (typeId) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa loại phép này?')) return;
    try {
      const res = await fetch(`/api/leave-types/${typeId}`, { method: 'DELETE', headers: getAuthHeaders() });
      if (res.ok) { showToast('Xóa thành công'); fetchData(); }
      else showToast('Lỗi hệ thống', 'error');
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  // --- Policies ---
  const handleSavePolicy = async (e) => {
    e.preventDefault();
    if (!policyForm.name.trim()) return showToast('Tên chính sách không được trống', 'error');

    const isEdit = !!editPolicy;
    const url = isEdit ? `/api/leave-policies/${editPolicy.id}` : '/api/leave-policies';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const res = await fetch(url, {
        method, headers: getAuthHeaders(), body: JSON.stringify(policyForm)
      });
      if (res.ok) {
        showToast(isEdit ? 'Cập nhật chính sách thành công' : 'Tạo chính sách thành công');
        setIsPolicyModalOpen(false);
        setEditPolicy(null);
        fetchData();
      } else {
        const d = await res.json();
        showToast(d.error || 'Lỗi', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const handleDeletePolicy = async (policy) => {
    if (policy.is_default) {
      return showToast('Không thể xóa chính sách mặc định. Hãy đặt chính sách khác làm mặc định trước.', 'error');
    }
    if (!window.confirm(`Bạn có chắc chắn muốn xóa chính sách "${policy.name}"?`)) return;
    try {
      const res = await fetch(`/api/leave-policies/${policy.id}`, { method: 'DELETE', headers: getAuthHeaders() });
      if (res.ok) { showToast('Xóa chính sách thành công'); fetchData(); }
      else {
        const d = await res.json();
        showToast(d.error || 'Lỗi hệ thống', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  // --- Assign Policy ---
  const handleAssignPolicy = async (e) => {
    e.preventDefault();
    if (!assignForm.policy_id || assignForm.employee_ids.length === 0) {
      return showToast('Vui lòng chọn chính sách và ít nhất 1 nhân viên', 'error');
    }

    try {
      const res = await fetch(`/api/leave-policies/${assignForm.policy_id}/assign`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(assignForm)
      });
      if (res.ok) {
        showToast('Gán chính sách thành công');
        setIsAssignModalOpen(false);
      } else {
        showToast('Lỗi khi gán chính sách', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

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
        <span className="breadcrumb__item">Chính sách nghỉ phép</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Quản trị hệ thống Nghỉ phép</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Thiết lập loại phép và gán chính sách phép cho nhân sự.
          </p>
        </div>
      </div>

      <div className="leave-tabs">
        <button className={`leave-tabs__tab ${activeTab === 'types' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setActiveTab('types')}>
          Loại nghỉ phép
        </button>
        <button className={`leave-tabs__tab ${activeTab === 'policies' ? 'leave-tabs__tab--active' : ''}`} onClick={() => setActiveTab('policies')}>
          Chính sách phép
        </button>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '40px' }}><Loader2 className="animate-spin" /></div>}

      {/* TABS NỘI DUNG */}
      {!loading && activeTab === 'types' && (
        <div className="card card--no-hover">
          <div className="card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card__title">Danh sách Loại phép</h3>
            <button className="btn btn--primary" onClick={() => {
              setEditType(null);
              setTypeForm({ name: '', code: '', is_paid: true, max_days: 0, description: '' });
              setIsTypeModalOpen(true);
            }}>
              <Plus size={16} /> Thêm Loại phép
            </button>
          </div>
          <div className="card__body" style={{ padding: 0 }}>
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead>
                  <tr>
                    <th>Mã</th>
                    <th>Tên loại phép</th>
                    <th>Hưởng lương</th>
                    <th>Giới hạn mặc định (ngày)</th>
                    <th>Mô tả</th>
                    <th style={{ textAlign: 'right' }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {leaveTypes.map(t => (
                    <tr key={t.id}>
                      <td style={{ fontWeight: 600, color: 'var(--color-text-muted)' }}>{t.code}</td>
                      <td style={{ fontWeight: 600 }}>{t.name}</td>
                      <td>{t.is_paid ? <span className="status-badge status-badge--approved">Có</span> : <span className="status-badge status-badge--rejected">Không</span>}</td>
                      <td>{t.max_days || 'Không giới hạn'}</td>
                      <td>{t.description}</td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                          <button className="btn btn--icon" onClick={() => {
                            setEditType(t);
                            setTypeForm({ name: t.name, code: t.code, is_paid: t.is_paid, max_days: t.max_days, description: t.description || '' });
                            setIsTypeModalOpen(true);
                          }}><Edit size={16} /></button>
                          <button className="btn btn--icon btn--icon-danger" onClick={() => handleDeleteType(t.id)}><Trash2 size={16} /></button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {!loading && activeTab === 'policies' && (
        <>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
            <button className="btn btn--primary" onClick={() => {
              setEditPolicy(null);
              setPolicyForm({ name: '', is_default: false, details: leaveTypes.map(t => ({ type_id: t.id, entitlement: t.max_days })) });
              setIsPolicyModalOpen(true);
            }}>
              <Plus size={16} /> Tạo Chính sách mới
            </button>
            <button className="btn btn--secondary" onClick={() => {
              setAssignForm({ policy_id: '', employee_ids: [], effective_year: new Date().getFullYear() });
              setIsAssignModalOpen(true);
            }}>Gán Chính sách cho Nhân viên</button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            {policies.map(p => (
              <div className="policy-card" key={p.id}>
                <div className="policy-card__header">
                  <div className="policy-card__title">{p.name} {p.is_default && <span className="status-badge status-badge--approved" style={{ marginLeft: '8px' }}>Mặc định</span>}</div>
                  {isAdmin && (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button className="btn btn--icon" title="Sửa chính sách" onClick={() => {
                        setEditPolicy(p);
                        // Ghép details hiện có với tất cả leave types (bổ sung type mới nếu cần)
                        const mergedDetails = leaveTypes.map(t => {
                          const existing = p.details.find(d => d.type_id === t.id);
                          return { type_id: t.id, entitlement: existing ? existing.entitlement : t.max_days };
                        });
                        setPolicyForm({ name: p.name, is_default: p.is_default, details: mergedDetails });
                        setIsPolicyModalOpen(true);
                      }}><Edit size={16} /></button>
                      <button className="btn btn--icon btn--icon-danger" title="Xóa chính sách" onClick={() => handleDeletePolicy(p)}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  )}
                </div>
                <div>
                  {p.details.map(d => (
                    <div className="policy-card__detail" key={d.type_id}>
                      <span style={{ fontWeight: 500, color: 'var(--color-text-secondary)' }}>{d.type_name}</span>
                      <span style={{ fontWeight: 700 }}>{d.entitlement} ngày</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* MODALS */}
      {isTypeModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '400px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{editType ? 'Sửa loại phép' : 'Thêm loại phép'}</h3>
              <button className="modal__close" onClick={() => setIsTypeModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSaveType}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Tên loại phép</label>
                  <input type="text" className="input" value={typeForm.name} onChange={e => setTypeForm({ ...typeForm, name: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Mã (Code)</label>
                  <input type="text" className="input" value={typeForm.code} onChange={e => setTypeForm({ ...typeForm, code: e.target.value })} required disabled={!!editType} />
                </div>
                <div className="form-group">
                  <label className="form-label">Hưởng lương</label>
                  <select className="input" value={typeForm.is_paid} onChange={e => setTypeForm({ ...typeForm, is_paid: e.target.value === 'true' })}>
                    <option value="true">Có</option>
                    <option value="false">Không</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Mô tả</label>
                  <textarea className="input" value={typeForm.description} onChange={e => setTypeForm({ ...typeForm, description: e.target.value })}></textarea>
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsTypeModalOpen(false)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isPolicyModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '500px' }}>
            <div className="modal__header">
              <h3 className="modal__title">{editPolicy ? 'Sửa Chính sách phép' : 'Tạo Chính sách phép'}</h3>
              <button className="modal__close" onClick={() => { setIsPolicyModalOpen(false); setEditPolicy(null); }}>&times;</button>
            </div>
            <form onSubmit={handleSavePolicy}>
              <div className="modal__body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
                <div className="form-group">
                  <label className="form-label form-label--required">Tên chính sách</label>
                  <input type="text" className="input" value={policyForm.name} onChange={e => setPolicyForm({ ...policyForm, name: e.target.value })} required />
                </div>
                <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <input type="checkbox" id="is_default" checked={policyForm.is_default} onChange={e => setPolicyForm({ ...policyForm, is_default: e.target.checked })} />
                  <label htmlFor="is_default">Áp dụng mặc định cho tất cả nhân viên</label>
                </div>

                <h4 style={{ margin: '16px 0 8px 0', fontSize: '14px', fontWeight: 600 }}>Cấu hình số ngày nghỉ (Entitlement)</h4>
                {policyForm.details.map((d, index) => {
                  const type = leaveTypes.find(t => t.id === d.type_id);
                  return (
                    <div key={d.type_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '13px' }}>{type?.name}</span>
                      <input
                        type="number"
                        className="input"
                        style={{ width: '100px' }}
                        value={d.entitlement}
                        min="0"
                        onChange={(e) => {
                          const newDetails = [...policyForm.details];
                          newDetails[index].entitlement = Math.max(0, parseInt(e.target.value) || 0);
                          setPolicyForm({ ...policyForm, details: newDetails });
                        }}
                      />
                    </div>
                  );
                })}
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => { setIsPolicyModalOpen(false); setEditPolicy(null); }}>Hủy</button>
                <button type="submit" className="btn btn--primary">Lưu Chính sách</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isAssignModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '500px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Gán Chính sách cho nhân viên</h3>
              <button className="modal__close" onClick={() => setIsAssignModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleAssignPolicy}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Năm áp dụng</label>
                  <input type="number" className="input" value={assignForm.effective_year} onChange={e => setAssignForm({ ...assignForm, effective_year: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Chính sách</label>
                  <select className="input" value={assignForm.policy_id} onChange={e => setAssignForm({ ...assignForm, policy_id: e.target.value })} required>
                    <option value="">-- Chọn chính sách --</option>
                    {policies.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Nhân viên (Giữ Ctrl để chọn nhiều)</label>
                  <select
                    multiple
                    className="input"
                    style={{ height: '150px' }}
                    value={assignForm.employee_ids}
                    onChange={(e) => {
                      const options = [...e.target.options];
                      const values = options.filter(o => o.selected).map(o => parseInt(o.value));
                      setAssignForm({ ...assignForm, employee_ids: values });
                    }}
                    required
                  >
                    {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.full_name} ({emp.employee_id})</option>)}
                  </select>
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsAssignModalOpen(false)}>Hủy</button>
                <button type="submit" className="btn btn--primary">Áp dụng</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default LeavePolicyPage;
