import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, UserPlus, CalendarDays, Settings, ShieldAlert } from 'lucide-react';

const Sidebar = ({ isOpen, onCloseSidebar }) => {
  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Quản lý nhân viên', path: '/employees', icon: Users },
    { name: 'Tuyển dụng', path: '/recruitment', icon: UserPlus },
    { name: 'Thời gian & Nghỉ phép', path: '/leave', icon: CalendarDays },
    { name: 'Hệ thống & Bảo mật', path: '/settings', icon: Settings },
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
