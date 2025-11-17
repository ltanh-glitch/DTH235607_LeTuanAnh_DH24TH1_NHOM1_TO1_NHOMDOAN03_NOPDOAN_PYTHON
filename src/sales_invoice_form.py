# -*- coding: utf-8 -*-
# sales_invoice_form.py - Module Lập Hóa Đơn Bán Hàng (Sales Invoice Form)
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import threading
from datetime import datetime
from auth import get_connection

class SalesInvoiceForm:
    def __init__(self, master, user_info):
        self.master = master
        if isinstance(self.master, tk.Tk):
            self.master.title("Lập Hóa Đơn Bán Hàng")

        self.user_info = user_info # Thông tin người lập hóa đơn
        self.master.config(bg="#ECEFF1")
        
        self.current_state = 'VIEW'
        self.current_mahd = None
        self.cart_items = {} # {MaHang: {data}} - Giỏ hàng
        self.product_map = {} # {MaHang: TenHang, DonGiaNhap, SoLuongTon}
        self.customer_map = {} # {TenKhach: MaKhach}
        
        main_frame = tk.Frame(master, bg="#ECEFF1", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="💰 LẬP HÓA ĐƠN BÁN HÀNG",
                 font=("Arial", 20, "bold"), fg="#D84315", bg="#ECEFF1").pack(pady=(0, 15)) # Màu đỏ cam

        # --- CONTAINER CHÍNH (Chia thành 2 khung) ---
        input_container = tk.Frame(main_frame, bg="#ECEFF1")
        input_container.pack(fill="x", pady=5)

        # 1. KHUNG THÔNG TIN CHUNG & KHÁCH HÀNG (LEFT)
        general_frame = tk.LabelFrame(input_container, text="Thông tin Chung & Khách hàng", bg="#FFFFFF", padx=10, pady=10)
        general_frame.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        
        self.entries = {}
        labels = [
            ("Mã HĐ:", "ma_hdban"),
            ("Ngày bán:", "ngay_ban"),
            ("Nhân viên:", "ten_nhanvien"),
            ("Khách hàng:", "ma_khach"), # Combobox Tên Khách
        ]
        
        for i, (label, field) in enumerate(labels):
            tk.Label(general_frame, text=label, bg="#FFFFFF").grid(row=i, column=0, sticky="w", padx=5, pady=3)
            
            if field == "ma_khach":
                combo = ttk.Combobox(general_frame, state="readonly")
                combo.grid(row=i, column=1, sticky="ew", padx=5, pady=3)
                self.entries[field] = combo
            else:
                entry = tk.Entry(general_frame)
                entry.grid(row=i, column=1, sticky="ew", padx=5, pady=3)
                self.entries[field] = entry

        # Thiết lập giá trị mặc định/readonly
        self.entries["ma_hdban"].config(state="readonly")
        self.entries["ngay_ban"].insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entries["ngay_ban"].config(state="readonly")
        self.entries["ten_nhanvien"].insert(0, self.user_info.get('HoTen', 'N/A'))
        self.entries["ten_nhanvien"].config(state="readonly")
        general_frame.grid_columnconfigure(1, weight=1)

        # 2. KHUNG CHI TIẾT SẢN PHẨM (RIGHT)
        detail_frame = tk.LabelFrame(input_container, text="Thêm Sản phẩm", bg="#FFFFFF", padx=10, pady=10)
        detail_frame.pack(side=tk.LEFT, fill="x", expand=True, padx=(5, 0))
        
        detail_labels = [("Mặt hàng:", "ma_hang"), ("Số lượng:", "so_luong"), ("Đơn giá:", "don_gia")]
        self.detail_entries = {}

        for i, (label, field) in enumerate(detail_labels):
            tk.Label(detail_frame, text=label, bg="#FFFFFF").grid(row=0, column=i*2, sticky="w", padx=5, pady=3)
            
            if field == "ma_hang":
                # Combobox cho sản phẩm
                combo = ttk.Combobox(detail_frame, state="readonly", width=30)
                combo.grid(row=0, column=i*2 + 1, sticky="ew", padx=(0, 10), pady=3)
                self.detail_entries[field] = combo
                combo.bind("<<ComboboxSelected>>", self.update_don_gia)
            else:
                entry = tk.Entry(detail_frame, width=15)
                entry.grid(row=0, column=i*2 + 1, sticky="ew", padx=(0, 10), pady=3)
                self.detail_entries[field] = entry
                if field == "don_gia":
                     entry.config(state="readonly")

        # Nút Thêm vào giỏ
        self.btn_add_to_cart = tk.Button(detail_frame, text="➕ Thêm vào HĐ", command=self.add_to_cart, bg="#03A9F4", fg="white", state=tk.DISABLED)
        self.btn_add_to_cart.grid(row=0, column=6, padx=(10, 5), pady=3, sticky="e")
        detail_frame.grid_columnconfigure(5, weight=1)

        # --- TREEVIEW GIỎ HÀNG (Cart View) ---
        cart_columns = ("MaHang", "TenHang", "SoLuong", "DonGia", "GiamGia", "ThanhTien")
        self.cart_tree = ttk.Treeview(main_frame, columns=cart_columns, show="headings", height=8)
        cart_widths = [80, 250, 100, 120, 80, 150]
        cart_names = ["Mã Hàng", "Tên Mặt Hàng", "SL", "Đơn Giá", "Giảm (%)", "Thành Tiền"]

        for col, text, width in zip(cart_columns, cart_names, cart_widths):
            self.cart_tree.heading(col, text=text, anchor="center")
            anchor_type = "e" if col in ["SoLuong", "DonGia", "ThanhTien"] else "w"
            self.cart_tree.column(col, width=width, anchor=anchor_type)
        
        self.cart_tree.pack(fill=tk.X, pady=10)
        # Style xen kẽ cho giỏ hàng
        self.cart_tree.tag_configure('oddrow', background="#F5F5F5")
        self.cart_tree.tag_configure('evenrow', background="#FFFFFF")
        self.cart_tree.bind("<Delete>", self.remove_from_cart) # Bắt sự kiện nhấn Delete
        # Enter để thêm nhanh vào giỏ khi đang ở trạng thái NEW
        self.detail_entries["so_luong"].bind("<Return>", lambda e: self.add_to_cart() if self.btn_add_to_cart['state'] == tk.NORMAL else None)

        # --- KHUNG TỔNG KẾT & NÚT CHỨC NĂNG ---
        summary_controls_frame = tk.Frame(main_frame, bg="#ECEFF1")
        summary_controls_frame.pack(fill="x", pady=5)

        # Left: Tổng kết
        summary_frame = tk.LabelFrame(summary_controls_frame, text="Tổng kết Thanh toán", bg="#FFFFFF", padx=10, pady=5)
        summary_frame.pack(side=tk.LEFT, padx=(0, 10), fill="y")

        self.lbl_tong_tien = tk.Label(summary_frame, text="TỔNG CỘNG: 0 VND", font=("Arial", 14, "bold"), bg="#FFFFFF", fg="#D32F2F")
        self.lbl_tong_tien.pack(side="top", pady=5, anchor="w")
        
        # Right: Nút điều khiển
        control_frame = tk.Frame(summary_controls_frame, bg="#ECEFF1")
        control_frame.pack(side=tk.RIGHT, fill="y")
        
        self.btn_new = tk.Button(control_frame, text="➕ Hóa đơn Mới", command=self.set_new_invoice_state, bg="#AED581", width=15)
        self.btn_save = tk.Button(control_frame, text="💾 LƯU & Thanh toán", command=self.save_invoice, bg="#64B5F6", width=20, state=tk.DISABLED)
        self.btn_cancel = tk.Button(control_frame, text="🗑️ Hủy Hóa đơn", command=self.cancel_action, bg="#E57373", width=15, state=tk.DISABLED)
        
        self.btn_new.pack(side=tk.LEFT, padx=5)
        self.btn_save.pack(side=tk.LEFT, padx=5)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)


        # --- Thanh trạng thái ---
        self.status_bar = tk.Label(main_frame, text="Sẵn sàng.", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        # Khởi tạo dữ liệu tham chiếu
        self.master.after(100, self.load_reference_data)
        self.set_state("VIEW")

    # =======================================================
    # KẾT NỐI & LOAD (Dùng Threading)
    # =======================================================
    def get_conn(self):
        try:
            return get_connection()
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối SQL thất bại:\n{e}"))
            return None

    def load_reference_data(self):
        """Tải danh sách Khách hàng và Mặt hàng."""
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            
            # 1. Load Khách hàng
            cursor.execute("SELECT MaKhach, TenKhach FROM tblKhach ORDER BY TenKhach")
            cust_data = cursor.fetchall()
            self.customer_map = {r.TenKhach: r.MaKhach for r in cust_data}
            cust_names = ["-- Khách lẻ (Không lưu) --"] + list(self.customer_map.keys())
            self.entries["ma_khach"]["values"] = cust_names
            self.entries["ma_khach"].set(cust_names[0])
            
            # 2. Load Mặt hàng (bao gồm SoLuong tồn kho)
            cursor.execute("SELECT MaHang, TenHang, DonGiaNhap, SoLuong FROM tblHang ORDER BY TenHang")
            prod_data = cursor.fetchall()
            # Lưu cả DonGiaNhap và SoLuongTon
            self.product_map = {r.TenHang: {'MaHang': r.MaHang, 'DonGiaNhap': r.DonGiaNhap, 'SoLuongTon': r.SoLuong} for r in prod_data}
            prod_names = ["-- Chọn mặt hàng --"] + list(self.product_map.keys())
            self.detail_entries["ma_hang"]["values"] = prod_names
            self.detail_entries["ma_hang"].set(prod_names[0])
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải dữ liệu tham chiếu: {e}")
        finally:
            if conn: conn.close()

    def get_next_mahd(self):
        """Lấy Mã HĐ tiếp theo (dùng MAX+1)."""
        conn = self.get_conn()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(MaHDBan) FROM tblHDBan")
            max_id = cursor.fetchone()[0]
            next_id = 1 if max_id is None else max_id + 1
            return next_id
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lấy mã HĐ tiếp theo:\n{e}")
            return None
        finally:
            conn.close()

    # =======================================================
    # LOGIC GIỎ HÀNG (CART LOGIC)
    # =======================================================
    def update_don_gia(self, event=None):
        """Cập nhật Đơn giá và hiển thị số lượng tồn kho khi chọn Mặt hàng."""
        selected_name = self.detail_entries["ma_hang"].get()
        if selected_name in self.product_map:
            price = self.product_map[selected_name]['DonGiaNhap'] # Dùng giá nhập làm giá bán đề xuất
            so_luong_ton = self.product_map[selected_name]['SoLuongTon']
            
            self.detail_entries["don_gia"].config(state="normal")
            self.detail_entries["don_gia"].delete(0, tk.END)
            self.detail_entries["don_gia"].insert(0, f"{price:,.0f}")
            self.detail_entries["don_gia"].config(state="readonly")
            
            # Hiển thị số lượng tồn kho trên status bar
            self.status_bar.config(text=f"📦 Tồn kho: {so_luong_ton} {self.get_don_vi(selected_name)}")
        else:
            self.detail_entries["don_gia"].config(state="normal")
            self.detail_entries["don_gia"].delete(0, tk.END)
            self.detail_entries["don_gia"].config(state="readonly")
            self.status_bar.config(text="Sẵn sàng.")
    
    def get_don_vi(self, ten_hang):
        """Lấy đơn vị tính của sản phẩm (nếu cần)."""
        # Đơn giản trả về 'SP' (Sản phẩm), có thể mở rộng để lấy từ DB
        return "SP"


    def add_to_cart(self):
        """Thêm mặt hàng đang chọn vào giỏ hàng."""
        # 1. Lấy và Validate dữ liệu
        try:
            selected_name = self.detail_entries["ma_hang"].get()
            so_luong = int(self.detail_entries["so_luong"].get().replace(",", "").replace(".", ""))
            don_gia_raw = self.detail_entries["don_gia"].get().replace(",", "").replace(".", "")
            don_gia = float(don_gia_raw)
            
            if selected_name not in self.product_map or selected_name == "-- Chọn mặt hàng --":
                raise ValueError("Vui lòng chọn mặt hàng hợp lệ.")
            if so_luong <= 0:
                 raise ValueError("Số lượng phải lớn hơn 0.")
            
            ma_hang = self.product_map[selected_name]['MaHang']
            so_luong_ton = self.product_map[selected_name]['SoLuongTon']
            
            # **KIỂM TRA SỐ LƯỢNG TỒN KHO**
            # Tính tổng số lượng đã có trong giỏ (nếu có)
            so_luong_trong_gio = self.cart_items[ma_hang]['SoLuong'] if ma_hang in self.cart_items else 0
            tong_so_luong_mua = so_luong_trong_gio + so_luong
            
            if tong_so_luong_mua > so_luong_ton:
                # Số lượng không đủ
                if so_luong_ton == 0:
                    messagebox.showerror("⚠️ Hết hàng!", 
                                       f"Sản phẩm '{selected_name}' đã HẾT HÀNG trong kho!\n\n"
                                       f"📦 Tồn kho hiện tại: 0\n"
                                       f"Vui lòng chọn sản phẩm khác hoặc nhập hàng.")
                else:
                    con_lai = so_luong_ton - so_luong_trong_gio
                    messagebox.showwarning("⚠️ Không đủ hàng!", 
                                         f"Số lượng tồn kho KHÔNG ĐỦ cho sản phẩm '{selected_name}'!\n\n"
                                         f"📦 Tồn kho hiện tại: {so_luong_ton}\n"
                                         f"🛒 Đã có trong giỏ: {so_luong_trong_gio}\n"
                                         f"✅ Còn có thể thêm tối đa: {con_lai}\n"
                                         f"❌ Bạn đang muốn thêm: {so_luong}\n\n"
                                         f"Vui lòng giảm số lượng hoặc chọn sản phẩm khác!")
                self.status_bar.config(text=f"❌ Không đủ hàng! Tồn kho: {so_luong_ton}, Còn lại: {so_luong_ton - so_luong_trong_gio}")
                return  # Không thêm vào giỏ
            
            thanh_tien = so_luong * don_gia # Giả định giảm giá = 0

            # 2. Cập nhật giỏ hàng
            if ma_hang in self.cart_items:
                # Nếu hàng đã có, cập nhật số lượng
                old_sl = self.cart_items[ma_hang]['SoLuong']
                self.cart_items[ma_hang]['SoLuong'] = old_sl + so_luong
                self.cart_items[ma_hang]['ThanhTien'] = (old_sl + so_luong) * don_gia
            else:
                # Hàng mới
                self.cart_items[ma_hang] = {
                    'MaHang': ma_hang,
                    'TenHang': selected_name,
                    'SoLuong': so_luong,
                    'DonGia': don_gia,
                    'GiamGia': 0.0, # Chưa có ô nhập giảm giá
                    'ThanhTien': thanh_tien
                }
            
            self.refresh_cart_view()
            self.clear_detail_entries()
            self.update_summary()
            self.status_bar.config(text=f"✅ Đã thêm {so_luong} '{selected_name}' vào hóa đơn.")

        except ValueError as e:
            messagebox.showwarning("Lỗi nhập liệu", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi thêm vào giỏ: {e}")

    def remove_from_cart(self, event=None):
        """Xóa mặt hàng khỏi giỏ hàng khi nhấn Delete/chọn nút."""
        selected_item = self.cart_tree.selection()
        if not selected_item: return
        
        # Lấy MaHang từ Treeview
        ma_hang = self.cart_tree.item(selected_item)['values'][0]
        
        if ma_hang in self.cart_items:
            del self.cart_items[ma_hang]
            self.refresh_cart_view()
            self.update_summary()
            self.status_bar.config(text=f"✅ Đã xóa mặt hàng Mã {ma_hang} khỏi giỏ hàng.")

    def refresh_cart_view(self):
        """Tải lại Treeview Giỏ hàng từ self.cart_items."""
        self.cart_tree.delete(*self.cart_tree.get_children())
        total_value = 0
        
        for i, item in enumerate(self.cart_items.values()):
            # Định dạng lại dữ liệu hiển thị
            display_values = (
                item['MaHang'],
                item['TenHang'],
                item['SoLuong'],
                f"{item['DonGia']:,.0f}",
                f"{item['GiamGia']:.0f}",
                f"{item['ThanhTien']:,.0f}"
            )
            total_value += item['ThanhTien']
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.cart_tree.insert('', tk.END, values=display_values, tags=(tag,))
        
        return total_value

    def update_summary(self):
        """Tính toán và cập nhật tổng tiền."""
        total_revenue = sum(item['ThanhTien'] for item in self.cart_items.values())
        self.lbl_tong_tien.config(text=f"TỔNG CỘNG: {total_revenue:,.0f} VND")
        # Bật/tắt nút LƯU dựa trên trạng thái và có hàng trong giỏ
        self.btn_save.config(state=(tk.NORMAL if self.current_state == 'NEW' and len(self.cart_items) > 0 else tk.DISABLED))

    # =======================================================
    # CRUD (LƯU HÓA ĐƠN)
    # =======================================================
    def save_invoice(self):
        """Xử lý lưu Hóa đơn (tblHDBan) và Chi tiết (tblChiTietHDBan)."""
        if not self.cart_items:
            messagebox.showwarning("Lỗi", "Vui lòng thêm ít nhất một mặt hàng vào hóa đơn.")
            return

        ma_khach_name = self.entries["ma_khach"].get()
        ma_khach = self.customer_map.get(ma_khach_name)
        tong_tien = sum(item['ThanhTien'] for item in self.cart_items.values())
        ma_nv = self.user_info.get('MaNhanVien', None) # Lấy MaNV từ user_info (cần bổ sung MaNV khi đăng nhập)
        
        if ma_nv is None:
             messagebox.showerror("Lỗi", "Không tìm thấy Mã Nhân viên. Vui lòng đăng nhập lại.")
             return
             
        if not messagebox.askyesno("Xác nhận", f"Xác nhận thanh toán tổng cộng {tong_tien:,.0f} VND?"):
            return

        self.status_bar.config(text="🔄 Đang xử lý thanh toán...")
        threading.Thread(target=self._execute_save_invoice, 
                         args=(ma_nv, ma_khach, tong_tien, self.cart_items), 
                         daemon=True).start()

    def _execute_save_invoice(self, ma_nv, ma_khach, tong_tien, cart_items):
        conn = self.get_conn()
        if not conn: return

        try:
            cursor = conn.cursor()
            
            # 1. INSERT tblHDBan
            cursor.execute("""
                INSERT INTO tblHDBan (MaNhanVien, MaKhach, NgayBan, TongTien)
                OUTPUT INSERTED.MaHDBan
                VALUES (?, ?, GETDATE(), ?)
            """, (ma_nv, ma_khach, tong_tien))
            
            ma_hdban = cursor.fetchone()[0]
            
            # 2. INSERT tblChiTietHDBan và UPDATE SoLuong tblHang
            for item in cart_items.values():
                # Chèn chi tiết
                cursor.execute("""
                    INSERT INTO tblChiTietHDBan (MaHDBan, MaHang, SoLuong, DonGia, GiamGia)
                    VALUES (?, ?, ?, ?, ?)
                """, (ma_hdban, item['MaHang'], item['SoLuong'], item['DonGia'], item['GiamGia']))
                
                # Cập nhật số lượng tồn kho (trừ đi số lượng bán)
                cursor.execute("""
                    UPDATE tblHang SET SoLuong = SoLuong - ? WHERE MaHang = ?
                """, (item['SoLuong'], item['MaHang']))

            conn.commit()
            
            self.master.after(0, lambda: self._on_invoice_saved(ma_hdban))

        except Exception as e:
            conn.rollback()
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Thanh toán thất bại:\n{e}"))
        finally:
            if conn: conn.close()
            self.master.after(0, self.load_reference_data) # Tải lại ref data để cập nhật số lượng tồn

    # =======================================================
    # QUẢN LÝ TRẠNG THÁI (STATE MANAGEMENT)
    # =======================================================
    def set_state(self, state):
        self.current_state = state
        is_view = state == 'VIEW'
        is_new = state == 'NEW'

        # Thông tin chung
        self.entries["ma_hdban"].config(state="readonly")
        self.entries["ngay_ban"].config(state="readonly")
        self.entries["ten_nhanvien"].config(state="readonly")
        self.entries["ma_khach"].config(state="readonly" if is_new else tk.DISABLED)
        
        # Chi tiết mặt hàng
        self.detail_entries["ma_hang"].config(state="readonly" if is_new else tk.DISABLED)
        self.detail_entries["so_luong"].config(state=tk.NORMAL if is_new else tk.DISABLED)
        self.detail_entries["don_gia"].config(state="readonly" if is_new else tk.DISABLED)
        self.btn_add_to_cart.config(state=tk.NORMAL if is_new else tk.DISABLED)
        
        # Nút điều khiển
        self.btn_new.config(state=tk.NORMAL if is_view else tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL if is_new and self.cart_items else tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL if is_new else tk.DISABLED)

    def set_new_invoice_state(self):
        """Chuyển sang trạng thái NEW: lấy Mã HĐ mới và xóa giỏ hàng."""
        self.current_mahd = self.get_next_mahd()
        if self.current_mahd is None: return

        # 1. Reset
        self.entries["ma_hdban"].config(state="normal")
        self.entries["ma_hdban"].delete(0, tk.END)
        self.entries["ma_hdban"].insert(0, self.current_mahd)
        self.entries["ma_hdban"].config(state="readonly")
        
        self.entries["ma_khach"].set(self.entries["ma_khach"]["values"][0])
        self.clear_detail_entries()
        
        self.cart_items = {}
        self.refresh_cart_view()
        self.update_summary()

        # 2. Set State
        self.set_state("NEW")
        self.status_bar.config(text=f"📝 Đang lập Hóa đơn mới Mã {self.current_mahd}. Vui lòng chọn khách hàng và mặt hàng.")

    def cancel_action(self):
        """Hủy hóa đơn đang lập."""
        if messagebox.askyesno("Xác nhận Hủy", "Bạn có muốn hủy bỏ Hóa đơn đang lập không?"):
            self.cart_items = {}
            self.refresh_cart_view()
            self.update_summary()
            self.set_state("VIEW")
            self.status_bar.config(text="🗑️ Đã hủy hóa đơn. Sẵn sàng cho Hóa đơn mới.")

    def _on_invoice_saved(self, ma_hdban):
        """Hàm chạy trên luồng chính sau khi lưu hóa đơn thành công."""
        messagebox.showinfo("Thành công", f"Thanh toán thành công! Mã HĐ: {ma_hdban}")
        self.set_state("VIEW")
        self.status_bar.config(text=f"✅ Hóa đơn Mã {ma_hdban} đã được lưu thành công!")
        self.current_mahd = ma_hdban

    def clear_detail_entries(self):
        """Xóa các trường nhập chi tiết sản phẩm."""
        self.detail_entries["ma_hang"].set(self.detail_entries["ma_hang"]["values"][0])
        self.detail_entries["so_luong"].delete(0, tk.END)
        self.detail_entries["so_luong"].insert(0, 1) # Mặc định là 1
        
        self.detail_entries["don_gia"].config(state="normal")
        self.detail_entries["don_gia"].delete(0, tk.END)
        self.detail_entries["don_gia"].config(state="readonly")


if __name__ == "__main__":
    # Test độc lập (Cần mô phỏng user_info)
    mock_user_info = {
         "TenDangNhap": "dev_test",
         "PhanQuyen": 0,
         "HoTen": "Lê Tuấn Anh (Admin)",
         "MaNhanVien": 1 # Quan trọng: Phải có MaNhanVien để lập HĐ
    }
    root = tk.Tk()
    root.state('zoomed')
    app = SalesInvoiceForm(root, mock_user_info)
    root.mainloop()