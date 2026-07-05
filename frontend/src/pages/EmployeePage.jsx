import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Plus, Edit, Trash2, Search, X, Loader2, UserCheck, UserX, 
  Calendar, Phone, Mail, Award, CheckCircle, AlertTriangle 
} from 'lucide-react';

const EmployeePage = () => {
  const { getAuthHeaders, user } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Trạng thái biểu mẫu Modal Nhân viên
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editEmployee, setEditEmployee] = useState(null); // null = Thêm mới, object = Đang sửa
  
  // Trạng thái quản lý Chức vụ (Job Titles)
  const [titles, setTitles] = useState([]);
  const [isTitleModalOpen, setIsTitleModalOpen] = useState(false);
  const [editingTitle, setEditingTitle] = useState(null);
  const [titleFormData, setTitleFormData] = useState({ name: '', description: '' });

  // Trạng thái quản lý Phòng ban (Departments)
  const [departments, setDepartments] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [isDeptModalOpen, setIsDeptModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState(null);
  const [deptFormData, setDeptFormData] = useState({ name: '', description: '' });

  // Các trường biểu mẫu form nhân viên
  const [formData, setFormData] = useState({
    employee_id: '',
    first_name: '',
    middle_name: '',
    last_name: '',
    gender: '1',
    marital_status: 'Single',
    birthday: '',
    num_dependents: 0,
    mobile: '',
    work_email: '',
    joined_date: '',
    end_date: '',
    address: '',
    title_id: '',
    department_id: '',
    shift_id: '',
    profile_pic_url: '',
    role: 'employee'
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

  const fetchTitles = async () => {
    try {
      const response = await fetch('/api/job-titles', {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setTitles(data);
      }
    } catch (err) {
      console.error('Fetch titles error:', err);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await fetch('/api/departments', {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const data = await response.json();
        setDepartments(data);
      }
    } catch (err) {
      console.error('Fetch departments error:', err);
    }
  };

  const fetchShifts = async () => {
    try {
      const response = await fetch('/api/work-shifts', { headers: getAuthHeaders() });
      if (response.ok) setShifts(await response.json());
    } catch (err) {
      console.error('Fetch shifts error:', err);
    }
  };

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
    fetchTitles();
    fetchDepartments();
    fetchShifts();
  }, []);

  // Vô hiệu hóa cuộn trang của body khi bất kỳ Modal nào đang mở
  useEffect(() => {
    if (isModalOpen || isTitleModalOpen || isDeptModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isModalOpen, isTitleModalOpen, isDeptModalOpen]);

  // Modal Nhân sự
  const handleOpenAddModal = async () => {
    setEditEmployee(null);
    let nextId = '';
    try {
      const response = await fetch('/api/employees/next-id', { headers: getAuthHeaders() });
      if (response.ok) {
        const data = await response.json();
        nextId = data.next_id;
      }
    } catch (err) { console.error(err); }

    setFormData({
      employee_id: nextId,
      first_name: '',
      middle_name: '',
      last_name: '',
      gender: '1',
      marital_status: 'Single',
      birthday: '',
      num_dependents: 0,
      mobile: '',
      work_email: '',
      joined_date: new Date().toISOString().split('T')[0],
      end_date: '',
      address: '',
      title_id: '',
      department_id: '',
      shift_id: '',
      profile_pic_url: '',
      role: 'employee'
    });
    setIsModalOpen(true);
  };

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
      num_dependents: emp.num_dependents || 0,
      mobile: emp.mobile || '',
      work_email: emp.work_email || '',
      joined_date: emp.joined_date || '',
      end_date: emp.end_date || '',
      address: emp.address || '',
      title_id: emp.title_id !== null ? String(emp.title_id) : '',
      department_id: emp.department_id !== null ? String(emp.department_id) : '',
      shift_id: emp.shift_id ? String(emp.shift_id) : '',
      profile_pic_url: emp.profile_pic_url || '',
      role: emp.role || 'employee'
    });
    setIsModalOpen(true);
  };

  const handleSaveEmployee = async (e) => {
    e.preventDefault();
    if (!formData.first_name.trim() || !formData.last_name.trim()) {
      showToast('Họ và Tên nhân viên là bắt buộc.', 'error');
      return;
    }

    const payload = {
      ...formData,
      gender: parseInt(formData.gender),
      title_id: formData.title_id ? parseInt(formData.title_id) : null,
      department_id: formData.department_id ? parseInt(formData.department_id) : null,
      shift_id: formData.shift_id ? parseInt(formData.shift_id) : null,
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
      const contentType = response.headers.get("content-type");
      let resData = {};
      if (contentType && contentType.includes("application/json")) {
        resData = await response.json();
      }

      if (response.ok) {
        showToast(isEdit ? 'Cập nhật nhân viên thành công!' : 'Thêm nhân viên mới thành công!', 'success');
        setIsModalOpen(false);
        fetchEmployees();
      } else {
        showToast(resData.error || `Lỗi hệ thống (${response.status})`, 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Lỗi xử lý dữ liệu.', 'error');
    }
  };

  const handleDeleteEmployee = async (emp) => {
    const isConfirmed = window.confirm(`Bạn có chắc chắn muốn xóa nhân viên "${emp.full_name}" khỏi hệ thống không?`);
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
        showToast('Không thể xóa nhân viên.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Có lỗi mạng xảy ra khi xóa.', 'error');
    }
  };

  // Modal Chức vụ (Title)
  const handleSaveTitle = async (e) => {
    e.preventDefault();
    if (!titleFormData.name.trim()) {
      showToast('Tên chức vụ không được để trống.', 'error');
      return;
    }

    const isEdit = !!editingTitle;
    const url = isEdit ? `/api/job-titles/${editingTitle.id}` : '/api/job-titles';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(titleFormData),
      });
      if (response.ok) {
        showToast(isEdit ? 'Cập nhật chức vụ thành công!' : 'Thêm chức vụ thành công!', 'success');
        setTitleFormData({ name: '', description: '' });
        setEditingTitle(null);
        fetchTitles();
        fetchEmployees();
      } else {
        const d = await response.json();
        showToast(d.error || 'Lỗi lưu chức vụ', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const handleDeleteTitle = async (pos) => {
    if (!window.confirm(`Xóa chức vụ "${pos.name}"?`)) return;
    try {
      const response = await fetch(`/api/job-titles/${pos.id}`, { method: 'DELETE', headers: getAuthHeaders() });
      if (response.ok) {
        showToast('Xóa chức vụ thành công', 'success');
        fetchTitles();
        fetchEmployees();
      } else {
        const d = await response.json();
        showToast(d.error || 'Không thể xóa', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  // Modal Phòng ban (Department)
  const handleSaveDepartment = async (e) => {
    e.preventDefault();
    if (!deptFormData.name.trim()) {
      showToast('Tên phòng ban không được để trống.', 'error');
      return;
    }

    const isEdit = !!editingDept;
    const url = isEdit ? `/api/departments/${editingDept.id}` : '/api/departments';
    const method = isEdit ? 'PUT' : 'POST';

    try {
      const response = await fetch(url, {
        method,
        headers: getAuthHeaders(),
        body: JSON.stringify(deptFormData),
      });
      if (response.ok) {
        showToast(isEdit ? 'Cập nhật phòng ban thành công!' : 'Thêm phòng ban thành công!', 'success');
        setDeptFormData({ name: '', description: '' });
        setEditingDept(null);
        fetchDepartments();
        fetchEmployees();
      } else {
        const d = await response.json();
        showToast(d.error || 'Lỗi lưu phòng ban', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

  const handleDeleteDepartment = async (dept) => {
    if (!window.confirm(`Xóa phòng ban "${dept.name}"?`)) return;
    try {
      const response = await fetch(`/api/departments/${dept.id}`, { method: 'DELETE', headers: getAuthHeaders() });
      if (response.ok) {
        showToast('Xóa phòng ban thành công', 'success');
        fetchDepartments();
        fetchEmployees();
      } else {
        const d = await response.json();
        showToast(d.error || 'Không thể xóa', 'error');
      }
    } catch (err) { showToast('Lỗi mạng', 'error'); }
  };

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

      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-primary-dark)' }}>Hồ sơ nhân sự</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginTop: '4px' }}>
            Xem, sửa, thêm mới và xóa thông tin nhân viên toàn doanh nghiệp.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn--secondary" onClick={() => setIsTitleModalOpen(true)}>
            <span>Quản lý Chức vụ</span>
          </button>
          <button className="btn btn--secondary" onClick={() => setIsDeptModalOpen(true)}>
            <span>Quản lý Phòng ban</span>
          </button>
          <button className="btn btn--primary" onClick={handleOpenAddModal}>
            <Plus size={16} />
            <span>Thêm nhân viên</span>
          </button>
        </div>
      </div>

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
                    <th>Vai trò</th>
                    <th>Chức vụ</th>
                    <th>Phòng ban</th>
                    <th>Email Công việc</th>
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
                      <td>
                        <span className={`badge ${emp.role === 'admin' ? 'badge--danger' : emp.role === 'hr_manager' ? 'badge--warning' : 'badge--primary'}`} style={{textTransform: 'capitalize'}}>
                          {emp.role ? emp.role.replace('_', ' ') : 'employee'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {emp.title_name || <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>Không có</span>}
                      </td>
                      <td style={{ fontWeight: 500 }}>
                        {emp.department_name || <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>Không có</span>}
                      </td>
                      <td>{emp.work_email || '---'}</td>
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
          <div className="modal" style={{ maxWidth: '800px' }}>
            <div className="modal__header">
              <h3 className="modal__title">
                {editEmployee ? `Sửa thông tin: ${editEmployee.full_name}` : 'Thêm hồ sơ nhân viên mới'}
              </h3>
              <button className="modal__close" type="button" onClick={() => setIsModalOpen(false)}>&times;</button>
            </div>
            
            <form onSubmit={handleSaveEmployee}>
              <div className="modal__body" style={{ maxHeight: '75vh', overflowY: 'auto' }}>
                
                {/* Custom CSS for 3-columns grid */}
                <style>{`
                  .form-grid-3 {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 16px;
                    margin-bottom: 16px;
                  }
                  @media (max-width: 768px) {
                    .form-grid-3 {
                      grid-template-columns: 1fr;
                    }
                  }
                `}</style>

                {/* Hàng 1 */}
                <div className="form-grid-3">
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="employee_id">Mã nhân sự</label>
                    <input 
                      type="text" 
                      id="employee_id" 
                      className="input" 
                      value={formData.employee_id}
                      disabled
                      style={{ backgroundColor: '#e9ecef', cursor: 'not-allowed' }}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="title_id">Chức vụ</label>
                    <select 
                      id="title_id" 
                      className="input" 
                      value={formData.title_id}
                      onChange={(e) => setFormData({ ...formData, title_id: e.target.value })}
                      required
                    >
                      <option value="">-- Chọn chức vụ --</option>
                      {titles.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="department_id">Phòng ban</label>
                    <select 
                      id="department_id" 
                      className="input" 
                      value={formData.department_id}
                      onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                      required
                    >
                      <option value="">-- Chọn phòng ban --</option>
                      {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="shift_id">Ca làm việc</label>
                    <select
                      id="shift_id"
                      className="input"
                      value={formData.shift_id}
                      onChange={(e) => setFormData({ ...formData, shift_id: e.target.value })}
                    >
                      <option value="">Ca mặc định của công ty</option>
                      {shifts.map((sh) => (
                        <option key={sh.id} value={sh.id}>
                          {sh.name} ({sh.start_time}-{sh.end_time}){sh.is_default ? ' — mặc định' : ''}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Hàng 2 */}
                <div className="form-grid-3">
                  <div className="form-group" style={{ marginBottom: 0 }}>
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
                  <div className="form-group" style={{ marginBottom: 0 }}>
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
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="gender">Giới tính</label>
                    <select 
                      id="gender" 
                      className="input" 
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      required
                    >
                      <option value="1">Nam</option>
                      <option value="2">Nữ</option>
                      <option value="3">Khác</option>
                    </select>
                  </div>
                </div>

                {/* Hàng 3 */}
                <div className="form-grid-3">
                  <div className="form-group" style={{ marginBottom: 0 }}>
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
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="marital_status">Hôn nhân</label>
                    <select 
                      id="marital_status" 
                      className="input" 
                      value={formData.marital_status}
                      onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                    >
                      <option value="Single">Độc thân</option>
                      <option value="Married">Đã kết hôn</option>
                      <option value="Divorced">Đã ly hôn</option>
                    </select>
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="num_dependents">Người phụ thuộc (giảm trừ thuế)</label>
                    <input
                      type="number"
                      id="num_dependents"
                      min="0"
                      className="input"
                      value={formData.num_dependents}
                      onChange={(e) => setFormData({ ...formData, num_dependents: e.target.value })}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="mobile">Số điện thoại</label>
                    <input 
                      type="tel" 
                      id="mobile" 
                      className="input" 
                      value={formData.mobile}
                      onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                      required
                    />
                  </div>
                </div>

                {/* Hàng 4 */}
                <div className="form-grid-3">
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="work_email">Email công việc</label>
                    <input 
                      type="email" 
                      id="work_email" 
                      className="input" 
                      value={formData.work_email}
                      onChange={(e) => setFormData({ ...formData, work_email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label form-label--required" htmlFor="joined_date">Ngày bắt đầu</label>
                    <input 
                      type="date" 
                      id="joined_date" 
                      className="input" 
                      value={formData.joined_date}
                      onChange={(e) => setFormData({ ...formData, joined_date: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="end_date">Ngày kết thúc</label>
                    <input 
                      type="date" 
                      id="end_date" 
                      className="input" 
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    />
                  </div>
                </div>

                {/* Hàng 5 */}
                <div style={{ marginBottom: '16px' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="address">Địa chỉ</label>
                    <input 
                      type="text" 
                      id="address" 
                      className="input" 
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành phố"
                    />
                  </div>
                </div>

                {/* Hàng Phân quyền (chỉ dành cho admin) */}
                {user?.role === 'admin' && (
                  <div style={{ marginBottom: '16px' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label className="form-label form-label--required" htmlFor="role">Vai trò hệ thống</label>
                      <select 
                        id="role" 
                        className="input" 
                        value={formData.role}
                        onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                        required
                      >
                        <option value="employee">Nhân viên (Employee)</option>
                        <option value="hr_manager">Quản lý Nhân sự (HR Manager)</option>
                        <option value="admin">Quản trị viên (Admin)</option>
                      </select>
                      <small style={{ color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
                        Tài khoản đăng nhập tự động là <b>nvXXX</b> với mật khẩu mặc định <b>123456</b>
                      </small>
                    </div>
                  </div>
                )}

                {/* Hàng 6 */}
                <div style={{ marginBottom: '16px' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label" htmlFor="profile_pic_file">Ảnh đại diện nhân viên</label>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ 
                        width: '42px', height: '42px', borderRadius: '50%', backgroundColor: 'var(--color-primary-light)', color: 'var(--color-primary)', fontWeight: '700', fontSize: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', border: '2px solid var(--color-border-light)', flexShrink: 0
                      }}>
                        {formData.profile_pic_url ? (
                          <img src={formData.profile_pic_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                          formData.first_name && formData.last_name ? `${formData.first_name[0]}${formData.last_name[0]}` : '?'
                        )}
                      </div>
                      <div style={{ flex: 1 }}>
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
                              reader.onloadend = () => setFormData({ ...formData, profile_pic_url: reader.result });
                              reader.readAsDataURL(file);
                            }
                          }}
                        />
                      </div>
                      {formData.profile_pic_url && (
                        <button 
                          type="button" 
                          className="btn btn--secondary" 
                          onClick={() => {
                            setFormData({ ...formData, profile_pic_url: '' });
                            const fileInput = document.getElementById('profile_pic_file');
                            if (fileInput) fileInput.value = '';
                          }}
                          style={{ borderColor: 'var(--color-error)', color: 'var(--color-error)' }}
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

      {/* Modal Quản lý Chức vụ */}
      {isTitleModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '600px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Quản lý Chức vụ</h3>
              <button className="modal__close" onClick={() => setIsTitleModalOpen(false)}>&times;</button>
            </div>
            <div className="modal__body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <form onSubmit={handleSaveTitle} style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '6px', border: '1px solid #dee2e6' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--color-primary-dark)' }}>
                  {editingTitle ? `Chỉnh sửa chức vụ: ${editingTitle.name}` : 'Thêm chức vụ mới'}
                </h4>
                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label className="form-label form-label--required">Tên chức vụ</label>
                  <input type="text" className="input" value={titleFormData.name} onChange={(e) => setTitleFormData({ ...titleFormData, name: e.target.value })} required />
                </div>
                <div className="form-group" style={{ marginBottom: '16px' }}>
                  <label className="form-label">Mô tả</label>
                  <input type="text" className="input" value={titleFormData.description || ''} onChange={(e) => setTitleFormData({ ...titleFormData, description: e.target.value })} />
                </div>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  {editingTitle && (
                    <button type="button" className="btn btn--secondary" onClick={() => { setEditingTitle(null); setTitleFormData({ name: '', description: '' }); }}>Hủy sửa</button>
                  )}
                  <button type="submit" className="btn btn--primary">{editingTitle ? 'Cập nhật' : 'Thêm mới'}</button>
                </div>
              </form>
              <h4 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Danh sách ({titles.length})</h4>
              <div className="table-responsive" style={{ border: '1px solid #dee2e6', borderRadius: '4px' }}>
                <table className="table">
                  <thead><tr style={{ backgroundColor: '#f1f3f5' }}><th>Tên chức vụ</th><th>Mô tả</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                  <tbody>
                    {titles.map((t) => (
                      <tr key={t.id}>
                        <td style={{ fontWeight: 600 }}>{t.name}</td>
                        <td style={{ color: 'var(--color-text-muted)' }}>{t.description || '---'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                            <button type="button" className="btn btn--icon" onClick={() => { setEditingTitle(t); setTitleFormData({ name: t.name, description: t.description || '' }); }}><Edit size={13} /></button>
                            <button type="button" className="btn btn--icon btn--icon-danger" onClick={() => handleDeleteTitle(t)}><Trash2 size={13} /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Quản lý Phòng ban */}
      {isDeptModalOpen && (
        <div className="modal-overlay">
          <div className="modal" style={{ maxWidth: '600px' }}>
            <div className="modal__header">
              <h3 className="modal__title">Quản lý Phòng ban</h3>
              <button className="modal__close" onClick={() => setIsDeptModalOpen(false)}>&times;</button>
            </div>
            <div className="modal__body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <form onSubmit={handleSaveDepartment} style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#f8f9fa', borderRadius: '6px', border: '1px solid #dee2e6' }}>
                <h4 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px', color: 'var(--color-primary-dark)' }}>
                  {editingDept ? `Chỉnh sửa phòng ban: ${editingDept.name}` : 'Thêm phòng ban mới'}
                </h4>
                <div className="form-group" style={{ marginBottom: '12px' }}>
                  <label className="form-label form-label--required">Tên phòng ban</label>
                  <input type="text" className="input" value={deptFormData.name} onChange={(e) => setDeptFormData({ ...deptFormData, name: e.target.value })} required />
                </div>
                <div className="form-group" style={{ marginBottom: '16px' }}>
                  <label className="form-label">Mô tả</label>
                  <input type="text" className="input" value={deptFormData.description || ''} onChange={(e) => setDeptFormData({ ...deptFormData, description: e.target.value })} />
                </div>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  {editingDept && (
                    <button type="button" className="btn btn--secondary" onClick={() => { setEditingDept(null); setDeptFormData({ name: '', description: '' }); }}>Hủy sửa</button>
                  )}
                  <button type="submit" className="btn btn--primary">{editingDept ? 'Cập nhật' : 'Thêm mới'}</button>
                </div>
              </form>
              <h4 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Danh sách ({departments.length})</h4>
              <div className="table-responsive" style={{ border: '1px solid #dee2e6', borderRadius: '4px' }}>
                <table className="table">
                  <thead><tr style={{ backgroundColor: '#f1f3f5' }}><th>Tên phòng ban</th><th>Mô tả</th><th style={{ textAlign: 'right' }}>Thao tác</th></tr></thead>
                  <tbody>
                    {departments.map((d) => (
                      <tr key={d.id}>
                        <td style={{ fontWeight: 600 }}>{d.name}</td>
                        <td style={{ color: 'var(--color-text-muted)' }}>{d.description || '---'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                            <button type="button" className="btn btn--icon" onClick={() => { setEditingDept(d); setDeptFormData({ name: d.name, description: d.description || '' }); }}><Edit size={13} /></button>
                            <button type="button" className="btn btn--icon btn--icon-danger" onClick={() => handleDeleteDepartment(d)}><Trash2 size={13} /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default EmployeePage;
