import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Menu, User } from 'lucide-react';
import logoIcon from '../assets/img/logo-white-trans-full.svg';

const Header = ({ onToggleSidebar }) => {
  const { user, logout, activeTenant } = useAuth();

  return (
    <header className="header">
      <div className="header__brand">
        <button
          className="btn btn--icon"
          onClick={onToggleSidebar}
          style={{ marginRight: '8px', color: 'white' }}
          aria-label="Toggle Navigation Sidebar"
        >
          <Menu size={20} />
        </button>
        <div className="header__logo" style={{ justifyContent: 'flex-start', background: 'transparent', padding: 0, display: 'flex', alignItems: 'center', width: 'auto' }}>
          <img src={logoIcon} alt="G" style={{ height: '28px', width: 'auto', objectFit: 'contain' }} />
        </div>
        
        {/* Render tenant name */}
        {( (user?.role === 'super_admin' && activeTenant?.name) || (user?.role !== 'super_admin' && user?.tenant_name) ) && (
          <div style={{ marginLeft: '16px', paddingLeft: '20px', borderLeft: '1px solid rgba(255,255,255,0.2)', color: 'white', display: 'flex', alignItems: 'center' }}>
            <span style={{ fontSize: '16px', fontWeight: 600, letterSpacing: '0.3px' }}>
              {user?.role === 'super_admin' ? activeTenant.name : user.tenant_name}
            </span>
          </div>
        )}
      </div>

      <div className="header__nav">
        {user && (
          <div className="header__user-info">
            <span className="header__username">
              {user.employee_full_name && user.employee_code
                ? `${user.employee_full_name} (${user.employee_code})`
                : user.username}
            </span>
            <span className="header__role">{user.role}</span>
          </div>
        )}

        <button className="header__logout-btn" onClick={logout}>
          <LogOut size={16} />
          <span>Đăng xuất</span>
        </button>
      </div>
    </header>
  );
};

export default Header;
