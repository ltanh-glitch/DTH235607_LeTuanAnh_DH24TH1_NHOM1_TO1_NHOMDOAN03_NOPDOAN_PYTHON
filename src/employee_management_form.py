# -*- coding: utf-8 -*-
# employee_management_form.py - Module Quản lý Nhân viên (Dùng Date Picker)
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import threading
from datetime import datetime
from tkcalendar import DateEntry
from auth import get_connection # Giả định module auth.py tồn tại và cung cấp get_connection()

class EmployeeManagementForm:
    def __init__(self, master):
        self.master = master
        if isinstance(self.master, tk.Tk):
            self.master.title("Quản lý Nhân viên")

        self.master.config(bg="#ECEFF1")
        self.current_state = 'VIEW'
        self.selected_item = None
        
        main_frame = tk.Frame(master, bg="#ECEFF1", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="👨‍💼 QUẢN LÝ NHÂN VIÊN",
                 font=("Arial", 20, "bold"), fg="#00796B", bg="#ECEFF1").pack(pady=(0, 15))

        # --- Khung tìm kiếm (Giống ProductManagementForm) ---
        search_frame = tk.Frame(main_frame, bg="#E0E0E0", padx=10, pady=5)
        search_frame.pack(fill="x", pady=(0, 10))
        tk.Label(search_frame, text="Tìm kiếm (Tên/SĐT):", bg="#E0E0E0").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(5, 10))
        ttk.Button(search_frame, text="🔍 Tìm", command=self.search_employees).pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔄 Đặt lại", command=self.reset_search).pack(side="left", padx=5)

        # --- Form nhập liệu (Giống ProductManagementForm) ---
        form_frame = tk.LabelFrame(main_frame, text="Thông tin nhân viên", bg="#ECEFF1", padx=10, pady=10)
        form_frame.pack(fill=tk.X, pady=5)
        self.entries = {}
        
        # Danh sách các trường
        labels = [
            ("Mã NV:", "ma_nhanvien"),
            ("Tên NV:", "ten_nhanvien"),
            ("Giới tính:", "gioi_tinh"),
            ("Ngày sinh:", "ngay_sinh"),
            ("Điện thoại:", "dien_thoai"),
            ("Địa chỉ:", "dia_chi"),
        ]
        
        for i, (label, field) in enumerate(labels):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(form_frame, text=label, bg="#ECEFF1").grid(row=row, column=col, sticky="w", padx=(5, 0), pady=3)
            
            if field == "gioi_tinh":
                combo = ttk.Combobox(form_frame, state="readonly", values=["Nam", "Nữ", "Khác"])
                combo.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=3)
                self.entries[field] = combo
                self.entries[field].set("Nam")
            elif field == "ngay_sinh":
                 date_entry = DateEntry(
                    form_frame, 
                    date_pattern='yyyy-mm-dd', 
                    locale='vi_VN', 
                    font=("Arial", 10),
                    selectbackground="#00796B", 
                    selectforeground="white",
                    headersbackground="#00796B",
                    headersforeground="white"
                 )
                 date_entry.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=3)
                 self.entries[field] = date_entry
                 self.entries[field].set_date(datetime.now().date())
            else:
                entry = tk.Entry(form_frame)
                entry.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=3)
                self.entries[field] = entry

        self.entries["ma_nhanvien"].config(state="readonly")
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1) # Cột cho trường bên phải

        # --- Nút chức năng (Giống ProductManagementForm) ---
        button_frame = tk.Frame(main_frame, bg="#ECEFF1")
        button_frame.pack(fill=tk.X, pady=5)
        self.btn_add = tk.Button(button_frame, text="➕ Thêm", command=self.set_add_state, bg="#AED581", width=10)
        self.btn_save = tk.Button(button_frame, text="💾 Lưu", command=self.save_data, bg="#64B5F6", width=10, state=tk.DISABLED)
        self.btn_edit = tk.Button(button_frame, text="📝 Sửa", command=self.set_edit_state, bg="#FFB74D", width=10)
        self.btn_delete = tk.Button(button_frame, text="❌ Xóa", command=self.delete_employee, bg="#E57373", width=10)
        self.btn_cancel = tk.Button(button_frame, text="🗑️ Hủy", command=self.cancel_action, bg="#90A4AE", width=10, state=tk.DISABLED)
        for b in [self.btn_add, self.btn_save, self.btn_edit, self.btn_delete, self.btn_cancel]:
            b.pack(side=tk.LEFT, padx=5)

        # --- TreeView ---
        columns = ("MaNV", "TenNV", "GioiTinh", "NgaySinh", "DienThoai", "DiaChi")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        widths = [80, 200, 70, 120, 130, 250]
        for col, text, width in zip(columns, ["Mã NV", "Tên Nhân Viên", "GT", "Ngày Sinh", "Điện thoại", "Địa chỉ"], widths):
            self.tree.heading(col, text=text, anchor="center")
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-Button-1>", self.on_tree_double_click)
        
        # Thêm Scrollbar
        vscrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vscrollbar.set)
        vscrollbar.pack(side="right", fill="y")

        # --- Thanh trạng thái ---
        self.status_bar = tk.Label(main_frame, text="Sẵn sàng.", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.set_form_state("VIEW")
        self.master.after(300, self.load_data)

    # =======================================================
    # KẾT NỐI & LOAD (Dựa trên ProductManagementForm, dùng threading)
    # =======================================================
    def get_conn(self):
        try:
            return get_connection()
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối SQL thất bại:\n{e}"))
            return None

    def load_data(self, search_term=""):
        def _task():
            conn = self.get_conn()
            if not conn:
                self.master.after(0, lambda: self.status_bar.config(text="❌ Lỗi kết nối"))
                return
            try:
                cursor = conn.cursor()
                query = "SELECT MaNhanVien, TenNhanVien, GioiTinh, NgaySinh, DienThoai, DiaChi FROM tblNhanVien"
                params = []
                if search_term:
                    query += " WHERE TenNhanVien COLLATE Vietnamese_CI_AI LIKE ? OR DienThoai LIKE ? OR DiaChi COLLATE Vietnamese_CI_AI LIKE ? OR GioiTinh COLLATE Vietnamese_CI_AI LIKE ?"
                    params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
                query += " ORDER BY MaNhanVien ASC"
                cursor.execute(query, params)
                rows = cursor.fetchall()
                self.master.after(0, lambda: self._update_treeview(rows))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Tải dữ liệu thất bại:\n{e}"))
            finally:
                conn.close()

        self.status_bar.config(text="🔄 Đang tải dữ liệu...")
        threading.Thread(target=_task, daemon=True).start()

    def _update_treeview(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            # Format NgaySinh
            ngay_sinh_str = row.NgaySinh.strftime("%Y-%m-%d") if isinstance(row.NgaySinh, datetime) else str(row.NgaySinh or '')

            formatted_row = (
                row.MaNhanVien, row.TenNhanVien, row.GioiTinh or '',
                ngay_sinh_str, row.DienThoai or '', row.DiaChi or ''
            )
            tag = 'evenrow' if i % 2 == 0 else 'oddrow' # Giữ lại màu xen kẽ
            self.tree.insert('', tk.END, values=formatted_row, tags=(tag,))

        self.status_bar.config(text=f"✅ Đã tải {len(rows)} bản ghi.")
        
    def search_employees(self):
        keyword = self.search_var.get().strip()
        if not keyword:
            self.load_data()
            self.status_bar.config(text="🔍 Đặt lại tìm kiếm.")
            return
        self.load_data(keyword)

    def reset_search(self):
        self.search_var.set("")
        self.load_data()
        self.status_bar.config(text="🔄 Đã tải lại toàn bộ dữ liệu.")

    # =======================================================
    # STATE (Điều chỉnh cho form NV)
    # =======================================================
    def set_form_state(self, state):
        self.current_state = state
        editable = state in ("ADD", "EDIT")
        
        for field, entry in self.entries.items():
            if field == "ma_nhanvien":
                # Mã nhân viên luôn readonly
                entry.config(state="readonly")
            elif field == "gioi_tinh":
                # Combobox: normal khi ADD/EDIT, disabled khi VIEW
                entry.config(state="normal" if editable else "disabled")
            elif field == "ngay_sinh":
                # DateEntry: normal khi ADD/EDIT, disabled khi VIEW
                entry.config(state=tk.NORMAL if editable else tk.DISABLED)
            else:
                # Các trường khác: normal khi ADD/EDIT, disabled khi VIEW
                entry.config(state=tk.NORMAL if editable else tk.DISABLED)
        
        has_selection = self.selected_item is not None
        self.btn_add.config(state=tk.NORMAL if state == "VIEW" else tk.DISABLED)
        self.btn_edit.config(state=tk.NORMAL if state == "VIEW" and has_selection else tk.DISABLED)
        self.btn_delete.config(state=tk.NORMAL if state == "VIEW" and has_selection else tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL if editable else tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL if editable else tk.DISABLED)

    def set_add_state(self):
        self.clear_entries()
        # Lấy mã NV tiếp theo
        next_id = self.get_next_manhanvien()
        if next_id is not None:
            self.entries["ma_nhanvien"].config(state="normal")
            self.entries["ma_nhanvien"].delete(0, tk.END)
            self.entries["ma_nhanvien"].insert(0, next_id)
            self.entries["ma_nhanvien"].config(state="readonly")
        self.set_form_state("ADD")
        self.entries["ten_nhanvien"].focus()

    def get_next_manhanvien(self):
        """Lấy mã NV tiếp theo, ưu tiên lấp khoảng trống (gap) nếu có."""
        conn = self.get_conn()
        if not conn: return None
        try:
            cursor = conn.cursor()
            
            # Tương tự logic get_next_mahang của file Product
            cursor.execute("""
                SELECT MIN(t1.MaNhanVien + 1) AS NextID
                FROM tblNhanVien t1
                WHERE NOT EXISTS (
                    SELECT 1 FROM tblNhanVien t2 
                    WHERE t2.MaNhanVien = t1.MaNhanVien + 1
                )
                AND t1.MaNhanVien + 1 <= (SELECT MAX(MaNhanVien) FROM tblNhanVien)
            """)
            result = cursor.fetchone()
            gap_id = result[0] if result and result[0] else None
            
            if gap_id:
                return gap_id
            else:
                cursor.execute("SELECT MAX(MaNhanVien) FROM tblNhanVien")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] else 0
                return max_id + 1
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lấy mã NV tiếp theo:\n{e}")
            return None
        finally:
            conn.close()

    def set_edit_state(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhân viên để sửa!")
            return
            
        # Dữ liệu đã được load lên form trong on_tree_select, chỉ cần chuyển trạng thái
        self.set_form_state("EDIT")
        self.entries["ten_nhanvien"].focus()

    def cancel_action(self):
        self.clear_entries()
        self.set_form_state("VIEW")
        self.load_data()

    def clear_entries(self):
        self.selected_item = None
        self.entries['ma_nhanvien'].config(state='normal')
        for key, entry in self.entries.items():
            entry.config(state="normal")
            if key in ['gioi_tinh']:
                entry.set("Nam")
            elif key == 'ngay_sinh':
                 entry.set_date(datetime.now().date())
            else:
                entry.delete(0, tk.END)
                
        self.entries['ma_nhanvien'].config(state='readonly')
        self.tree.selection_remove(self.tree.selection())

    # =======================================================
    # CRUD (DÙNG THREADING)
    # =======================================================
    def save_data(self):
        ma_nv, data = self.get_validated_data(self.current_state == 'ADD')
        if data is None: return
        
        if self.current_state == "ADD":
            self.status_bar.config(text="🔄 Đang thêm nhân viên...")
            # Truyền next_id đã tính toán vào thread
            next_id = int(self.entries["ma_nhanvien"].get())
            threading.Thread(target=self._execute_add_item, args=(next_id, data,), daemon=True).start()
        elif self.current_state == "EDIT":
            self.status_bar.config(text=f"🔄 Đang cập nhật Mã {ma_nv}...")
            threading.Thread(target=self._execute_update_item, args=(ma_nv, data), daemon=True).start()

    def _execute_add_item(self, next_id, data):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            
            # Bật IDENTITY_INSERT để chèn mã tùy chỉnh
            cursor.execute("SET IDENTITY_INSERT tblNhanVien ON")
            cursor.execute("""
                INSERT INTO tblNhanVien (MaNhanVien, TenNhanVien, GioiTinh, DiaChi, DienThoai, NgaySinh)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (next_id, data['TenNhanVien'], data['GioiTinh'], data['DiaChi'], data['DienThoai'], data['NgaySinh']))
            cursor.execute("SET IDENTITY_INSERT tblNhanVien OFF")
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã thêm nhân viên mới với Mã {next_id}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã thêm Mã {next_id}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Thêm thất bại:\n{e}"))
        finally:
            if conn: 
                try: cursor.execute("SET IDENTITY_INSERT tblNhanVien OFF")
                except: pass
                conn.close()

    def _execute_update_item(self, ma_nv, data):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tblNhanVien 
                SET TenNhanVien=?, GioiTinh=?, DiaChi=?, DienThoai=?, NgaySinh=?
                WHERE MaNhanVien=?
            """, (data['TenNhanVien'], data['GioiTinh'], data['DiaChi'], data['DienThoai'], data['NgaySinh'], ma_nv))
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã cập nhật Mã {ma_nv}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã cập nhật Mã {ma_nv}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def delete_employee(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn nhân viên để xóa!")
            return
        ma_nv = self.entries["ma_nhanvien"].get()
        if not messagebox.askyesno("Xác nhận", f"Xóa nhân viên Mã {ma_nv}?"):
            return
        self.status_bar.config(text=f"🔄 Đang xóa Mã {ma_nv}...")
        threading.Thread(target=self._execute_delete_item, args=(ma_nv,), daemon=True).start()

    def _execute_delete_item(self, ma_nv):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            # Xử lý khóa ngoại (Giống như logic cũ)
            cursor.execute("UPDATE tblTaiKhoan SET MaNhanVien = NULL WHERE MaNhanVien = ?", (ma_nv,))
            # Xóa nhân viên
            cursor.execute("DELETE FROM tblNhanVien WHERE MaNhanVien=?", (ma_nv,))
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã xóa Mã {ma_nv}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã xóa Mã {ma_nv}")
            ])
        except pyodbc.IntegrityError:
             self.master.after(0, lambda: messagebox.showerror("Lỗi DB", "Không thể xóa nhân viên này vì đã có giao dịch (Hóa đơn bán hàng) liên quan."))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Xóa thất bại:\n{e}"))
        finally:
            if conn: conn.close()
            
    # =======================================================
    # TIỆN ÍCH
    # =======================================================
    def get_validated_data(self, is_add):
        ma_nv = self.entries['ma_nhanvien'].get().strip()
        ten_nv = self.entries['ten_nhanvien'].get().strip()
        gioi_tinh = self.entries['gioi_tinh'].get().strip()
        dien_thoai = self.entries['dien_thoai'].get().strip()
        dia_chi = self.entries['dia_chi'].get().strip()
        
        # DateEntry trả về ngày theo format string đã định
        ngay_sinh = self.entries['ngay_sinh'].get() 

        if not ten_nv:
            messagebox.showwarning("Thiếu thông tin", "Tên nhân viên không được để trống.")
            return None, None
            
        return ma_nv, {
            "TenNhanVien": ten_nv,
            "GioiTinh": gioi_tinh,
            "DiaChi": dia_chi,
            "DienThoai": dien_thoai,
            "NgaySinh": ngay_sinh,
        }

    def on_tree_select(self, event):
        """Xử lý khi chọn một dòng trong Treeview - Lấy đầy đủ thông tin lên textbox."""
        # Chỉ xử lý khi đang ở chế độ VIEW
        if self.current_state != "VIEW":
            return
            
        selected = self.tree.selection()
        if not selected:
            self.selected_item = None
            self.set_form_state("VIEW")
            return
            
        self.selected_item = selected[0]
        values = self.tree.item(self.selected_item)['values']
        
        if len(values) >= 6:
            # Clear tất cả trước - PHẢI enable trước khi clear/insert
            for key, widget in self.entries.items():
                if key == "ma_nhanvien":
                    widget.config(state="normal")
                    widget.delete(0, tk.END)
                elif key == "gioi_tinh":
                    # Tạm chuyển về readonly để hiển thị giá trị
                    widget.config(state="readonly")
                    widget.set("")
                elif key == "ngay_sinh":
                    # Cho phép set_date
                    widget.config(state=tk.NORMAL)
                else:
                    widget.config(state=tk.NORMAL)
                    widget.delete(0, tk.END)
            
            # Điền đầy đủ dữ liệu từ treeview lên textbox
            # Index: 0=MaNV, 1=TenNV, 2=GioiTinh, 3=NgaySinh, 4=DienThoai, 5=DiaChi
            self.entries["ma_nhanvien"].insert(0, str(values[0]))
            self.entries["ma_nhanvien"].config(state="readonly")
            
            self.entries["ten_nhanvien"].insert(0, str(values[1]) if values[1] else "")
            # Ghi giá trị combobox giới tính khi đang readonly để đảm bảo hiển thị
            self.entries["gioi_tinh"].config(state="readonly")
            self.entries["gioi_tinh"].set(str(values[2]) if values[2] else "Nam")
            
            # Cập nhật DateEntry cho Ngày sinh
            ngay_sinh_str = str(values[3]) if values[3] else ""
            try:
                date_obj = datetime.strptime(ngay_sinh_str, '%Y-%m-%d').date()
                self.entries['ngay_sinh'].set_date(date_obj)
            except (ValueError, AttributeError):
                self.entries['ngay_sinh'].set_date(datetime.now().date())
            
            self.entries["dien_thoai"].insert(0, str(values[4]) if values[4] else "")
            self.entries["dia_chi"].insert(0, str(values[5]) if values[5] else "")
        
        # Giữ nguyên state VIEW (disable lại tất cả), cập nhật lại các nút
        self.set_form_state("VIEW")

    def on_tree_double_click(self, event):
        """Double-click vào dòng → tự động chuyển sang chế độ Sửa"""
        if self.selected_item and self.current_state == "VIEW":
            self.set_edit_state()


if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    app = EmployeeManagementForm(root)
    root.mainloop()