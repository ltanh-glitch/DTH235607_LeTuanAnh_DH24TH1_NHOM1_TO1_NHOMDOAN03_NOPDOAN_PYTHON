# -*- coding: utf-8 -*-
# main_form.py - Form Chính (Main Form) với giao diện Sidebar và logic Phân quyền
import tkinter as tk
from tkinter import messagebox, ttk
import sys
from splash_form import center_window, SplashScreen
from auth import verify_login 
import pyodbc # Cần thiết cho các hàm DB mô phỏng

# Đảm bảo console (nếu có log) dùng UTF-8 để không lỗi Unicode khi in tiếng Việt
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# 1. IMPORT MODULES (Giữ nguyên)
try:
    from product_management_form import ProductManagementForm 
    from customer_management_form import CustomerManagementForm 
    from employee_management_form import EmployeeManagementForm 
    from account_management_form import AccountManagementForm 
    from revenue_report_form import DetailedInvoiceReportForm
    from sales_invoice_form import SalesInvoiceForm
except ImportError as e:
    print(f"❌ Lỗi Import Modules: Vui lòng đảm bảo các file form có trong thư mục. Chi tiết: {e}")
    ProductManagementForm = None 
    CustomerManagementForm = None 
    EmployeeManagementForm = None
    AccountManagementForm = None
    RevenueReportForm = None
    SalesInvoiceForm = None
    DetailedInvoiceReportForm = None

# ==========================================================
# LỚP BẢNG ĐIỀU KHIỂN (DASHBOARD) MỚI
# ==========================================================

