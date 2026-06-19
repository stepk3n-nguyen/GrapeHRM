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
import EmailSettingsPage from './pages/EmailSettingsPage';
import ProfilePage from './pages/ProfilePage';
import SettingsPage from './pages/SettingsPage';
import WorkConfigPage from './pages/WorkConfigPage';
import ReportsPage from './pages/ReportsPage';
import SalaryConfigPage from './pages/SalaryConfigPage';
import PayrollPage from './pages/PayrollPage';
import MyPayslipPage from './pages/MyPayslipPage';
import OvertimePage from './pages/OvertimePage';
import ContractsPage from './pages/ContractsPage';
import RecruitmentPage from './pages/RecruitmentPage';
import PerformancePage from './pages/PerformancePage';
import SuperAdminPage from './pages/SuperAdminPage';
import { Loader2 } from 'lucide-react';

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
                  <Route path="/overtime" element={<OvertimePage />} />
                  <Route path="/performance" element={<PerformancePage />} />
                  <Route path="/my-payslip" element={<MyPayslipPage />} />
                  <Route path="/" element={<Navigate to="/profile" replace />} />
                  <Route path="*" element={<Navigate to="/profile" replace />} />
                </>
              ) : (
                <>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/employees" element={<EmployeePage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/leave" element={<LeavePage />} />
                  <Route path="/attendance" element={<AttendancePage />} />
                  <Route path="/work-config" element={<WorkConfigPage />} />
                  <Route path="/overtime" element={<OvertimePage />} />
                  <Route path="/contracts" element={<ContractsPage />} />
                  <Route path="/recruitment" element={<RecruitmentPage />} />
                  <Route path="/performance" element={<PerformancePage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/salary-config" element={<SalaryConfigPage />} />
                  <Route path="/payroll" element={<PayrollPage />} />
                  <Route path="/leave-policy" element={<LeavePolicyPage />} />
                  <Route path="/email-settings" element={<EmailSettingsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  {user?.role === 'super_admin' && <Route path="/super-admin" element={<SuperAdminPage />} />}
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
