import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, Menu, User } from 'lucide-react';
import logoIcon from '../assets/img/logo-white-trans-full.svg';

const Header = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();

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
        <div className="header__logo" style={{ justifyContent: 'flex-start', background: 'transparent', padding: 0 }}>
          <img src={logoIcon} alt="G" style={{ width: '800%', height: '100%', objectFit: 'contain' }} />
        </div>
        {/* <h1 className="header__title">GrapeHRM</h1> */}
      </div>

      <div className="header__nav">
        {user && (
          <div className="header__user-info">
            <span className="header__username">{user.username}</span>
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