class Dashboard:
    def __init__(self, master, user_info):
        self.master = master
        self.user_info = user_info
        self.user_role = user_info['PhanQuyen']
        self.setup_ui()

    def get_conn(self):
        # Dùng lại hàm get_conn từ auth.py (Giả định)
        try:
            from auth import get_connection
            return get_connection()
        except Exception:
            return None
        
    def fetch_stats(self):
        """Mô phỏng/Thực hiện tải các số liệu thống kê từ DB."""
        stats = {
            "TotalRevenue": 0, "TotalOrders": 0, "TotalProducts": 0, "TotalCustomers": 0, "TopProduct": "N/A"
        }
        
        # Nếu là ADMIN/QUẢN LÝ (role 0, 1) thì mới hiển thị doanh thu
        if self.user_role in [0, 1]:
            conn = self.get_conn()
            if conn:
                try:
                    cursor = conn.cursor()
                    
                    # 1. Tổng doanh thu (Tổng TongTien từ tblHDBan)
                    cursor.execute("SELECT ISNULL(SUM(TongTien), 0) FROM tblHDBan")
                    stats["TotalRevenue"] = cursor.fetchone()[0]
                    
                    # 2. Tổng số đơn hàng
                    cursor.execute("SELECT COUNT(MaHDBan) FROM tblHDBan")
                    stats["TotalOrders"] = cursor.fetchone()[0]
                    
                    # 3. Tổng số sản phẩm
                    cursor.execute("SELECT COUNT(MaHang) FROM tblHang")
                    stats["TotalProducts"] = cursor.fetchone()[0]
                    
                    # 4. Tổng số khách hàng
                    cursor.execute("SELECT COUNT(MaKhach) FROM tblKhach")
                    stats["TotalCustomers"] = cursor.fetchone()[0]

                    # 5. Top sản phẩm bán chạy nhất (ví dụ: theo số lượng)
                    cursor.execute("""
                        SELECT TOP 1 h.TenHang, SUM(ct.SoLuong) AS TotalSL
                        FROM tblChiTietHDBan ct
                        JOIN tblHang h ON ct.MaHang = h.MaHang
                        GROUP BY h.TenHang
                        ORDER BY TotalSL DESC
                    """)
                    top_row = cursor.fetchone()
                    if top_row:
                         stats["TopProduct"] = f"{top_row[0]} ({top_row[1]} SP)"
                    
                except Exception as e:
                    print(f"Lỗi tải thống kê DB: {e}")
                finally:
                    conn.close()
        else:
             # Dữ liệu cho Nhân viên (chỉ được xem những thứ không liên quan đến tiền)
            conn = self.get_conn()
            if conn:
                try:
                     cursor = conn.cursor()
                     cursor.execute("SELECT COUNT(MaHang) FROM tblHang")
                     stats["TotalProducts"] = cursor.fetchone()[0]
                     cursor.execute("SELECT COUNT(MaKhach) FROM tblKhach")
                     stats["TotalCustomers"] = cursor.fetchone()[0]
                except Exception:
                     pass
                finally:
                    conn.close()

        return stats

    def setup_ui(self):
        # 1. Header
        tk.Label(self.master, text="📊 BẢNG ĐIỀU KHIỂN CHÍNH",
                 font=("Arial", 20, "bold"), fg="#00796B", bg="#ECEFF1").pack(pady=(20, 15))
        
        # 2. Khung thống kê chính (KPI Cards)
        kpi_frame = tk.Frame(self.master, bg="#ECEFF1", padx=10, pady=10)
        kpi_frame.pack(fill="x", pady=10)

        stats = self.fetch_stats()

        # Danh sách các thẻ KPI
        kpi_cards = [
            {"title": "Tổng Doanh thu (VND)", "value": f"{stats['TotalRevenue']:,.0f}", "color": "#4CAF50", "visible": self.user_role in [0, 1], "icon": "💵"},
            {"title": "Tổng Đơn hàng", "value": f"{stats['TotalOrders']:,.0f}", "color": "#03A9F4", "visible": self.user_role in [0, 1], "icon": "🧾"},
            {"title": "Tổng Sản phẩm", "value": f"{stats['TotalProducts']:,.0f}", "color": "#FFC107", "visible": True, "icon": "📦"},
            {"title": "Tổng Khách hàng", "value": f"{stats['TotalCustomers']:,.0f}", "color": "#795548", "visible": True, "icon": "👤"},
        ]

        # Tạo các thẻ
        col = 0
        for card in kpi_cards:
            if card["visible"]:
                self.create_kpi_card(kpi_frame, card["title"], card["value"], card["color"], col, card["icon"])
                col += 1
        
        kpi_frame.grid_columnconfigure(0, weight=1)
        kpi_frame.grid_columnconfigure(1, weight=1)
        kpi_frame.grid_columnconfigure(2, weight=1)
        kpi_frame.grid_columnconfigure(3, weight=1)

        # 3. Khung chi tiết (Thông tin người dùng & Bán chạy)
        detail_frame = tk.Frame(self.master, bg="#ECEFF1", padx=10, pady=10)
        detail_frame.pack(fill="both", expand=True, pady=10)
        
        # Khung Thông tin người dùng
        user_info_frame = tk.LabelFrame(detail_frame, text="Thông tin phiên làm việc", bg="#FFFFFF", padx=15, pady=15)
        user_info_frame.pack(side="left", fill="y", padx=(0, 20))
        
        user_role_text = MainApp.ROLE_MAP.get(self.user_role, 'Không rõ')
        
        tk.Label(user_info_frame, text=f"Tài khoản: ", font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#2196F3").grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(user_info_frame, text=self.user_info['HoTen'], font=("Arial", 11), bg="#FFFFFF").grid(row=0, column=1, sticky="w", padx=10, pady=2)
        
        tk.Label(user_info_frame, text=f"Tên ĐN: ", font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#2196F3").grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(user_info_frame, text=self.user_info['TenDangNhap'], font=("Arial", 11), bg="#FFFFFF").grid(row=1, column=1, sticky="w", padx=10, pady=2)
        
        tk.Label(user_info_frame, text=f"Quyền hạn: ", font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#2196F3").grid(row=2, column=0, sticky="w", pady=2)
        tk.Label(user_info_frame, text=user_role_text, font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#E65100").grid(row=2, column=1, sticky="w", padx=10, pady=2)

        # Khung Bán chạy nhất
        top_selling_frame = tk.LabelFrame(detail_frame, text="Sản phẩm Bán chạy nhất (theo SL)", bg="#FFFFFF", padx=15, pady=15)
        top_selling_frame.pack(side="left", fill="both", expand=True)

        tk.Label(top_selling_frame, text=f"Tên Hàng: ", font=("Arial", 11, "bold"), bg="#FFFFFF", fg="#00796B").grid(row=0, column=0, sticky="w", pady=5)
        tk.Label(top_selling_frame, text=stats['TopProduct'], font=("Arial", 12, "bold"), bg="#FFFFFF", fg="#00796B").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        tk.Label(top_selling_frame, text="💡 Dữ liệu này được cập nhật từ DB.", font=("Arial", 10, "italic"), bg="#FFFFFF", fg="#757575").grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))


    def create_kpi_card(self, parent, title, value, color, col, icon):
        """Tạo một thẻ KPI đơn giản."""
        card = tk.Frame(parent, bg="#FFFFFF", padx=15, pady=15, bd=1, relief=tk.SOLID)
        card.grid(row=0, column=col, padx=10, sticky="nsew")

        # Icon
        tk.Label(card, text=icon, font=("Arial", 24), bg="#FFFFFF", fg=color).pack(pady=(0, 5))
        
        # Title
        tk.Label(card, text=title, font=("Arial", 10), bg="#FFFFFF", fg="#757575").pack(pady=(0, 2))

        # Value
        tk.Label(card, text=value, font=("Arial", 18, "bold"), bg="#FFFFFF", fg=color).pack()

# ------------------------------------------------
# CÁC HÀM XỬ LÝ TRONG MAIN APP
# ------------------------------------------------

def set_active_menu(button):
    """Đặt button được chọn làm active và reset các button khác"""
    # Reset tất cả các button về màu mặc định
    for btn in MainApp.menu_buttons:
        btn.config(bg="#263238")
    
    # Đặt button hiện tại thành active (màu nổi bật)
    button.config(bg="#00796B")
    MainApp.active_button = button

def open_module(title, button=None):
    """Xử lý hiển thị form module tương ứng trong Content Frame"""
    try:
        print(f"--- Dang mo module: {title}")
    except Exception:
        # Fallback tránh crash nếu console không hỗ trợ Unicode
        print("--- Dang mo module")
    
    if not MainApp.content_frame:
        print("Lỗi: Content Frame chưa được khởi tạo.")
        return
    
    # Highlight button được chọn
    if button:
        set_active_menu(button)
        
    # Xóa nội dung cũ trong Content Frame
    for widget in MainApp.content_frame.winfo_children():
        widget.destroy()

    # LOGIC TẢI FORM THEO TITLE
    if title == "Bảng điều khiển":
        FormClass = Dashboard
    elif title == "Quản lý Hàng hóa":
        FormClass = ProductManagementForm 
    elif title == "Quản lý Khách hàng":
        FormClass = CustomerManagementForm 
    elif title == "Quản lý Nhân viên":
        FormClass = EmployeeManagementForm 
    elif title == "Quản lý Tài khoản":
        FormClass = AccountManagementForm 
    elif title == "Báo cáo Doanh thu":
        FormClass = DetailedInvoiceReportForm
    elif title == "Lập Hóa đơn Bán hàng":
        FormClass = SalesInvoiceForm
    else:
        FormClass = None
        
    # Xử lý tải Form
    if FormClass:
        try:
            # Truyền user_info nếu là Dashboard
            if title == "Bảng điều khiển" or title == "Lập Hóa đơn Bán hàng":
                FormClass(MainApp.content_frame, MainApp.user_info)
            else:
                FormClass(MainApp.content_frame)
        except Exception as e:
            error_msg = f"LỖI KHỞI TẠO FORM {title.upper()}: {e}"
            tk.Label(MainApp.content_frame, text=error_msg,
                     font=("Arial", 16, "bold"), fg="#D32F2F", bg="#ECEFF1", wraplength=700).pack(expand=True, pady=50)
            print(f"❌ Lỗi khởi tạo {title}: {e}")
    else:
        # Placeholder cho các module chưa code
        tk.Label(MainApp.content_frame, text=f"MODULE: {title} (Đang phát triển)",
                 font=("Arial", 20, "bold"), fg="#E64A19", bg="#ECEFF1").pack(expand=True, pady=50)


# ------------------------------------------------
# LỚP ỨNG DỤNG CHÍNH (Giữ nguyên)
# ------------------------------------------------

class MainApp:
    
    ROLE_MAP = { 0: 'ADMIN', 1: 'QUẢN LÝ', 2: 'NHÂN VIÊN' }
    
    MENU_ITEMS = [
        {"text": "📊 Bảng điều khiển", "command": lambda: open_module("Bảng điều khiển"), "roles": [0, 1, 2]},
        {"text": "🛒 Quản lý Hàng hóa", "command": lambda: open_module("Quản lý Hàng hóa"), "roles": [0, 1]},
        {"text": "👤 Quản lý Khách hàng", "command": lambda: open_module("Quản lý Khách hàng"), "roles": [0, 1, 2]},
        {"text": "👨‍💼 Quản lý Nhân viên", "command": lambda: open_module("Quản lý Nhân viên"), "roles": [0]},
        {"text": "💰 Lập Hóa đơn Bán hàng", "command": lambda: open_module("Lập Hóa đơn Bán hàng"), "roles": [0, 1, 2]},
        {"text": "📜 Báo cáo Doanh thu", "command": lambda: open_module("Báo cáo Doanh thu"), "roles": [0, 1]},
        {"text": "⚙️ Quản lý Tài khoản", "command": lambda: open_module("Quản lý Tài khoản"), "roles": [0]},
    ]
    
    user_info = None
    content_frame = None
    menu_buttons = []  # Danh sách các button menu để quản lý highlight
    active_button = None  # Button đang được chọn

    def __init__(self, root, user_info, start_login_callback):
        self.root = root
        MainApp.user_info = user_info
        self.start_login = start_login_callback
        self.user_role = user_info['PhanQuyen']
        self.setup_ui()

    def setup_ui(self):
        self.root.title(f"🏪 PHẦN MỀM QUẢN LÝ BÁN HÀNG - Quyền: {MainApp.ROLE_MAP.get(self.user_role, 'Không rõ')}")
        self.root.state('zoomed')  
        self.root.configure(bg="#F4F4F4")

        # 1. HEADER FRAME
        header_frame = tk.Frame(self.root, bg="#00796B", height=60)
        header_frame.pack(fill="x")
        
        # Logo/Tiêu đề
        tk.Label(header_frame, text="🏪 QUẢN LÝ BÁN HÀNG", 
                 font=("Arial", 18, "bold"), fg="white", bg="#00796B").pack(side="left", padx=20)
        
        # Thông tin người dùng
        user_text = f"Xin chào {self.user_info['HoTen']} | Quyền: {MainApp.ROLE_MAP.get(self.user_role, 'Không rõ')}"
        tk.Label(header_frame, text=user_text, 
                 font=("Arial", 12), fg="#E0F2F1", bg="#00796B").pack(side="right", padx=10)

        # Nút Đăng xuất
        tk.Button(header_frame, text="Đăng xuất", 
                  font=("Arial", 10, "bold"), bg="#D32F2F", fg="white", relief=tk.FLAT,
                  command=self.logout).pack(side="right", padx=10, pady=10)

        # 2. MAIN CONTAINER
        container = tk.Frame(self.root, bg="#F4F4F4")
        container.pack(expand=True, fill="both")
        
        # 3. SIDEBAR FRAME
        sidebar_frame = tk.Frame(container, bg="#263238", width=250)
        sidebar_frame.pack(side="left", fill="y")
        
        # Xóa danh sách button cũ (nếu có)
        MainApp.menu_buttons = []
        
        for item in MainApp.MENU_ITEMS:
            if self.user_role in item["roles"]:
                # Tạo button với command mới có truyền button
                btn = tk.Button(sidebar_frame, text=item["text"], 
                                font=("Arial", 11), fg="white", bg="#263238",
                                activebackground="#37474F", activeforeground="white",
                                anchor="w", bd=0, padx=20, pady=10, relief=tk.FLAT)
                btn.pack(fill="x", pady=1)
                
                # Lưu button vào danh sách
                MainApp.menu_buttons.append(btn)
                
                # Cấu hình command với lambda để truyền cả title và button
                title = item["text"].split(" ", 1)[1]  # Lấy text không có icon
                btn.config(command=lambda t=title, b=btn: open_module(t, b))
                
                # Giữ nguyên hover effect
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#37474F") if b != MainApp.active_button else None)
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#263238") if b != MainApp.active_button else b.config(bg="#00796B"))

        # 4. CONTENT FRAME
        MainApp.content_frame = tk.Frame(container, bg="#ECEFF1")
        MainApp.content_frame.pack(side="right", expand=True, fill="both")
        
        # Hiển thị mặc định (Dashboard) và set active cho button đầu tiên
        if MainApp.menu_buttons:
            open_module("Bảng điều khiển", MainApp.menu_buttons[0])


    def logout(self):
        """Xử lý đăng xuất"""
        if messagebox.askyesno("Xác nhận", "Bạn có muốn đăng xuất không?"):
            self.root.destroy()
            self.start_login() 
            
# ------------------------------------------------
# LUỒNG CHẠY CHÍNH (Giữ nguyên)
# ------------------------------------------------

def start_login():
    """Mở form đăng nhập sau khi splash xong"""
    import login_form 
    login_root = tk.Tk()
    app = login_form.LoginForm(login_root, on_success_callback=start_main_form)
    login_root.mainloop()

def start_main_form(user_info):
    """Form chính sau khi đăng nhập thành công"""
    main = tk.Tk()
    app = MainApp(main, user_info, start_login)
    main.mainloop()

if __name__ == "__main__":
    # --- LUỒNG CHẠY CHÍNH (Splash -> Login -> Main) ---
    root = tk.Tk()
    # Khởi động bằng SplashScreen, rồi gọi start_login khi xong
    app = SplashScreen(root, on_done=start_login)
    root.mainloop()