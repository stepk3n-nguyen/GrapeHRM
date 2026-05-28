import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Plus, Edit, Trash2, Search, X, Loader2, UserCheck, UserX, 
  Calendar, Phone, Mail, Award, CheckCircle, AlertTriangle 
} from 'lucide-react';

const EmployeePage = () => {
  const { getAuthHeaders } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Trạng thái biểu mẫu Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editEmployee, setEditEmployee] = useState(null); // null = Thêm mới, object = Đang sửa
  
  // Trạng thái quản lý Vị trí công việc (Job Positions)
  const [positions, setPositions] = useState([]);
  const [isPositionModalOpen, setIsPositionModalOpen] = useState(false);
  const [editingPosition, setEditingPosition] = useState(null); // null = Thêm mới, object = Đang sửa
  const [posFormData, setPosFormData] = useState({ name: '', description: '' });

  // Các trường biểu mẫu form
  const [formData, setFormData] = useState({
    employee_id: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: '1',
    marital_status: 'Single',
    birthday: '',
    mobile: '',
    work_email: '',
    joined_date: '',
    state: 'ACTIVE',
    position_id: '',
  });

  // Trạng thái Toast thông báo
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  };

  // Fetch danh sách vị trí công việc từ API
  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/positions', {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setPositions(data);
      }
    } catch (err) {
      console.error('Fetch positions error:', err);
    }
  };

  // Fetch danh sách nhân viên từ API
  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/employees', {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setEmployees(data);
      } else {
        showToast('Không thể tải danh sách nhân viên.', 'error');
      }
    } catch (err) {
      console.error('Fetch employees error:', err);
      showToast('Lỗi mạng. Không thể kết nối API.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
    fetchPositions();
  }, []);

  // Vô hiệu hóa cuộn trang của body khi Modal đang mở
  useEffect(() => {
    if (isModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isModalOpen]);

  // Xử lý khi bấm nút "Thêm mới" để mở modal
  const handleOpenAddModal = async () => {
    setEditEmployee(null);
    let nextId = '';
    try {
      const response = await fetch('/api/employees/next-id', {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        nextId = data.next_id;
      }
    } catch (err) {
      console.error('Fetch next-id error:', err);
    }

    setFormData({
      employee_id: nextId,
      first_name: '',
      middle_name: '',
      last_name: '',
      gender: '1',
      marital_status: 'Single',
      birthday: '',
      mobile: '',
      work_email: '',
      joined_date: new Date().toISOString().split('T')[0], // Mặc định ngày hôm nay
      state: 'ACTIVE',
      position_id: '',
    });
    setIsModalOpen(true);
  };

  // Xử lý khi bấm nút "Sửa" nhân sự
  const handleOpenEditModal = (emp) => {
    setEditEmployee(emp);
    setFormData({
      employee_id: emp.employee_id || '',
      first_name: emp.first_name || '',
      middle_name: emp.middle_name || '',
      last_name: emp.last_name || '',
      gender: emp.gender !== null ? String(emp.gender) : '1',
      marital_status: emp.marital_status || 'Single',
      birthday: emp.birthday || '',
      mobile: emp.mobile || '',
      work_email: emp.work_email || '',
      joined_date: emp.joined_date || '',
      state: emp.state || 'ACTIVE',
      position_id: emp.position_id !== null ? String(emp.position_id) : '',
    });
    setIsModalOpen(true);
  };

  // Lưu thông tin form (Thêm mới hoặc Cập nhật)
  const handleSaveEmployee = async (e) => {
    e.preventDefault();
    
    if (!formData.first_name.trim() || !formData.last_name.trim()) {
      showToast('Họ và Tên nhân viên là bắt buộc.', 'error');
      return;
    }

    const payload = {
      ...formData,
      gender: parseInt(formData.gender),
      position_id: formData.position_id ? parseInt(formData.position_id) : null,
    };

    const isEdit = !!editEmployee;
    const url = isEdit ? `/api/employees/${editEmployee.id}` : '/api/employees';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(payload),
      });

      let resData = {};
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        resData = await response.json();
      }

      if (response.ok) {
        showToast(isEdit ? 'Cập nhật nhân viên thành công!' : 'Thêm nhân viên mới thành công!', 'success');
        setIsModalOpen(false);
        fetchEmployees(); // Tải lại danh sách
      } else {
        showToast(resData.error || `Lỗi hệ thống (${response.status}): Không thể lưu thông tin.`, 'error');
      }
    } catch (err) {
      console.error('Save employee error:', err);
      showToast('Lỗi xử lý dữ liệu hoặc không thể kết nối đến máy chủ.', 'error');
    }
  };

  // Xóa nhân sự khỏi hệ thống
  const handleDeleteEmployee = async (emp) => {
    const isConfirmed = window.confirm(`Bạn có chắc chắn muốn xóa nhân viên "${emp.full_name}" khỏi hệ thống không? Hành động này không thể hoàn tác.`);
    if (!isConfirmed) return;

    try {
      const response = await fetch(`/api/employees/${emp.id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        showToast('Xóa nhân viên thành công!', 'success');
        fetchEmployees();
      } else {
        let resData = {};
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          resData = await response.json();
        }
        showToast(resData.error || `Lỗi hệ thống (${response.status}): Không thể xóa nhân viên.`, 'error');
      }
    } catch (err) {
      console.error('Delete employee error:', err);
      showToast('Có lỗi mạng xảy ra khi xóa.', 'error');
    }
  };

  // Mở modal quản lý Vị trí
  const handleOpenPositionModal = () => {
    setEditingPosition(null);
    setPosFormData({ name: '', description: '' });
    setIsPositionModalOpen(true);
  };

  // Lưu Vị trí công việc (Thêm hoặc Cập nhật)
  const handleSavePosition = async (e) => {
    e.preventDefault();
    if (!posFormData.name.trim()) {
      showToast('Tên vị trí công việc không được để trống.', 'error');
      return;
    }

    const isEdit = !!editingPosition;
    const url = isEdit ? `/api/positions/${editingPosition.id}` : '/api/positions';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(posFormData),
      });

      let resData = {};
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        resData = await response.json();
      }

      if (response.ok) {
        showToast(isEdit ? 'Cập nhật vị trí thành công!' : 'Thêm vị trí mới thành công!', 'success');
        setPosFormData({ name: '', description: '' });
        setEditingPosition(null);
        fetchPositions();
        fetchEmployees();
      } else {
        showToast(resData.error || 'Không thể lưu vị trí công việc.', 'error');
      }
    } catch (err) {
      console.error('Save position error:', err);
      showToast('Lỗi kết nối máy chủ.', 'error');
    }
  };

  // Xóa vị trí công việc
  const handleDeletePosition = async (pos) => {
    const isConfirmed = window.confirm(`Bạn có chắc muốn xóa vị trí "${pos.name}"? Nhân viên thuộc vị trí này sẽ bị gán về trạng thái trống.`);
    if (!isConfirmed) return;

    try {
      const response = await fetch(`/api/positions/${pos.id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        showToast('Xóa vị trí thành công!', 'success');
        fetchPositions();
        fetchEmployees();
      } else {
        let resData = {};
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          resData = await response.json();
        }
        showToast(resData.error || 'Không thể xóa vị trí.', 'error');
      }
    } catch (err) {
      console.error('Delete position error:', err);
      showToast('Lỗi mạng khi xóa vị trí.', 'error');
    }
  };

  // Lọc danh sách nhân viên theo từ khóa tìm kiếm (Họ tên, mã NV, email)
  const filteredEmployees = employees.filter((emp) => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return true;
    
    return (
      emp.full_name?.toLowerCase().includes(query) ||
      emp.employee_id?.toLowerCase().includes(query) ||
      emp.work_email?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="fade-in">
      {/* Toast notifications container */}
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
        <span className="breadcrumb__item">Quản lý nhân viên</span>
      </div>

      {/* Header khu vực quản lý */}
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Hồ sơ nhân sự</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Xem, sửa, thêm mới và xóa thông tin nhân viên toàn doanh nghiệp.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn--secondary" onClick={handleOpenPositionModal}>
            <span>Quản lý Vị trí</span>
          </button>
          <button className="btn btn--primary" onClick={handleOpenAddModal}>
            <Plus size={16} />
            <span>Thêm nhân viên</span>
          </button>
        </div>
      </div>

      {/* Bộ lọc và Tìm kiếm */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div className="card__body" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '100%', maxWidth: '400px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', color: 'var(--color-text-muted)' }} />
            <input 
              type="text" 
              className="input" 
              placeholder="Tìm theo họ tên, mã nhân viên, email..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '38px' }}
            />
          </div>
        </div>
      </div>

      {/* Bảng dữ liệu nhân viên */}
      <div className="card card--no-hover">
        <div className="card__body" style={{ padding: 0 }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '64px', gap: '12px' }}>
              <Loader2 size={36} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
              <span style={{ color: 'var(--color-text-muted)', fontSize: '14px' }}>Đang tải danh sách nhân sự...</span>
            </div>
          ) : filteredEmployees.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '64px', gap: '8px' }}>
              <AlertTriangle size={36} style={{ color: 'var(--color-warning)' }} />
              <h4 style={{ fontWeight: 600, fontSize: '16px', color: 'var(--color-text-primary)' }}>Không tìm thấy nhân sự nào</h4>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>Hãy thử đổi từ khóa tìm kiếm hoặc thêm một nhân viên mới.</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table--zebra">
                <thead>
                  <tr>
                    <th>STT</th>
                    <th>Ảnh</th>
                    <th>Mã NV</th>
                    <th>Họ và Tên</th>
                    <th>Vị trí</th>
                    <th>Email Công việc</th>
                    <th>Ngày vào làm</th>
                    <th>Trạng thái</th>
                    <th style={{ textAlign: 'right' }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map((emp, index) => (
                    <tr key={emp.id}>
                      <td style={{ fontWeight: 500, color: 'var(--color-text-muted)', textAlign: 'center' }}>
                        {index + 1}
                      </td>
                      <td>
                        <div style={{ 
                          width: '36px', 
                          height: '36px', 
                          borderRadius: '50%', 
                          backgroundColor: 'var(--color-primary-light)', 
                          color: 'var(--color-primary)',
                          fontWeight: '700',
                          fontSize: '14px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          overflow: 'hidden'
                        }}>
                          {emp.profile_pic_url ? (
                            <img src={emp.profile_pic_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          ) : (
                            `${emp.first_name[0]}${emp.last_name[0]}`
                          )}
                        </div>
                      </td>
                      <td style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                        {emp.employee_id || '---'}
                      </td>
                      <td style={{ fontWeight: 500, color: 'var(--color-primary-dark)' }}>
                        {emp.full_name}
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {emp.position_name || <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>Không có</span>}
                      </td>
                      <td>{emp.work_email || '---'}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Calendar size={14} style={{ color: 'var(--color-text-muted)' }} />
                          <span>{emp.joined_date ? new Date(emp.joined_date).toLocaleDateString('vi-VN') : '---'}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${emp.state === 'ACTIVE' ? 'badge--success' : 'badge--danger'}`}>
                          {emp.state === 'ACTIVE' ? 'Đang làm' : 'Đã nghỉ'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                          <button 
                            className="btn btn--icon" 
                            title="Sửa thông tin"
                            onClick={() => handleOpenEditModal(emp)}
                          >
                            <Edit size={16} />
                          </button>
                          <button 
                            className="btn btn--icon btn--icon-danger" 
                            title="Xóa nhân sự"
                            onClick={() => handleDeleteEmployee(emp)}
                          >
                            <Trash2 size={16} />
                          </button>
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

      {/* Modal biểu mẫu Thêm/Sửa nhân viên */}
      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal__header">
              <h3 className="modal__title">
                {editEmployee ? `Sửa thông tin: ${editEmployee.full_name}` : 'Thêm hồ sơ nhân viên mới'}
              </h3>
              <button className="modal__close" onClick={() => setIsModalOpen(false)}>&times;</button>
            </div>
            
            <form onSubmit={handleSaveEmployee}>
              <div className="modal__body">
                
                {/* 1. Mã nhân sự & Vị trí công việc */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="employee_id">Mã nhân sự (ID)</label>
                    <input 
                      type="text" 
                      id="employee_id" 
                      className="input" 
                      value={formData.employee_id}
                      onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                      disabled
                      style={{ backgroundColor: '#e9ecef', cursor: 'not-allowed' }}
                    />
                    <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                      Mã nhân sự được hệ thống tự động thiết lập và không được phép chỉnh sửa.
                    </p>
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="position_id">Vị trí công việc</label>
                    <select 
                      id="position_id" 
                      className="input" 
                      value={formData.position_id}
                      onChange={(e) => setFormData({ ...formData, position_id: e.target.value })}
                      style={{ height: '40px' }}
                      required
                    >
                      <option value="">-- Chọn vị trí công việc --</option>
                      {positions.map((pos) => (
                        <option key={pos.id} value={pos.id}>{pos.name}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* 2. Trạng thái công việc & Tình trạng hôn nhân */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="state">Trạng thái công việc</label>
                    <select 
                      id="state" 
                      className="input" 
                      value={formData.state}
                      onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                      style={{ height: '40px' }}
                      required
                    >
                      <option value="ACTIVE">Đang làm việc (ACTIVE)</option>
                      <option value="TERMINATED">Đã chấm dứt (TERMINATED)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="marital_status">Hôn nhân</label>
                    <select 
                      id="marital_status" 
                      className="input" 
                      value={formData.marital_status}
                      onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                      style={{ height: '40px' }}
                    >
                      <option value="Single">Độc thân</option>
                      <option value="Married">Đã kết hôn</option>
                      <option value="Divorced">Đã ly hôn</option>
                    </select>
                  </div>
                </div>

                {/* 3. Họ và tên */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="first_name">Họ & Tên đệm</label>
                    <input 
                      type="text" 
                      id="first_name" 
                      className="input" 
                      placeholder="Nguyễn Văn" 
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="last_name">Tên chính</label>
                    <input 
                      type="text" 
                      id="last_name" 
                      className="input" 
                      placeholder="An" 
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      required
                    />
                  </div>
                </div>

                {/* 4. Giới tính & Ngày sinh */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="gender">Giới tính</label>
                    <select 
                      id="gender" 
                      className="input" 
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      style={{ height: '40px' }}
                      required
                    >
                      <option value="1">Nam</option>
                      <option value="2">Nữ</option>
                      <option value="3">Khác</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="birthday">Ngày sinh</label>
                    <input 
                      type="date" 
                      id="birthday" 
                      className="input" 
                      value={formData.birthday}
                      onChange={(e) => setFormData({ ...formData, birthday: e.target.value })}
                      required
                    />
                  </div>
                </div>

                {/* 5. Ngày vào làm & Số điện thoại */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="joined_date">Ngày vào làm</label>
                    <input 
                      type="date" 
                      id="joined_date" 
                      className="input" 
                      value={formData.joined_date}
                      onChange={(e) => setFormData({ ...formData, joined_date: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="mobile">Số điện thoại</label>
                    <input 
                      type="tel" 
                      id="mobile" 
                      className="input" 
                      placeholder="Ví dụ: 0987654321" 
                      value={formData.mobile}
                      onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                      required
                    />
                  </div>
                </div>

                {/* 6. Email công việc & Ảnh đại diện */}
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label form-label--required" htmlFor="work_email">Email công việc</label>
                    <input 
                      type="email" 
                      id="work_email" 
                      className="input" 
                      placeholder="Ví dụ: nv.an@company.com" 
                      value={formData.work_email}
                      onChange={(e) => setFormData({ ...formData, work_email: e.target.value })}
                      required
                    />
                  </div>
                  
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="profile_pic_file">Ảnh đại diện nhân viên</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                      {/* Vùng xem trước ảnh đại diện */}
                      <div style={{ 
                        width: '42px', 
                        height: '42px', 
                        borderRadius: '50%', 
                        backgroundColor: 'var(--color-primary-light)', 
                        color: 'var(--color-primary)',
                        fontWeight: '700',
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden',
                        border: '2px solid var(--color-border-light)',
                        flexShrink: 0
                      }}>
                        {formData.profile_pic_url ? (
                          <img src={formData.profile_pic_url} alt="Xem trước" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                          formData.first_name && formData.last_name ? `${formData.first_name[0]}${formData.last_name[0]}` : '?'
                        )}
                      </div>

                      {/* Ô tải file lên */}
                      <div style={{ flex: 1, minWidth: '150px' }}>
                        <input 
                          type="file" 
                          id="profile_pic_file" 
                          accept="image/*"
                          className="input" 
                          onChange={(e) => {
                            const file = e.target.files[0];
                            if (file) {
                              if (file.size > 2 * 1024 * 1024) {
                                showToast('Kích thước ảnh đại diện không được vượt quá 2MB.', 'error');
                                e.target.value = '';
                                return;
                              }
                              const reader = new FileReader();
                              reader.onloadend = () => {
                                setFormData({ ...formData, profile_pic_url: reader.result });
                              };
                              reader.readAsDataURL(file);
                            }
                          }}
                          style={{ padding: '8px 12px' }}
                        />
                        <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                          Chấp nhận PNG, JPG (Tối đa 2MB).
                        </p>
                      </div>

                      {/* Nút xóa ảnh hiện tại */}
                      {formData.profile_pic_url && (
                        <button 
                          type="button" 
                          className="btn btn--secondary" 
                          onClick={() => {
                            setFormData({ ...formData, profile_pic_url: '' });
                            const fileInput = document.getElementById('profile_pic_file');
                            if (fileInput) fileInput.value = '';
                          }}
                          style={{ padding: '6px 12px', fontSize: '12px', borderColor: 'var(--color-error)', color: 'var(--color-error)' }}
                        >
                          Xóa ảnh
                        </button>
                      )}
                    </div>
                  </div>
                </div>

              </div>
              <div className="modal__footer">
                <button type="button" className="btn btn--secondary" onClick={() => setIsModalOpen(false)}>
                  Hủy bỏ
                </button>
                <button type="submit" className="btn btn--primary">
                  Lưu hồ sơ
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Quản lý Vị trí công việc */}
      {isPositionModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '600px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Quản lý Vị trí công việc</h3>
              <button className="modal__close" onClick={() => setIsPositionModalOpen(false)}>&times;</button>
            </div>
            <div className="modal__body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              
              {/* Form thêm/sửa vị trí */}
              <form onSubmit={handleSavePosition} style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '6px', border: '1px solid #dee2e6' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--color-primary-dark)' }}>
                  {editingPosition ? `Chỉnh sửa vị trí: ${editingPosition.name}` : 'Thêm vị trí công việc mới'}
                </h4>
                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label className="form-label form-label--required" htmlFor="pos_name">Tên vị trí</label>
                  <input
                    type="text"
                    id="pos_name"
                    className="input"
                    placeholder="Ví dụ: IT, Bảo vệ, Lễ tân,..."
                    value={posFormData.name}
                    onChange={(e) => setPosFormData({ ...posFormData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group" style={{ marginBottom: '16px' }}>
                  <label className="form-label" htmlFor="pos_description">Mô tả chi tiết</label>
                  <input
                    type="text"
                    id="pos_description"
                    className="input"
                    placeholder="Mô tả công việc (không bắt buộc)"
                    value={posFormData.description || ''}
                    onChange={(e) => setPosFormData({ ...posFormData, description: e.target.value })}
                  />
                </div>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  {editingPosition && (
                    <button
                      type="button"
                      className="btn btn--secondary"
                      onClick={() => {
                        setEditingPosition(null);
                        setPosFormData({ name: '', description: '' });
                      }}
                      style={{ padding: '6px 12px', fontSize: '13px' }}
                    >
                      Hủy sửa
                    </button>
                  )}
                  <button
                    type="submit"
                    className="btn btn--primary"
                    style={{ padding: '6px 16px', fontSize: '13px' }}
                  >
                    {editingPosition ? 'Cập nhật' : 'Thêm mới'}
                  </button>
                </div>
              </form>

              {/* Danh sách vị trí hiện có */}
              <h4 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--color-text-primary)' }}>
                Danh sách Vị trí hiện tại ({positions.length})
              </h4>
              
              {positions.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', fontStyle: 'italic', textAlign: 'center', padding: '16px' }}>
                  Chưa có vị trí công việc nào được định nghĩa.
                </p>
              ) : (
                <div className="table-responsive" style={{ border: '1px solid #dee2e6', borderRadius: '4px' }}>
                  <table className="table" style={{ fontSize: '13px' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f1f3f5' }}>
                        <th style={{ padding: '10px' }}>Tên vị trí</th>
                        <th style={{ padding: '10px' }}>Mô tả</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      {positions.map((pos) => (
                        <tr key={pos.id}>
                          <td style={{ fontWeight: 600, padding: '10px' }}>{pos.name}</td>
                          <td style={{ color: 'var(--color-text-muted)', padding: '10px' }}>{pos.description || '---'}</td>
                          <td style={{ padding: '10px', textAlign: 'right' }}>
                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                              <button
                                type="button"
                                className="btn btn--icon"
                                style={{ width: '28px', height: '28px' }}
                                title="Sửa vị trí"
                                onClick={() => {
                                  setEditingPosition(pos);
                                  setPosFormData({ name: pos.name, description: pos.description || '' });
                                }}
                              >
                                <Edit size={13} />
                              </button>
                              <button
                                type="button"
                                className="btn btn--icon btn--icon-danger"
                                style={{ width: '28px', height: '28px' }}
                                title="Xóa vị trí"
                                onClick={() => handleDeletePosition(pos)}
                              >
                                <Trash2 size={13} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="modal__footer">
              <button type="button" className="btn btn--secondary" onClick={() => setIsPositionModalOpen(false)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EmployeePage;
