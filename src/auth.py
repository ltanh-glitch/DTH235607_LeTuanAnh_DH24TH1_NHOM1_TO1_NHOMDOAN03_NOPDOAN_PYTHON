# -*- coding: utf-8 -*-
import pyodbc

# ==========================
# KẾT NỐI SQL SERVER
# ==========================
def get_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=LAPTOP-TUANANH;'      # 👈 Tên máy của bạn
            'DATABASE=QuanLyBanHang;'     # 👈 Tên CSDL
            'UID=sa;'                     # 👈 Tài khoản sa
            'PWD=123;'                    # 👈 Mật khẩu
            'TrustServerCertificate=yes;' # Tránh lỗi SSL
        )
        # Để pyodbc tự động xử lý encoding (không force UTF-8)
        return conn
    except Exception as e:
        # Giữ lại print để bạn thấy lỗi kết nối trong console
        print("❌ Lỗi kết nối SQL Server:", e) 
        return None


# ==========================
# HÀM KIỂM TRA ĐĂNG NHẬP
# ==========================
def verify_login(username, password):
    conn = get_connection()
    if conn is None:
        # Đã cập nhật thông báo lỗi rõ ràng hơn
        return False, None, "Không thể kết nối đến cơ sở dữ liệu. Vui lòng kiểm tra lại cấu hình kết nối."

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tk.TenDangNhap, tk.MatKhau, tk.PhanQuyen, tk.TrangThai, nv.TenNhanVien, nv.MaNhanVien
            FROM tblTaiKhoan tk
            LEFT JOIN tblNhanVien nv ON tk.MaNhanVien = nv.MaNhanVien
            WHERE tk.TenDangNhap = ? AND tk.MatKhau = ?
        """, (username, password))

        row = cursor.fetchone()
        if not row:
            return False, None, "Sai tên đăng nhập hoặc mật khẩu."

        ten_dang_nhap, mat_khau, phan_quyen, trang_thai, ten_nhan_vien, ma_nhan_vien = row

        # Kiểm tra trạng thái tài khoản
        if trang_thai == 0:
            return False, None, "Tài khoản đã bị khóa."

        # ✅ Thông tin người dùng
        user_info = {
            "TenDangNhap": ten_dang_nhap,
            "PhanQuyen": phan_quyen,
            "HoTen": ten_nhan_vien if ten_nhan_vien else "Không rõ",
            "MaNhanVien": ma_nhan_vien
        }

        return True, user_info, "Đăng nhập thành công."

    except Exception as e:
        return False, None, f"Lỗi truy vấn: {e}"
    finally:
        if conn:
            conn.close()
