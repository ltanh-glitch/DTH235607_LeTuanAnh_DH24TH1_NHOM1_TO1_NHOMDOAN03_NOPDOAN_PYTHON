# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import threading
from auth import get_connection # Giả định module auth.py tồn tại và cung cấp get_connection()

class CustomerManagementForm:
    def __init__(self, master):
        self.master = master
        if isinstance(self.master, tk.Tk):
            self.master.title("Quản lý Khách hàng")

        self.master.config(bg="#ECEFF1")
        self.current_state = 'VIEW'
        self.selected_item = None
        
        main_frame = tk.Frame(master, bg="#ECEFF1", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="👤 QUẢN LÝ KHÁCH HÀNG",
                 font=("Arial", 20, "bold"), fg="#00796B", bg="#ECEFF1").pack(pady=(0, 15))

        # --- Khung tìm kiếm (Giống ProductManagementForm) ---
        search_frame = tk.Frame(main_frame, bg="#E0E0E0", padx=10, pady=5)
        search_frame.pack(fill="x", pady=(0, 10))
        tk.Label(search_frame, text="Tìm kiếm (Tên khách):", bg="#E0E0E0").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(5, 10))
        ttk.Button(search_frame, text="🔍 Tìm", command=self.search_customers).pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔄 Đặt lại", command=self.reset_search).pack(side="left", padx=5)

        # --- Form nhập liệu (Sử dụng LabelFrame và bố cục 2 cột) ---
        form_frame = tk.LabelFrame(main_frame, text="Thông tin khách hàng", bg="#ECEFF1", padx=10, pady=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        self.entries = {}
        labels = [
            ("Mã Khách:", "ma_khach"), 
            ("Tên Khách:", "ten_khach"),
            ("Điện thoại:", "dien_thoai"),
            ("Địa chỉ:", "dia_chi"), # Đưa Địa chỉ xuống dòng 2 (cột trái)
        ]
        
        for i, (label, field) in enumerate(labels):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(form_frame, text=label, bg="#ECEFF1").grid(row=row, column=col, sticky="w", padx=(5, 0), pady=3)
            
            entry = tk.Entry(form_frame)
            entry.grid(row=row, column=col + 1, sticky="ew", padx=5, pady=3)
            self.entries[field] = entry

        self.entries["ma_khach"].config(state="readonly")
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        # --- Nút chức năng (Sử dụng tk.Button với màu sắc) ---
        button_frame = tk.Frame(main_frame, bg="#ECEFF1")
        button_frame.pack(fill=tk.X, pady=5)
        self.btn_add = tk.Button(button_frame, text="➕ Thêm", command=self.set_add_state, bg="#AED581", width=10)
        self.btn_save = tk.Button(button_frame, text="💾 Lưu", command=self.save_data, bg="#64B5F6", width=10, state=tk.DISABLED)
        self.btn_edit = tk.Button(button_frame, text="📝 Sửa", command=self.set_edit_state, bg="#FFB74D", width=10)
        self.btn_delete = tk.Button(button_frame, text="❌ Xóa", command=self.delete_customer, bg="#E57373", width=10)
        self.btn_cancel = tk.Button(button_frame, text="🗑️ Hủy", command=self.cancel_action, bg="#90A4AE", width=10, state=tk.DISABLED)
        for b in [self.btn_add, self.btn_save, self.btn_edit, self.btn_delete, self.btn_cancel]:
            b.pack(side=tk.LEFT, padx=5)

        # --- TreeView ---
        columns = ("MaKhach", "TenKhach", "DiaChi", "DienThoai")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        widths = [100, 220, 300, 130]
        for col, text, width in zip(columns, ["Mã Khách", "Tên Khách", "Địa chỉ", "Điện thoại"], widths):
            self.tree.heading(col, text=text, anchor="center")
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Thanh cuộn (giữ nguyên)
        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Style xen kẽ (giữ nguyên)
        self.tree.tag_configure('oddrow', background="#F5F5F5") 
        self.tree.tag_configure('evenrow', background="#FFFFFF") 
        
        # --- Bắt sự kiện chọn ---
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select) # Đổi tên hàm
        self.tree.bind("<Double-Button-1>", self.on_tree_double_click)

        # --- Thanh trạng thái ---
        self.status_bar = tk.Label(main_frame, text="Sẵn sàng.", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.set_form_state("VIEW")
        self.master.after(300, self.load_data) # Bắt đầu tải dữ liệu bằng Threading

    # =======================================================
    # KẾT NỐI & LOAD (Dùng Threading, giống ProductForm)
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
                query = "SELECT MaKhach, TenKhach, DiaChi, DienThoai FROM tblKhach"
                params = []
                if search_term:
                    # Sửa lại query để chỉ tìm kiếm theo TenKhach (theo yêu cầu ban đầu)
                    query += " WHERE TenKhach COLLATE Vietnamese_CI_AI LIKE ?"
                    params.append(f"%{search_term}%")
                query += " ORDER BY MaKhach ASC"
                cursor.execute(query, params)
                rows = cursor.fetchall()
                self.master.after(0, lambda: self._update_treeview(rows))
            except Exception as e:
                self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Tải dữ liệu thất bại:\n{e}"))
            finally:
                if conn: conn.close()

        self.status_bar.config(text="🔄 Đang tải dữ liệu...")
        threading.Thread(target=_task, daemon=True).start()

    def _update_treeview(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(rows):
            formatted_row = (
                row.MaKhach, row.TenKhach, row.DiaChi or '', row.DienThoai or ''
            )
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert('', tk.END, values=formatted_row, tags=(tag,))

        self.status_bar.config(text=f"✅ Đã tải {len(rows)} bản ghi.")
    
    def search_customers(self):
        keyword = self.search_var.get().strip()
        if not keyword:
            self.status_bar.config(text="🔍 Vui lòng nhập từ khóa tìm kiếm!")
            return
        self.load_data(keyword)

    def reset_search(self):
        self.search_var.set("")
        self.load_data()
        self.status_bar.config(text="🔄 Đã tải lại toàn bộ dữ liệu.")

    # =======================================================
    # STATE (Đã đồng bộ với ProductForm)
    # =======================================================
    def set_form_state(self, state):
        self.current_state = state
        editable = state in ("ADD", "EDIT")
        
        for field, entry in self.entries.items():
            if field == "ma_khach":
                entry.config(state="readonly")
            else:
                entry.config(state=tk.NORMAL if editable else tk.DISABLED)
        
        has_selection = self.selected_item is not None
        self.btn_add.config(state=tk.NORMAL if state == "VIEW" else tk.DISABLED)
        self.btn_edit.config(state=tk.NORMAL if state == "VIEW" and has_selection else tk.DISABLED)
        self.btn_delete.config(state=tk.NORMAL if state == "VIEW" and has_selection else tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL if editable else tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL if editable else tk.DISABLED)

    def set_add_state(self):
        self.clear_entries()
        next_id = self.get_next_makhach()
        if next_id is not None:
            self.entries["ma_khach"].config(state="normal")
            self.entries["ma_khach"].delete(0, tk.END)
            self.entries["ma_khach"].insert(0, next_id)
            self.entries["ma_khach"].config(state="readonly")
        self.set_form_state("ADD")
        self.entries["ten_khach"].focus()

    def get_next_makhach(self):
        """Lấy mã khách tiếp theo (tìm gap ID), đã đồng bộ với ProductForm."""
        conn = self.get_conn()
        if not conn: return None
        try:
            cursor = conn.cursor()
            # Tìm khoảng trống (gap)
            cursor.execute("""
                SELECT MIN(t1.MaKhach + 1) AS NextID
                FROM tblKhach t1
                WHERE NOT EXISTS (
                    SELECT 1 FROM tblKhach t2 
                    WHERE t2.MaKhach = t1.MaKhach + 1
                )
                AND t1.MaKhach + 1 <= (SELECT MAX(MaKhach) FROM tblKhach)
            """)
            result = cursor.fetchone()
            gap_id = result[0] if result and result[0] else None
            
            if gap_id:
                return gap_id
            else:
                cursor.execute("SELECT MAX(MaKhach) FROM tblKhach")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] else 0
                return max_id + 1
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể lấy mã khách tiếp theo:\n{e}"))
            return None
        finally:
            conn.close()

    def set_edit_state(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn khách hàng để sửa!")
            return
        # Dữ liệu đã được điền trong on_tree_select
        self.set_form_state("EDIT")
        self.entries["ten_khach"].focus()

    def cancel_action(self):
        self.clear_entries()
        self.set_form_state("VIEW")
        self.load_data()

    def clear_entries(self):
        self.entries['ma_khach'].config(state='normal')
        for entry in self.entries.values():
            entry.config(state="normal")
            entry.delete(0, tk.END)
                
        self.entries['ma_khach'].config(state='readonly')
        self.selected_item = None
        self.tree.selection_remove(self.tree.selection())

    # =======================================================
    # CRUD (Dùng Threading, giống ProductForm)
    # =======================================================
    def save_data(self):
        ma_khach, data = self.get_validated_data()
        if data is None: return
        
        if self.current_state == "ADD":
            next_id = int(self.entries["ma_khach"].get()) # Lấy ID đã tính gap
            self.status_bar.config(text="🔄 Đang thêm khách hàng...")
            threading.Thread(target=self._execute_add_item, args=(next_id, data,), daemon=True).start()
        elif self.current_state == "EDIT":
            self.status_bar.config(text=f"🔄 Đang cập nhật Mã {ma_khach}...")
            threading.Thread(target=self._execute_update_item, args=(ma_khach, data), daemon=True).start()

    def _execute_add_item(self, next_id, data):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            
            # Bật IDENTITY_INSERT để chèn mã tùy chỉnh
            cursor.execute("SET IDENTITY_INSERT tblKhach ON")
            cursor.execute("""
                INSERT INTO tblKhach (MaKhach, TenKhach, DiaChi, DienThoai)
                VALUES (?, ?, ?, ?)
            """, (next_id, data['TenKhach'], data['DiaChi'], data['DienThoai']))
            cursor.execute("SET IDENTITY_INSERT tblKhach OFF")
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã thêm khách hàng với Mã {next_id}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã thêm Mã {next_id}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Thêm thất bại:\n{e}"))
        finally:
            if conn: 
                try: cursor.execute("SET IDENTITY_INSERT tblKhach OFF")
                except: pass
                conn.close()

    def _execute_update_item(self, ma_khach, data):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tblKhach 
                SET TenKhach=?, DiaChi=?, DienThoai=?
                WHERE MaKhach=?
            """, (data['TenKhach'], data['DiaChi'], data['DienThoai'], ma_khach))
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã cập nhật Mã {ma_khach}!"),
                self.load_data(), # Tải lại để cập nhật TreeView
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã cập nhật Mã {ma_khach}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def delete_customer(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn khách hàng để xóa!")
            return
        ma_khach = self.entries["ma_khach"].get()
        if not messagebox.askyesno("Xác nhận", f"Xóa khách hàng Mã {ma_khach}?"):
            return
        self.status_bar.config(text=f"🔄 Đang xóa Mã {ma_khach}...")
        threading.Thread(target=self._execute_delete_item, args=(ma_khach,), daemon=True).start()

    def _execute_delete_item(self, ma_khach):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblKhach WHERE MaKhach=?", (ma_khach,))
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã xóa Mã {ma_khach}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã xóa Mã {ma_khach}")
            ])
        except pyodbc.IntegrityError:
             self.master.after(0, lambda: messagebox.showerror("Lỗi DB", f"Không thể xóa khách hàng Mã {ma_khach} vì có dữ liệu liên quan (Hóa đơn, ...)"))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Xóa thất bại:\n{e}"))
        finally:
            if conn: conn.close()
            
    # =======================================================
    # TIỆN ÍCH
    # =======================================================
    def get_validated_data(self):
        ma_khach = self.entries['ma_khach'].get().strip()
        ten_khach = self.entries['ten_khach'].get().strip()
        dia_chi = self.entries['dia_chi'].get().strip()
        dien_thoai = self.entries['dien_thoai'].get().strip()
        
        if not ten_khach:
            messagebox.showwarning("Thiếu thông tin", "Tên khách hàng không được để trống.")
            return None, None
            
        return ma_khach, {
            "TenKhach": ten_khach,
            "DiaChi": dia_chi,
            "DienThoai": dien_thoai,
        }

    def on_tree_select(self, event):
        """Xử lý khi chọn một dòng trong Treeview."""
        if self.current_state != "VIEW":
            return
            
        selected = self.tree.selection()
        if not selected:
            self.selected_item = None
            self.set_form_state("VIEW")
            return
            
        self.selected_item = selected[0]
        values = self.tree.item(self.selected_item)['values']
        
        if values:
            # Tương tự ProductForm, clear entries và điền dữ liệu
            self.entries['ma_khach'].config(state='normal')
            for entry in self.entries.values():
                entry.config(state='normal')
                entry.delete(0, tk.END)
                
            self.entries["ma_khach"].insert(0, str(values[0]))
            self.entries["ma_khach"].config(state="readonly")
            
            self.entries["ten_khach"].insert(0, str(values[1]) if values[1] else "")
            self.entries["dia_chi"].insert(0, str(values[2]) if values[2] else "")
            self.entries["dien_thoai"].insert(0, str(values[3]) if values[3] else "")
        
        self.set_form_state("VIEW")

    def on_tree_double_click(self, event):
        """Double-click vào dòng → tự động chuyển sang chế độ Sửa"""
        if self.selected_item and self.current_state == "VIEW":
            self.set_edit_state()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("QUẢN LÝ KHÁCH HÀNG")
    root.state('zoomed') 
    app = CustomerManagementForm(root)
    root.mainloop()