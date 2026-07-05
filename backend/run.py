"""
Entry point — khởi chạy Flask app.
Chạy trực tiếp: python run.py  (hoặc: flask run)
"""

import sys

# Console Windows mặc định cp1252 → các print tiếng Việt sẽ crash.
# Ép stdout/stderr sang UTF-8 ngay từ đầu (an toàn cả khi đã là UTF-8).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from app import create_app  # noqa: E402

# Tạo app instance — biến 'app' này được Flask CLI tự phát hiện
app = create_app()

if __name__ == "__main__":
    # Chỉ dùng khi chạy trực tiếp bằng python (không qua flask run)
    app.run(host="0.0.0.0", port=5000, debug=True)
