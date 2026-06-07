import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, CalendarDays, Clock, ClipboardList, Settings } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ isOpen, onCloseSidebar }) => {
  const { user } = useAuth();
  
  const isAdminOrHR = user?.role === 'admin' || user?.role === 'hr_manager';

  const menuItems = [
    ...(isAdminOrHR ? [{ name: 'Dashboard', path: '/', icon: LayoutDashboard }] : []),
    ...(user?.role !== 'admin' ? [{ name: 'Thông tin cá nhân', path: '/profile', icon: Users }] : []),
    ...(isAdminOrHR ? [{ name: 'Quản lý nhân viên', path: '/employees', icon: Users }] : []),
    { name: 'Nghỉ phép', path: '/leave', icon: CalendarDays },
    { name: 'Chấm công', path: '/attendance', icon: Clock },
    ...(isAdminOrHR ? [{ name: 'Chính sách phép', path: '/leave-policy', icon: ClipboardList }] : []),
    ...(user?.role === 'admin' ? [{ name: 'Hệ thống & Bảo mật', path: '/settings', icon: Settings }] : []),
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
