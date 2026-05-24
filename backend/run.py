"""
Entry point — khởi chạy Flask app.
Docker container chạy file này qua lệnh: flask run
Hoặc chạy trực tiếp: python run.py
"""

from app import create_app

# Tạo app instance — biến 'app' này được Flask CLI tự phát hiện
app = create_app()

if __name__ == "__main__":
    # Chỉ dùng khi chạy trực tiếp bằng python (không qua flask run)
    app.run(host="0.0.0.0", port=5000, debug=True)
