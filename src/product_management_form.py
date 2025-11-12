# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import threading
from auth import get_connection

class ProductManagementForm:
    def __init__(self, master):
        self.master = master
        if isinstance(self.master, tk.Tk):
            self.master.title("Quản lý Hàng hóa")

        self.master.config(bg="#ECEFF1")
        self.current_state = 'VIEW'
        self.selected_item = None
        self.chatlieu_dict = {}

        main_frame = tk.Frame(master, bg="#ECEFF1", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="📦 QUẢN LÝ HÀNG HÓA",
                 font=("Arial", 20, "bold"), fg="#00796B", bg="#ECEFF1").pack(pady=(0, 15))

        # --- Khung tìm kiếm ---
        search_frame = tk.Frame(main_frame, bg="#E0E0E0", padx=10, pady=5)
        search_frame.pack(fill="x", pady=(0, 10))
        tk.Label(search_frame, text="Tìm kiếm (Tên hàng):", bg="#E0E0E0").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(5, 10))
        ttk.Button(search_frame, text="🔍 Tìm", command=self.search_products).pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔄 Đặt lại", command=self.reset_search).pack(side="left", padx=5)

        # --- Form nhập liệu ---
        form_frame = tk.LabelFrame(main_frame, text="Thông tin hàng hóa", bg="#ECEFF1", padx=10, pady=10)
        form_frame.pack(fill=tk.X, pady=5)
        self.entries = {}
        labels = [
            ("Mã hàng:", "ma_hang"),
            ("Tên hàng:", "ten_hang"),
            ("Chất liệu:", "ma_chatlieu"),
            ("Số lượng:", "so_luong"),
            ("Đơn giá nhập:", "don_gia_nhap"),
            ("Đơn vị:", "don_vi"),
            ("Ghi chú:", "ghi_chu")
        ]
        for i, (label, field) in enumerate(labels):
            tk.Label(form_frame, text=label, bg="#ECEFF1").grid(row=i, column=0, sticky="w", pady=3)
            if field == "ma_chatlieu":
                combo = ttk.Combobox(form_frame, state="normal")
                combo.grid(row=i, column=1, sticky="ew", pady=3)
                self.entries[field] = combo
            else:
                entry = tk.Entry(form_frame)
                entry.grid(row=i, column=1, sticky="ew", pady=3)
                self.entries[field] = entry
        self.entries["ma_hang"].config(state="readonly")
        form_frame.columnconfigure(1, weight=1)

        # --- Nút chức năng ---
        button_frame = tk.Frame(main_frame, bg="#ECEFF1")
        button_frame.pack(fill=tk.X, pady=5)
        self.btn_add = tk.Button(button_frame, text="➕ Thêm", command=self.set_add_state, bg="#AED581", width=10)
        self.btn_save = tk.Button(button_frame, text="💾 Lưu", command=self.save_data, bg="#64B5F6", width=10, state=tk.DISABLED)
        self.btn_edit = tk.Button(button_frame, text="📝 Sửa", command=self.set_edit_state, bg="#FFB74D", width=10)
        self.btn_delete = tk.Button(button_frame, text="❌ Xóa", command=self.delete_item, bg="#E57373", width=10)
        self.btn_cancel = tk.Button(button_frame, text="🗑️ Hủy", command=self.cancel_action, bg="#90A4AE", width=10, state=tk.DISABLED)
        for b in [self.btn_add, self.btn_save, self.btn_edit, self.btn_delete, self.btn_cancel]:
            b.pack(side=tk.LEFT, padx=5)

        # --- TreeView ---
        columns = ("MaHang", "TenHang", "TenChatLieu", "SoLuong", "DonGiaNhap", "DonVi", "GhiChu")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        widths = [80, 200, 120, 80, 120, 80, 200]
        for col, text, width in zip(columns, ["Mã hàng", "Tên hàng", "Chất liệu", "SL", "Đơn giá", "Đơn vị", "Ghi chú"], widths):
            self.tree.heading(col, text=text, anchor="center")
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-Button-1>", self.on_tree_double_click)

        # --- Thanh trạng thái ---
        self.status_bar = tk.Label(main_frame, text="Sẵn sàng.", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.set_form_state("VIEW")
        self.master.after(200, self.load_reference_data)
        self.master.after(300, self.load_data)

    # =======================================================
    # KẾT NỐI & LOAD
    # =======================================================
    def get_conn(self):
        try:
            return get_connection()
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối SQL thất bại:\n{e}"))
            return None

    def load_reference_data(self):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MaChatLieu, TenChatLieu FROM tblChatLieu ORDER BY TenChatLieu")
            data = cursor.fetchall()
            self.chatlieu_dict = {r.TenChatLieu: r.MaChatLieu for r in data}
            self.entries["ma_chatlieu"]["values"] = list(self.chatlieu_dict.keys())
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải chất liệu: {e}")
        finally:
            conn.close()

    def load_data(self, search_term=""):
        def _task():
            conn = self.get_conn()
            if not conn:
                self.master.after(0, lambda: self.status_bar.config(text="❌ Lỗi kết nối"))
                return
            try:
                cursor = conn.cursor()
                query = """
                    SELECT h.MaHang, h.TenHang, c.TenChatLieu, h.SoLuong, h.DonGiaNhap, h.DonVi, h.GhiChu
                    FROM tblHang h
                    LEFT JOIN tblChatLieu c ON h.MaChatLieu = c.MaChatLieu
                """
                params = []
                if search_term:
                    query += " WHERE h.TenHang COLLATE Vietnamese_CI_AI LIKE ?"
                    params.append(f"%{search_term}%")
                query += " ORDER BY h.MaHang"
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
        for row in rows:
            self.tree.insert('', tk.END, values=(
                row.MaHang, row.TenHang, row.TenChatLieu,
                row.SoLuong, f"{row.DonGiaNhap:,.0f}", row.DonVi, row.GhiChu
            ))
        self.status_bar.config(text=f"✅ Đã tải {len(rows)} bản ghi.")

    # =======================================================
    # STATE
    # =======================================================
    def set_form_state(self, state):
        self.current_state = state
        editable = state in ("ADD", "EDIT")
        
        for field, entry in self.entries.items():
            if field == "ma_hang":
                # Mã hàng luôn readonly
                entry.config(state="readonly")
            elif field == "ma_chatlieu":
                # Chất liệu: editable khi ADD/EDIT, disabled khi VIEW
                entry.config(state="normal" if editable else "disabled")
            else:
                # Các trường khác: editable khi ADD/EDIT, disabled khi VIEW
                entry.config(state="normal" if editable else "disabled")
        
        has_selection = self.selected_item is not None
        self.btn_add.config(state=tk.NORMAL if state == "VIEW" else tk.DISABLED)
        self.btn_edit.config(state=tk.NORMAL if state == "VIEW" and has_selection else tk.DISABLED)
        self.btn_delete.config(state=tk.NORMAL if state == "VIEW" and has_selection else tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL if editable else tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL if editable else tk.DISABLED)

    def set_add_state(self):
        self.clear_entries()
        # Lấy mã hàng tiếp theo
        next_id = self.get_next_mahang()
        if next_id:
            self.entries["ma_hang"].config(state="normal")
            self.entries["ma_hang"].delete(0, tk.END)
            self.entries["ma_hang"].insert(0, next_id)
            self.entries["ma_hang"].config(state="readonly")
        self.set_form_state("ADD")
        self.entries["ten_hang"].focus()

    def get_next_mahang(self):
        """Lấy mã hàng tiếp theo, ưu tiên lấp khoảng trống (gap) nếu có."""
        conn = self.get_conn()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            
            # Tìm khoảng trống (gap) trong dãy mã
            cursor.execute("""
                SELECT MIN(t1.MaHang + 1) AS NextID
                FROM tblHang t1
                WHERE NOT EXISTS (
                    SELECT 1 FROM tblHang t2 
                    WHERE t2.MaHang = t1.MaHang + 1
                )
                AND t1.MaHang + 1 <= (SELECT MAX(MaHang) FROM tblHang)
            """)
            result = cursor.fetchone()
            gap_id = result[0] if result and result[0] else None
            
            if gap_id:
                # Có khoảng trống → dùng mã đó
                return gap_id
            else:
                # Không có khoảng trống → lấy MAX + 1
                cursor.execute("SELECT MAX(MaHang) FROM tblHang")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] else 0
                return max_id + 1
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lấy mã hàng tiếp theo:\n{e}")
            return None
        finally:
            conn.close()

    def set_edit_state(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn hàng để sửa!")
            return
        
        # Đảm bảo dữ liệu đã được load lên form
        values = self.tree.item(self.selected_item)['values']
        if len(values) >= 7:
            self.entries["ma_hang"].config(state="normal")
            self.entries["ma_hang"].delete(0, tk.END)
            self.entries["ma_hang"].insert(0, values[0])
            self.entries["ma_hang"].config(state="readonly")
            
            self.entries["ten_hang"].delete(0, tk.END)
            self.entries["ten_hang"].insert(0, values[1])
            
            self.entries["ma_chatlieu"].set(values[2])
            
            self.entries["so_luong"].delete(0, tk.END)
            self.entries["so_luong"].insert(0, values[3])
            
            self.entries["don_gia_nhap"].delete(0, tk.END)
            gia_nhap = str(values[4]).replace(",", "").replace(".", "")
            self.entries["don_gia_nhap"].insert(0, gia_nhap)
            
            self.entries["don_vi"].delete(0, tk.END)
            self.entries["don_vi"].insert(0, values[5])
            
            self.entries["ghi_chu"].delete(0, tk.END)
            self.entries["ghi_chu"].insert(0, values[6])
        
        self.set_form_state("EDIT")
        self.entries["ten_hang"].focus()

    def cancel_action(self):
        self.clear_entries()
        self.set_form_state("VIEW")
        self.load_data()

    def clear_entries(self):
        for entry in self.entries.values():
            entry.config(state="normal")
            if isinstance(entry, ttk.Combobox):
                entry.set("")
            else:
                entry.delete(0, tk.END)
        self.selected_item = None

    # =======================================================
    # CRUD (DÙNG THREAD)
    # =======================================================
    def save_data(self):
        ma_hang, data = self.get_validated_data(self.current_state == 'ADD')
        if data is None: return
        if self.current_state == "ADD":
            self.status_bar.config(text="🔄 Đang thêm hàng hóa...")
            threading.Thread(target=self._execute_add_item, args=(data,), daemon=True).start()
        elif self.current_state == "EDIT":
            self.status_bar.config(text=f"🔄 Đang cập nhật Mã {ma_hang}...")
            threading.Thread(target=self._execute_update_item, args=(ma_hang, data), daemon=True).start()

    def _execute_add_item(self, data):
        try:
            conn = self.get_conn()
            if not conn: return
            cursor = conn.cursor()
            ma_chatlieu = self.process_chatlieu(cursor, data["TenChatLieu"], conn)
            
            # Lấy mã hàng từ form (đã tính toán gap)
            ma_hang_moi = int(self.entries["ma_hang"].get())
            
            # Bật IDENTITY_INSERT để chèn mã tùy chỉnh
            cursor.execute("SET IDENTITY_INSERT tblHang ON")
            cursor.execute("""
                INSERT INTO tblHang (MaHang, TenHang, MaChatLieu, SoLuong, DonGiaNhap, DonVi, GhiChu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ma_hang_moi, data["TenHang"], ma_chatlieu, data["SoLuong"], data["DonGiaNhap"], data["DonVi"], data["GhiChu"]))
            cursor.execute("SET IDENTITY_INSERT tblHang OFF")
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã thêm hàng mới với Mã {ma_hang_moi}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã thêm Mã {ma_hang_moi}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Thêm thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def _execute_update_item(self, ma_hang, data):
        try:
            conn = self.get_conn()
            if not conn: return
            cursor = conn.cursor()
            ma_chatlieu = self.process_chatlieu(cursor, data["TenChatLieu"], conn)
            cursor.execute("""
                UPDATE tblHang
                SET TenHang=?, MaChatLieu=?, SoLuong=?, DonGiaNhap=?, DonVi=?, GhiChu=?
                WHERE MaHang=?
            """, (data["TenHang"], ma_chatlieu, data["SoLuong"], data["DonGiaNhap"], data["DonVi"], data["GhiChu"], ma_hang))
            conn.commit()
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", "Đã cập nhật hàng hóa!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã cập nhật Mã {ma_hang}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def delete_item(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn hàng để xóa!")
            return
        ma_hang = self.entries["ma_hang"].get()
        if not messagebox.askyesno("Xác nhận", f"Xóa hàng hóa Mã {ma_hang}?"):
            return
        self.status_bar.config(text=f"🔄 Đang xóa Mã {ma_hang}...")
        threading.Thread(target=self._execute_delete_item, args=(ma_hang,), daemon=True).start()

    def _execute_delete_item(self, ma_hang):
        try:
            conn = self.get_conn()
            if not conn: return
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblHang WHERE MaHang=?", ma_hang)
            conn.commit()
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã xóa Mã {ma_hang}!"),
                self.load_data(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã xóa Mã {ma_hang}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Xóa thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    # =======================================================
    # TIỆN ÍCH
    # =======================================================
    def get_validated_data(self, is_add):
        ma_hang = self.entries['ma_hang'].get().strip() if not is_add else None
        ten_hang = self.entries['ten_hang'].get().strip()
        ten_chatlieu = self.entries['ma_chatlieu'].get().strip()
        so_luong = self.entries['so_luong'].get().strip() or "0"
        don_gia = self.entries['don_gia_nhap'].get().strip() or "0"
        don_vi = self.entries['don_vi'].get().strip()
        ghi_chu = self.entries['ghi_chu'].get().strip()
        try:
            so_luong = int(so_luong)
            don_gia = float(don_gia.replace(",", ""))
        except:
            messagebox.showwarning("Lỗi", "Số lượng hoặc đơn giá không hợp lệ.")
            return None, None
        if not ten_hang or not ten_chatlieu:
            messagebox.showwarning("Thiếu thông tin", "Tên hàng và Chất liệu không được để trống.")
            return None, None
        return ma_hang, {
            "TenHang": ten_hang,
            "TenChatLieu": ten_chatlieu,
            "SoLuong": so_luong,
            "DonGiaNhap": don_gia,
            "DonVi": don_vi,
            "GhiChu": ghi_chu
        }

    def process_chatlieu(self, cursor, ten_chatlieu, conn):
        if ten_chatlieu in self.chatlieu_dict:
            return self.chatlieu_dict[ten_chatlieu]
        cursor.execute("INSERT INTO tblChatLieu (TenChatLieu) VALUES (?)", ten_chatlieu)
        conn.commit()
        cursor.execute("SELECT @@IDENTITY")
        new_id = int(cursor.fetchone()[0])
        self.chatlieu_dict[ten_chatlieu] = new_id
        return new_id
    def search_products(self):
        """Hàm tìm kiếm sản phẩm theo tên hoặc chất liệu."""
        keyword = self.search_var.get().strip().lower()
        if not keyword:
            self.status_bar.config(text="🔍 Vui lòng nhập từ khóa tìm kiếm!")
            return

        # Xóa dữ liệu cũ trên TreeView
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Mở kết nối DB và tìm kiếm
        try:
            conn = get_connection()
            cursor = conn.cursor()
            query = """
                SELECT h.MaHang, h.TenHang, c.TenChatLieu, h.SoLuong, h.DonGiaNhap, h.DonVi, h.GhiChu
                FROM tblHang AS h
                JOIN tblChatLieu AS c ON h.MaChatLieu = c.MaChatLieu
                WHERE LOWER(h.TenHang) LIKE ? OR LOWER(c.TenChatLieu) LIKE ?
            """
            cursor.execute(query, ('%' + keyword + '%', '%' + keyword + '%'))
            rows = cursor.fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
            self.status_bar.config(text=f"🔍 Tìm thấy {len(rows)} sản phẩm khớp '{keyword}'")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi tìm kiếm: {e}")
        finally:
            if conn:
                conn.close()

    def reset_search(self):
        """Đặt lại ô tìm kiếm và tải lại toàn bộ dữ liệu."""
        self.search_var.set("")
        self.load_data()
        self.status_bar.config(text="🔄 Đã tải lại toàn bộ dữ liệu.")

    def on_tree_select(self, event):
        """Xử lý khi chọn một dòng trong Treeview."""
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
        
        if len(values) >= 7:
            # Clear tất cả trước
            for key in self.entries:
                if key == "ma_chatlieu":
                    self.entries[key].set("")
                else:
                    self.entries[key].config(state="normal")
                    self.entries[key].delete(0, tk.END)
            
            # Điền dữ liệu mới
            self.entries["ma_hang"].insert(0, str(values[0]))
            self.entries["ma_hang"].config(state="readonly")
            
            self.entries["ten_hang"].insert(0, str(values[1]) if values[1] else "")
            
            self.entries["ma_chatlieu"].set(str(values[2]) if values[2] else "")
            
            self.entries["so_luong"].insert(0, str(values[3]) if values[3] else "0")
            
            # Xóa dấu phẩy trong giá trước khi hiển thị
            gia_nhap = str(values[4]).replace(",", "").replace(".", "") if values[4] else "0"
            self.entries["don_gia_nhap"].insert(0, gia_nhap)
            
            self.entries["don_vi"].insert(0, str(values[5]) if values[5] else "")
            
            self.entries["ghi_chu"].insert(0, str(values[6]) if values[6] else "")
        
        # Giữ nguyên state VIEW, cập nhật lại các nút
        self.set_form_state("VIEW")

    def on_tree_double_click(self, event):
        """Double-click vào dòng → tự động chuyển sang chế độ Sửa"""
        if self.selected_item and self.current_state == "VIEW":
            self.set_edit_state()



if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    app = ProductManagementForm(root)
    root.mainloop()
