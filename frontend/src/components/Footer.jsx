import React from 'react';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="footer">
      <p>&copy; {currentYear} GrapeHRM. Quản trị nhân sự thế hệ mới.</p>
    </footer>
  );
};

export default Footer;
