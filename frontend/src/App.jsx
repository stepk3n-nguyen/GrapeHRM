import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import EmployeePage from './pages/EmployeePage';
import LeavePage from './pages/LeavePage';
import AttendancePage from './pages/AttendancePage';
import LeavePolicyPage from './pages/LeavePolicyPage';
import ProfilePage from './pages/ProfilePage';
import { Loader2 } from 'lucide-react';

// Thành phần Component Mock cho các trang chưa phát triển trong Phase này
const MockPage = ({ title }) => (
  <div className="fade-in">
    <div className="breadcrumb">
      <span>GrapeHRM</span>
      <span>&gt;</span>
      <span className="breadcrumb__item">{title}</span>
    </div>
    <div className="card">
      <div className="card__header">
        <h3 className="card__title">{title}</h3>
      </div>
      <div className="card__body" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <h4 style={{ fontWeight: 600, fontSize: '18px', color: 'var(--color-primary)', marginBottom: '8px' }}>
          Phân hệ đang hoàn thiện
        </h4>
        <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
          Cảm ơn bạn đã quan tâm. Tính năng liên quan đến <strong>{title}</strong> đang trong quá trình lập trình tích hợp. Vui lòng trải nghiệm tính năng Quản lý nhân viên!
        </p>
      </div>
    </div>
  </div>
);

// Trình bảo vệ tuyến đường đăng nhập (Authentication Guard)
const AppContent = () => {
  const { user, token, loading } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => 
    typeof window !== 'undefined' ? window.innerWidth > 768 : false
  );

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const closeSidebar = () => {
    setIsSidebarOpen(false);
  };

  // Hiển thị vòng xoay loading khi đang xác thực session JWT
  if (loading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        gap: '12px',
        backgroundColor: 'var(--color-bg)'
      }}>
        <Loader2 size={42} className="animate-spin" style={{ color: 'var(--color-primary)' }} />
        <span style={{ color: 'var(--color-text-muted)', fontSize: '14px', fontWeight: 500 }}>
          Đang khôi phục phiên hoạt động...
        </span>
      </div>
    );
  }

  // Nếu chưa đăng nhập, chỉ hiển thị trang Login
  if (!token) {
    return <LoginPage />;
  }

  // Đã đăng nhập -> Hiển thị khung Layout hoàn chỉnh của GrapeHRM
  return (
    <div className="app">
      <Header onToggleSidebar={toggleSidebar} />
      
      <div className="app__body">
        <Sidebar isOpen={isSidebarOpen} onCloseSidebar={closeSidebar} />
        
        <main className={`app__workspace ${isSidebarOpen ? 'app__workspace--shifted' : ''}`}>
          <div className="app__content">
            <Routes>
              {user?.role === 'employee' ? (
                <>
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/leave" element={<LeavePage />} />
                  <Route path="/attendance" element={<AttendancePage />} />
                  <Route path="/" element={<Navigate to="/profile" replace />} />
                  <Route path="*" element={<Navigate to="/profile" replace />} />
                </>
              ) : (
                <>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/employees" element={<EmployeePage />} />
                  {user?.role !== 'admin' && <Route path="/profile" element={<ProfilePage />} />}
                  <Route path="/leave" element={<LeavePage />} />
                  <Route path="/attendance" element={<AttendancePage />} />
                  <Route path="/leave-policy" element={<LeavePolicyPage />} />
                  <Route path="/settings" element={<MockPage title="Hệ thống & Bảo mật (Settings)" />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </>
              )}
            </Routes>
          </div>
          
          <Footer />
        </main>
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
