import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, CalendarDays, Clock, Clock4, ClipboardList, Settings, Mail, MapPin, BarChart3, Wallet, Receipt, Building2, FileSignature, Briefcase, Target } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ isOpen, onCloseSidebar }) => {
  const { user } = useAuth();
  
  const isAdminOrHR = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'hr_manager';
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const menuItems = [
    ...(user?.role === 'super_admin' ? [{ name: 'Quản lý Tổ chức', path: '/super-admin', icon: Building2 }] : []),
    ...(isAdminOrHR ? [{ name: 'Dashboard', path: '/', icon: LayoutDashboard }] : []),
    { name: 'Thông tin cá nhân', path: '/profile', icon: Users },
    ...(isAdminOrHR ? [{ name: 'Quản lý nhân viên', path: '/employees', icon: Users }] : []),
    ...(isAdminOrHR ? [{ name: 'Hợp đồng lao động', path: '/contracts', icon: FileSignature }] : []),
    ...(isAdminOrHR ? [{ name: 'Tuyển dụng', path: '/recruitment', icon: Briefcase }] : []),
    { name: 'Đánh giá hiệu suất', path: '/performance', icon: Target },
    { name: 'Nghỉ phép', path: '/leave', icon: CalendarDays },
    { name: 'Chấm công', path: '/attendance', icon: Clock },
    { name: 'Tăng ca', path: '/overtime', icon: Clock4 },
    ...(isAdminOrHR ? [{ name: 'Cấu hình chấm công', path: '/work-config', icon: MapPin }] : []),
    ...(isAdminOrHR ? [{ name: 'Chính sách phép', path: '/leave-policy', icon: ClipboardList }] : []),
    ...(isAdminOrHR ? [{ name: 'Báo cáo', path: '/reports', icon: BarChart3 }] : []),
    ...(isAdminOrHR ? [{ name: 'Cấu hình lương', path: '/salary-config', icon: Wallet }] : []),
    ...(isAdminOrHR ? [{ name: 'Bảng lương', path: '/payroll', icon: Receipt }] : []),
    ...(user?.role === 'employee' ? [{ name: 'Phiếu lương', path: '/my-payslip', icon: Receipt }] : []),
    ...(isAdmin ? [{ name: 'Cấu hình Email', path: '/email-settings', icon: Mail }] : []),
    ...(isAdmin ? [{ name: 'Hệ thống & Bảo mật', path: '/settings', icon: Settings }] : []),
  ];

  const handleLinkClick = () => {
    if (window.innerWidth <= 768) {
      onCloseSidebar();
    }
  };

  return (
    <>
      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="sidebar-overlay" onClick={onCloseSidebar} />
      )}

      <aside className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}>
        <ul className="sidebar__menu">
          {menuItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <li className="sidebar__item" key={idx}>
                <NavLink
                  to={item.path}
                  onClick={handleLinkClick}
                  className={({ isActive }) => 
                    `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`
                  }
                  end={item.path === '/'}
                >
                  <Icon className="sidebar__icon" size={18} />
                  <span>{item.name}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </aside>
    </>
  );
};

export default Sidebar;
