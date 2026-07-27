import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Plus, Check, X as XIcon, Loader2, AlertTriangle, CheckCircle, Calendar, CalendarDays, Trash2 } from 'lucide-react';

const LeavePage = () => {
  const { user, authFetch } = useAuth();
  const [activeTab, setActiveTab] = useState('personal');
  const [loading, setLoading] = useState(false);
  const [leaveBalances, setLeaveBalances] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [cancelReqId, setCancelReqId] = useState(null);
  const [formData, setFormData] = useState({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    total_days: '',
    reason: ''
  });

  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  const isAdminOrHR = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'hr_manager';
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  useEffect(() => {
    if (isAdmin && activeTab === 'personal') {
      setActiveTab('approval');
    }
  }, [isAdmin, activeTab]);

  const fetchLeaveBalances = async () => {
    if (!user?.employee_id) return;
    try {
      const response = await authFetch(`/api/leave-balance/${user.employee_id}`);
      if (response.ok) {
        setLeaveBalances(await response.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchLeaveTypes = async () => {
    try {
      const response = await authFetch('/api/leave-types');
      if (response.ok) setLeaveTypes(await response.json());
    } catch (err) { console.error(err); }
  };

  const fetchMyRequests = async () => {
    if (!user?.employee_id) return;
    setLoading(true);
    try {
      const response = await authFetch(`/api/leave-requests?employee_id=${user.employee_id}`);
      if (response.ok) setMyRequests(await response.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const fetchPendingRequests = async () => {
    setLoading(true);
    try {
      const response = await authFetch('/api/leave-requests?status=PENDING_HR');
      if (response.ok) setPendingRequests(await response.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    if (activeTab === 'personal') {
      fetchLeaveBalances();
      fetchMyRequests();
    } else if (activeTab === 'approval') {
      fetchPendingRequests();
    }
    fetchLeaveTypes();
  }, [activeTab, user?.employee_id]);

  // Tự động tính số ngày nghỉ (loại T7/CN — khớp với cách server tính)
  useEffect(() => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      if (end >= start) {
        let workdays = 0;
        const cur = new Date(start);
        while (cur <= end) {
          const dow = cur.getDay(); // 0=CN, 6=T7
          if (dow !== 0 && dow !== 6) workdays += 1;
          cur.setDate(cur.getDate() + 1);
        }
        setFormData(prev => ({ ...prev, total_days: workdays }));
      } else {
        setFormData(prev => ({ ...prev, total_days: 0 }));
      }
    }
  }, [formData.start_date, formData.end_date]);

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    try {
      const response = await authFetch('/api/leave-requests', {
        method: 'POST',
        body: JSON.stringify({ ...formData, employee_id: user.employee_id })
      });
      const data = await response.json();
      if (response.ok) {
        showToast('Tạo đơn xin nghỉ thành công');
        setIsModalOpen(false);
        setFormData({ leave_type_id: '', start_date: '', end_date: '', total_days: '', reason: '' });
        fetchMyRequests();
        fetchLeaveBalances();
      } else {
        showToast(data.error || 'Lỗi tạo đơn', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    }
  };

  const handleApprove = async (reqId) => {
    try {
      const response = await authFetch(`/api/leave-requests/${reqId}/approve`, {
        method: 'PUT'
      });
      if (response.ok) {
        showToast('Đã phê duyệt đơn nghỉ phép');
        fetchPendingRequests();
      } else {
        const data = await response.json();
        showToast(data.error || 'Lỗi thao tác', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    }
  };

  const handleCancelRequest = (reqId) => {
    setCancelReqId(reqId);
  };

  const confirmCancelRequest = async () => {
    if (!cancelReqId) return;
    try {
      const response = await authFetch(`/api/leave-requests/${cancelReqId}/cancel`, {
        method: 'PUT'
      });
      if (response.ok) {
        showToast('Đã hủy đơn nghỉ phép');
        fetchMyRequests();
      } else {
        const data = await response.json();
        showToast(data.error || 'Lỗi thao tác', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    } finally {
      setCancelReqId(null);
    }
  };

  const handleReject = async (reqId) => {
    try {
      const response = await authFetch(`/api/leave-requests/${reqId}/reject`, {
        method: 'PUT'
      });
      if (response.ok) {
        showToast('Đã từ chối đơn nghỉ phép');
        fetchPendingRequests();
      } else {
        const data = await response.json();
        showToast(data.error || 'Lỗi thao tác', 'error');
      }
    } catch (err) {
      showToast('Lỗi mạng', 'error');
    }
  };

  const renderStatus = (status) => {
    switch(status) {
      case 'PENDING_HR': return <span className="status-badge status-badge--warning">Chờ HR duyệt</span>;
      case 'APPROVED': return <span className="status-badge status-badge--approved">Đã duyệt</span>;
      case 'REJECTED': return <span className="status-badge status-badge--rejected">Từ chối</span>;
      case 'CANCELLED': return <span className="status-badge status-badge--cancelled">Đã hủy</span>;
      default: return <span className="status-badge">{status}</span>;
    }
  };

  const getLocalDateStr = () => {
    const d = new Date();
    const tzOffset = d.getTimezoneOffset() * 60000;
    return new Date(d.getTime() - tzOffset).toISOString().split('T')[0];
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
        <span className="breadcrumb__item">Nghỉ phép</span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Nghỉ phép</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Quản lý ngày phép, tạo đơn nghỉ phép và phê duyệt đơn.
          </p>
        </div>
        {activeTab === 'personal' && !isAdmin && (
          <button className="btn btn--primary" onClick={() => setIsModalOpen(true)}>
            <Plus size={16} /> Tạo đơn xin nghỉ
          </button>
        )}
      </div>

      <div className="leave-tabs">
        {!isAdmin && (
          <button 
            className={`leave-tabs__tab ${activeTab === 'personal' ? 'leave-tabs__tab--active' : ''}`}
            onClick={() => setActiveTab('personal')}
          >
            Cá nhân
          </button>
        )}
        {isAdminOrHR && (
          <button 
            className={`leave-tabs__tab ${activeTab === 'approval' ? 'leave-tabs__tab--active' : ''}`}
            onClick={() => setActiveTab('approval')}
          >
            Phê duyệt
          </button>
        )}
      </div>

      {activeTab === 'personal' && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            {leaveBalances.map(bal => (
              <div key={bal.type_id} className="card card--hover-blue">
                <div className="card__body">
                  <h4 style={{ fontSize: '14px', color: 'var(--color-text-muted)', fontWeight: 600 }}>{bal.type_name}</h4>
                  <div style={{ 
                    fontSize: '28px', 
                    fontWeight: 700, 
                    color: (bal.entitlement > 0 && bal.remaining <= 0) ? 'var(--color-error)' : 'var(--color-primary)', 
                    marginTop: '8px' 
                  }}>
                    {bal.remaining} <span style={{ fontSize: '14px', color: 'var(--color-text-muted)', fontWeight: 400 }}>ngày</span>
                  </div>
                  <div className="balance-bar">
                    <div className="balance-bar__fill" style={{ width: `${bal.entitlement > 0 ? (Math.max(0, bal.remaining) / bal.entitlement) * 100 : 0}%` }}></div>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Đã dùng: {bal.used}</span>
                    <span>Tổng: {bal.entitlement}</span>
                  </div>
                </div>
              </div>
            ))}
            {leaveBalances.length === 0 && (
              <div className="card card--no-hover" style={{ gridColumn: '1 / -1', padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                Chưa có thông tin số dư phép hoặc chưa được gán chính sách phép năm nay.
              </div>
            )}
          </div>

          <div className="card card--no-hover">
            <div className="card__header">
              <h3 className="card__title">Lịch sử đơn nghỉ phép</h3>
            </div>
            <div className="card__body" style={{ padding: 0 }}>
              {loading ? (
                <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
              ) : myRequests.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>Bạn chưa có đơn nghỉ phép nào.</div>
              ) : (
                <div className="table-responsive">
                  <table className="table table--zebra">
                    <thead>
                      <tr>
                        <th>Loại nghỉ phép</th>
                        <th>Từ ngày</th>
                        <th>Đến ngày</th>
                        <th>Số ngày</th>
                        <th>Trạng thái</th>
                        <th>Ngày tạo</th>
                        <th style={{ textAlign: 'right' }}>Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      {myRequests.map(req => (
                        <tr key={req.id}>
                          <td style={{ fontWeight: 600 }}>{req.leave_type}</td>
                          <td>{new Date(req.start_date).toLocaleDateString('vi-VN')}</td>
                          <td>{new Date(req.end_date).toLocaleDateString('vi-VN')}</td>
                          <td>{req.total_days}</td>
                          <td>{renderStatus(req.status)}</td>
                          <td style={{ color: 'var(--color-text-muted)' }}>{new Date(req.created_at).toLocaleDateString('vi-VN')}</td>
                          <td style={{ textAlign: 'right' }}>
                            {req.status === 'PENDING_HR' && (
                              <button className="btn btn--secondary" style={{ padding: '4px 9px', fontSize: 12 }} onClick={() => handleCancelRequest(req.id)} title="Hủy đơn">
                                <Trash2 size={13} />
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {activeTab === 'approval' && (
        <div className="card card--no-hover">
          <div className="card__header">
            <h3 className="card__title">Đơn đang chờ duyệt</h3>
          </div>
          <div className="card__body" style={{ padding: 0 }}>
            {loading ? (
              <div style={{ padding: '40px', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>
            ) : pendingRequests.length === 0 ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có đơn nào đang chờ duyệt.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table--zebra">
                  <thead>
                    <tr>
                      <th>Nhân viên</th>
                      <th>Loại phép</th>
                      <th>Thời gian</th>
                      <th>Số ngày</th>
                      <th>Trạng thái</th>
                      <th style={{ textAlign: 'right' }}>Thao tác</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingRequests.map(req => (
                      <tr key={req.id}>
                        <td style={{ fontWeight: 600, color: 'var(--color-primary-dark)' }}>{req.employee_name}</td>
                        <td>{req.leave_type}</td>
                        <td>{new Date(req.start_date).toLocaleDateString('vi-VN')} - {new Date(req.end_date).toLocaleDateString('vi-VN')}</td>
                        <td>{req.total_days}</td>
                        <td>{renderStatus(req.status)}</td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', alignItems: 'center' }}>
                            {req.end_date < getLocalDateStr() && !isAdmin ? (
                              <span style={{ fontSize: '13px', color: 'var(--color-error)', fontWeight: 500, marginRight: '8px' }}>Quá hạn</span>
                            ) : (
                              <>
                                <button className="btn btn--icon" style={{ color: 'var(--color-success)', borderColor: 'var(--color-success)' }} onClick={() => handleApprove(req.id)} title="Duyệt">
                                  <Check size={16} />
                                </button>
                                <button className="btn btn--icon" style={{ color: 'var(--color-error)', borderColor: 'var(--color-error)' }} onClick={() => handleReject(req.id)} title="Từ chối">
                                  <XIcon size={16} />
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}


      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '500px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Tạo đơn xin nghỉ</h3>
              <button className="modal__close" onClick={() => setIsModalOpen(false)}>&times;</button>
            </div>
            <form onSubmit={handleSubmitRequest}>
              <div className="modal__body">
                <div className="form-group">
                  <label className="form-label form-label--required">Loại nghỉ phép</label>
                  <select 
                    className="input" 
                    value={formData.leave_type_id} 
                    onChange={e => setFormData({...formData, leave_type_id: e.target.value})}
                    required
                  >
                    <option value="">-- Chọn loại phép --</option>
                    {leaveTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label form-label--required">Từ ngày</label>
                    <input type="date" className="input" value={formData.start_date} onChange={e => setFormData({...formData, start_date: e.target.value})} min={getLocalDateStr()} required />
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required">Đến ngày</label>
                    <input type="date" className="input" value={formData.end_date} onChange={e => setFormData({...formData, end_date: e.target.value})} min={formData.start_date || getLocalDateStr()} required />
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label form-label--required">Tổng số ngày nghỉ</label>
                  <input type="number" step="0.5" min="0.5" className="input" value={formData.total_days} readOnly style={{ backgroundColor: 'var(--color-bg)', cursor: 'not-allowed' }} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Lý do</label>
                  <textarea className="input" rows="3" value={formData.reason} onChange={e => setFormData({...formData, reason: e.target.value})}></textarea>
                </div>
              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsModalOpen(false)}>Hủy bỏ</button>
                <button type="submit" className="btn btn--primary">Nộp đơn</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {cancelReqId && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '400px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Xác nhận hủy đơn</h3>
              <button className="modal__close" onClick={() => setCancelReqId(null)}>&times;</button>
            </div>
            <div className="modal__body" style={{ padding: '24px 20px', textAlign: 'center' }}>
              <AlertTriangle size={48} style={{ color: 'var(--color-warning)', margin: '0 auto 16px' }} />
              <p style={{ fontSize: '15px', color: 'var(--color-text-main)' }}>
                Bạn có chắc chắn muốn hủy đơn nghỉ phép này không?
              </p>
            </div>
            <div className="modal__footer" style={{ justifyContent: 'center' }}>
              <button type="button" className="btn btn--secondary" onClick={() => setCancelReqId(null)}>Không</button>
              <button type="button" className="btn btn--danger" onClick={confirmCancelRequest}>Hủy đơn</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeavePage;
