import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, User, Users, CalendarDays, Clock, Clock4, ClipboardList, Settings, Mail, MapPin, BarChart3, Wallet, Receipt, Building2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ isOpen, onCloseSidebar }) => {
  const { user } = useAuth();

  const isAdminOrHR = user?.role === 'admin' || user?.role === 'super_admin' || user?.role === 'hr_manager';
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  const menuItems = [
    ...(user?.role === 'super_admin' ? [{ name: 'Quản lý Tổ chức', path: '/super-admin', icon: Building2 }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Dashboard', path: '/', icon: LayoutDashboard }] : []),
    ...(user?.tenant_id ? [{ name: 'Thông tin cá nhân', path: '/profile', icon: User }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Quản lý nhân viên', path: '/employees', icon: Users }] : []),
    ...(user?.tenant_id ? [{ name: 'Nghỉ phép', path: '/leave', icon: CalendarDays }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Chính sách phép', path: '/leave-policy', icon: ClipboardList }] : []),
    ...(user?.tenant_id ? [{ name: 'Chấm công', path: '/attendance', icon: Clock }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Cấu hình chấm công', path: '/work-config', icon: MapPin }] : []),
    ...(user?.tenant_id ? [{ name: 'Tăng ca', path: '/overtime', icon: Clock4 }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Báo cáo', path: '/reports', icon: BarChart3 }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Bảng lương', path: '/payroll', icon: Receipt }] : []),
    ...(isAdminOrHR && user?.tenant_id ? [{ name: 'Cấu hình lương', path: '/salary-config', icon: Wallet }] : []),
    ...(user?.role === 'employee' && user?.tenant_id ? [{ name: 'Phiếu lương', path: '/my-payslip', icon: Receipt }] : []),
    ...(isAdmin && user?.tenant_id ? [{ name: 'Cấu hình Email', path: '/email-settings', icon: Mail }] : []),
    ...(isAdmin && user?.tenant_id ? [{ name: 'Hệ thống & Bảo mật', path: '/settings', icon: Settings }] : []),
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
