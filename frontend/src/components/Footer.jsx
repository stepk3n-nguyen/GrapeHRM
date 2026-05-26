import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="footer">
      <p>&copy; {currentYear} GrapeHRM. Tất cả quyền được bảo lưu. Thiết kế theo tiêu chuẩn cao cấp.</p>
    </footer>
  );
};

export default Footer;
