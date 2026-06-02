import os
# pyrefly: ignore [missing-import]
from sqlalchemy import text
os.environ["DATABASE_URL"] = "mysql+pymysql://grapehrm_admin:grapehrm_secure_db_pwd_2026@localhost:3306/grapehrm"

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # 1. Update users
    print("Updating user roles...")
    db.session.execute(text("UPDATE users SET role='employee' WHERE role='supervisor'"))
    
    # 2. Alter users enum
    print("Altering users table...")
    db.session.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('super_admin','admin','hr_manager','employee') DEFAULT 'employee'"))
    
    # 3. Update leave requests
    print("Updating leave requests statuses...")
    db.session.execute(text("UPDATE leave_requests SET status='PENDING_HR' WHERE status='PENDING_SUPERVISOR'"))
    
    # 4. Alter leave_requests enum
    print("Altering leave_requests table...")
    db.session.execute(text("ALTER TABLE leave_requests MODIFY COLUMN status ENUM('PENDING_HR','APPROVED','REJECTED','CANCELLED') DEFAULT 'PENDING_HR'"))
    
    db.session.commit()
    print("Migration completed successfully.")
