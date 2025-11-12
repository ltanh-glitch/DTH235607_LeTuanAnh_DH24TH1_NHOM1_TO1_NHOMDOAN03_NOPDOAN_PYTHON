# -*- coding: utf-8 -*-
# login_form.py - Form đăng nhập cho hệ thống quản lý bán hàng (Phiên bản nâng cao)
import tkinter as tk
from tkinter import messagebox
from auth import verify_login
from splash_form import center_window
# from PIL import Image, ImageTk # Không cần nếu không dùng hình ảnh

class LoginForm:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success = on_success_callback
        self.show_pass_var = tk.BooleanVar() # Biến để lưu trạng thái checkbox
        self.setup_ui()

    def setup_ui(self):
        # 1. Cấu hình cơ bản
        self.root.title("Đăng nhập - Quản lý Bán hàng")
        center_window(self.root, 480, 480) # Tăng nhẹ chiều cao để chứa checkbox
        self.root.resizable(False, False)
        self.root.configure(bg="#E0E0E0")

        # 2. Frame chính với padding
        main_frame = tk.Frame(self.root, bg="white", padx=40, pady=40, bd=1, relief=tk.SOLID)
        main_frame.pack(expand=True, fill="both", padx=30, pady=30)

        # 3. Tiêu đề
        tk.Label(main_frame, text="🔑 ĐĂNG NHẬP HỆ THỐNG",
                 font=("Arial", 18, "bold"), bg="white", fg="#0288D1").pack(pady=(0, 30))
        
        # 4. Input Tài khoản
        tk.Label(main_frame, text="Tên đăng nhập:", font=("Arial", 11, "bold"), bg="white", fg="#424242").pack(anchor="w", pady=(5, 0))
        self.entry_user = tk.Entry(main_frame, font=("Arial", 12), bd=1, relief=tk.FLAT, highlightthickness=1, highlightbackground="#BDBDBD", highlightcolor="#03A9F4", insertbackground="#03A9F4")
        self.entry_user.pack(fill="x", ipady=5, pady=(2, 20))
        self.entry_user.focus()

        # 5. Input Mật khẩu
        tk.Label(main_frame, text="Mật khẩu:", font=("Arial", 11, "bold"), bg="white", fg="#424242").pack(anchor="w", pady=(5, 0))
        self.entry_pass = tk.Entry(main_frame, font=("Arial", 12), show="●", bd=1, relief=tk.FLAT, highlightthickness=1, highlightbackground="#BDBDBD", highlightcolor="#03A9F4", insertbackground="#03A9F4")
        self.entry_pass.pack(fill="x", ipady=5, pady=(2, 10))
        
        # 6. Checkbox "Hiện mật khẩu"
        tk.Checkbutton(main_frame, text="Hiện mật khẩu", font=("Arial", 10), bg="white", fg="#424242",
                       variable=self.show_pass_var, command=self.toggle_password_visibility).pack(anchor="w", pady=(0, 30))

        # 7. Khung chứa nút (tạo một frame riêng để căn chỉnh)
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 8. Nút Đăng nhập (bên trái)
        self.btn_login = tk.Button(button_frame, text="ĐĂNG NHẬP", font=("Arial", 12, "bold"),
                                   bg="#4CAF50", fg="white", relief=tk.FLAT, cursor="hand2", # SỬ DỤNG tk.FLAT
                                   command=self.login, activebackground="#43A047", activeforeground="white")
        self.btn_login.pack(side=tk.LEFT, ipadx=10, ipady=8, expand=True, fill="x", padx=(0, 5)) # Căn trái
        
        # 9. Nút Thoát (bên phải)
        self.btn_exit = tk.Button(button_frame, text="THOÁT", font=("Arial", 12, "bold"),
                                  bg="#E53935", fg="white", relief=tk.FLAT, cursor="hand2", # SỬ DỤNG tk.FLAT
                                  command=self.exit_app, activebackground="#D32F2F", activeforeground="white")
        self.btn_exit.pack(side=tk.RIGHT, ipadx=10, ipady=8, expand=True, fill="x", padx=(5, 0)) # Căn phải

        # 10. Enter key & Gợi ý
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda e: self.login())
        
        # Cập nhật Demo để khớp với mật khẩu SQL mới
        tk.Label(main_frame, text="💡 Demo: admin / admin123 hoặc nhanvien / nhanvien123",
                 font=("Arial", 9, "italic"), bg="white", fg="#757575").pack(pady=(25, 0))


    # ==== Hàm xử lý Hiện/Ẩn mật khẩu ====
    def toggle_password_visibility(self):
        if self.show_pass_var.get():
            # Hiện mật khẩu
            self.entry_pass.config(show="") 
        else:
            # Ẩn mật khẩu bằng ký tự ●
            self.entry_pass.config(show="●")


    # ==== Xử lý đăng nhập (Giữ nguyên logic) ====
    def login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tài khoản và mật khẩu!")
            return

        self.btn_login.config(state=tk.DISABLED, text="ĐANG KIỂM TRA...")
        self.root.update()

        success, user_info, msg = verify_login(username, password)
        self.btn_login.config(state=tk.NORMAL, text="ĐĂNG NHẬP")

        if success:
            self.root.destroy()
            if self.on_success:
                self.on_success(user_info)
        else:
            messagebox.showerror("Đăng nhập thất bại", msg)
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.focus()

    # ==== Xử lý thoát (Giữ nguyên logic) ====
    def exit_app(self):
        if messagebox.askyesno("Thoát chương trình", "Bạn có chắc chắn muốn thoát không?"):
            self.root.destroy()

# ==== Test riêng ====
if __name__ == "__main__":
    def after_login(user):
        print("✅ Đăng nhập thành công:", user["HoTen"])
    root = tk.Tk()
    app = LoginForm(root, after_login)
    root.mainloop()