# -*- coding: utf-8 -*-
# account_management_form.py - Module Quản lý Tài khoản (Dùng Threading)
import tkinter as tk
from tkinter import ttk, messagebox
from auth import get_connection
import pyodbc 
import threading

class AccountManagementForm:
    def __init__(self, master):
        self.master = master
        if isinstance(self.master, tk.Tk):
            self.master.title("Quản lý Tài khoản")

        # ----- Color palette (inspired by secure dashboard) -----
        self.APP_BG = "#ECEFF1"          # overall background
        self.APP_BAR_BG = "#0F172A"      # dark app bar
        self.APP_BAR_FG = "#E2E8F0"      # light text on app bar
        self.ACCENT = "#10B981"          # emerald accent
        self.PANEL_BG = "#F1F5F9"        # panel/search bg
        self.FORM_BG = "#F8FAFC"         # form bg
        self.TEXT_MAIN = "#111827"       # main text

        self.master.config(bg=self.APP_BG)
        self.current_state = 'VIEW'
        self.selected_item = None
        self.nhanvien_map = {}  # Map TenNV to MaNV
        self.quyen_map = {0: "ADMIN (0)", 1: "Quản lý (1)", 2: "Nhân viên (2)"}
        self.trangthai_map = {1: "Hoạt động (1)", 0: "Bị khóa (0)"}
        
        main_frame = tk.Frame(master, bg="#ECEFF1", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True) # Sử dụng fill=tk.BOTH và expand=True

        # ----- App Bar -----
        appbar = tk.Frame(main_frame, bg=self.APP_BAR_BG)
        appbar.pack(fill="x", pady=(0, 10))
        tk.Label(
            appbar,
            text="🔐 QUẢN LÝ TÀI KHOẢN",
            font=("Segoe UI", 18, "bold"),
            fg=self.APP_BAR_FG,
            bg=self.APP_BAR_BG,
            padx=10,
            pady=8,
        ).pack(side="left")
        tk.Frame(main_frame, bg=self.ACCENT, height=2).pack(fill="x", pady=(0, 12))

        # --- Khung tìm kiếm (Dạng Frame đơn giản) ---
        search_frame = tk.Frame(main_frame, bg=self.PANEL_BG, padx=10, pady=8)
        search_frame.pack(fill="x", pady=(0, 10))
        tk.Label(search_frame, text="Tìm kiếm (Tên ĐN/NV):", bg=self.PANEL_BG, fg=self.TEXT_MAIN).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        self.search_entry.pack(side="left", padx=(5, 10))
        ttk.Button(search_frame, text="🔍 Tìm", command=self.search_accounts).pack(side="left", padx=5)
        ttk.Button(search_frame, text="🔄 Đặt lại", command=self.reset_search).pack(side="left", padx=5)

        # --- Form nhập liệu (Sử dụng LabelFrame) ---
        form_frame = tk.LabelFrame(main_frame, text="Thông tin tài khoản", bg=self.FORM_BG, padx=10, pady=10, fg=self.TEXT_MAIN)
        form_frame.pack(fill=tk.X, pady=5)
        
        fields = [
            ("Mã TK:", "ma_tk"),
            ("Nhân viên:", "ma_nhanvien"),
            ("Tên ĐN:", "ten_dang_nhap"),
            ("Mật khẩu:", "mat_khau"),
            ("Phân quyền:", "phan_quyen"),
            ("Trạng thái:", "trang_thai"),
        ]
        
        self.entries = {}
        for i, (label, field) in enumerate(fields):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(form_frame, text=label, bg=self.FORM_BG, fg=self.TEXT_MAIN).grid(row=row, column=col, sticky="w", padx=(5, 0), pady=3)
            
            if field == "ma_nhanvien":
                combo = ttk.Combobox(form_frame, state="readonly")
                combo.grid(row=row, column=col+1, sticky="ew", padx=5, pady=3)
                self.entries[field] = combo
            elif field == "phan_quyen":
                combo = ttk.Combobox(form_frame, state="readonly", values=list(self.quyen_map.values()))
                combo.grid(row=row, column=col+1, sticky="ew", padx=5, pady=3)
                self.entries[field] = combo
                self.entries[field].set(self.quyen_map[2])
            elif field == "trang_thai":
                combo = ttk.Combobox(form_frame, state="readonly", values=list(self.trangthai_map.values()))
                combo.grid(row=row, column=col+1, sticky="ew", padx=5, pady=3)
                self.entries[field] = combo
                self.entries[field].set(self.trangthai_map[1])
            else:
                entry = tk.Entry(form_frame)
                entry.grid(row=row, column=col+1, sticky="ew", padx=5, pady=3)
                self.entries[field] = entry

            if field == "ma_tk":
                self.entries[field].config(state="readonly")
            elif field == "mat_khau":
                # Thêm hiệu ứng bảo mật cho Mật khẩu
                self.entries[field].config(show="●", bg="#424242", fg="white", insertbackground="white")
        
        form_frame.columnconfigure(1, weight=1)
        form_frame.columnconfigure(3, weight=1)

        # --- Nút chức năng (Sử dụng tk.Button với màu sắc) ---
        button_frame = tk.Frame(main_frame, bg=self.APP_BG)
        button_frame.pack(fill=tk.X, pady=5)
        self.btn_add = tk.Button(button_frame, text="➕ Thêm", command=self.set_add_state, bg="#AED581", width=10)
        self.btn_save = tk.Button(button_frame, text="💾 Lưu", command=self.save_data, bg="#64B5F6", width=10, state=tk.DISABLED)
        self.btn_edit = tk.Button(button_frame, text="📝 Sửa", command=self.set_edit_state, bg="#FFB74D", width=10)
        self.btn_delete = tk.Button(button_frame, text="❌ Xóa", command=self.delete_account, bg="#E57373", width=10)
        self.btn_cancel = tk.Button(button_frame, text="🗑️ Hủy", command=self.cancel_action, bg="#90A4AE", width=10, state=tk.DISABLED)
        for b in [self.btn_add, self.btn_save, self.btn_edit, self.btn_delete, self.btn_cancel]:
            b.pack(side=tk.LEFT, padx=5)

        # Nút/checkbox hiện ẩn mật khẩu trên ô nhập
        self.show_pw_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            button_frame,
            text="👁 Hiện Password",
            variable=self.show_pw_var,
            command=self.toggle_pw_visibility,
            bg=self.APP_BG
        ).pack(side=tk.LEFT, padx=8)
        
        # --- Treeview (Bảng hiển thị) ---
        # ----- ttk Styles for professional look -----
        self._init_styles()

        self.tree = ttk.Treeview(
            main_frame,
            columns=("MaTK", "TenNV", "TenDangNhap", "MatKhau", "PhanQuyen", "TrangThai"),
            show="headings",
            height=15,
            style="Secure.Treeview"
        )
        
        widths = [80, 240, 160, 140, 120, 120]
        for col, text, width in zip(self.tree['columns'], ["Mã TK", "Tên Nhân Viên", "Tên ĐN", "Mật khẩu", "Quyền", "Trạng Thái"], widths):
            self.tree.heading(col, text=text, anchor="center")
            self.tree.column(col, width=width, anchor="center")
            
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- Thanh cuộn, Style, Bắt sự kiện ---
        scrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.tag_configure('oddrow', background="#F5F5F5") 
        self.tree.tag_configure('evenrow', background="#FFFFFF")

        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)
        self.tree.bind("<Double-Button-1>", lambda e: self.set_edit_state()) # Thêm double click

        # Thanh trạng thái
        self.status_bar = tk.Label(main_frame, text="Sẵn sàng.", bd=1, relief=tk.SUNKEN, anchor="w", bg=self.PANEL_BG)
        self.status_bar.pack(side="bottom", fill="x")

        # Khởi tạo dữ liệu
        self.load_nhanvien_list() # Chạy trên luồng chính
        self.set_form_state('VIEW')
        self.load_accounts() # Chạy trên luồng nền

    def _init_styles(self):
        """Configure ttk styles for a modern, secure-dashboard look."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        # Treeview
        style.configure(
            "Secure.Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=self.TEXT_MAIN,
            rowheight=26,
            bordercolor="#CBD5E1",
            borderwidth=1,
        )
        style.map(
            "Secure.Treeview",
            background=[('selected', '#2563EB')],
            foreground=[('selected', '#FFFFFF')]
        )
        style.configure(
            "Secure.Treeview.Heading",
            background=self.APP_BAR_BG,
            foreground=self.APP_BAR_FG,
            relief='flat'
        )
        style.map("Secure.Treeview.Heading", background=[('active', '#1F2937')])

    def toggle_pw_visibility(self):
        """Hiện/ẩn nội dung ô mật khẩu trên form theo checkbox."""
        try:
            if self.show_pw_var.get():
                self.entries['mat_khau'].config(show="")
            else:
                self.entries['mat_khau'].config(show="●")
        except Exception:
            pass

    # =======================================================
    # KẾT NỐI & LOAD (Dùng Threading)
    # =======================================================
    def get_conn(self):
        try:
            return get_connection()
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối SQL thất bại:\n{e}"))
            return None

    def load_nhanvien_list(self):
        """Tải danh sách Nhân viên (MaNV và TenNV) vào self.nhanvien_map và ComboBox."""
        conn = self.get_conn()
        if conn is None: return

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MaNhanVien, TenNhanVien FROM tblNhanVien ORDER BY TenNhanVien")
            rows = cursor.fetchall()

            self.nhanvien_map = {}
            nhanvien_names = ["-- Chọn Nhân viên --"]
            
            for ma, ten in rows:
                self.nhanvien_map[ten] = ma
                nhanvien_names.append(ten)

            self.entries['ma_nhanvien']['values'] = nhanvien_names
            self.entries['ma_nhanvien'].set(nhanvien_names[0])
        except Exception as e:
            messagebox.showerror("Lỗi DB", f"Lỗi tải danh sách Nhân viên: {e}")
        finally:
            if conn: conn.close()
            
    def get_next_matk(self):
        """Lấy Mã TK tiếp theo (dùng MAX+1, do Mã TK thường là IDENTITY tự tăng)"""
        conn = self.get_conn()
        if conn is None: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(MaTK) FROM tblTaiKhoan")
            max_id = cursor.fetchone()[0]
            next_id = 1 if max_id is None else max_id + 1
            return next_id
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể lấy Mã TK tiếp theo:\n{e}"))
            return None
        finally:
            if conn: conn.close()

    def _load_data_in_thread(self, search_term=""):
        conn = self.get_conn()
        if not conn:
            self.master.after(0, lambda: self._update_treeview_from_thread(None, "❌ Lỗi: Không thể kết nối DB."))
            return

        try:
            cursor = conn.cursor()
            sql_query = """
                SELECT tk.MaTK, nv.TenNhanVien, tk.TenDangNhap, tk.MatKhau, tk.PhanQuyen, tk.TrangThai 
                FROM tblTaiKhoan tk
                LEFT JOIN tblNhanVien nv ON tk.MaNhanVien = nv.MaNhanVien
            """
            params = []
            
            if search_term:
                sql_query += " WHERE tk.TenDangNhap COLLATE Vietnamese_CI_AI LIKE ? OR nv.TenNhanVien COLLATE Vietnamese_CI_AI LIKE ?"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
                
            sql_query += " ORDER BY tk.MaTK ASC"
            
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
            
            formatted_rows = []
            for row in rows:
                ma_tk, ten_nv, ten_dn, mat_khau_raw, phan_quyen, trang_thai = row
                # ADMIN xem được mật khẩu dạng rõ trên bảng
                plain_pw = "" if mat_khau_raw is None else str(mat_khau_raw)
                # Chuyển mã quyền/trạng thái thành tên hiển thị
                quyen_text = self.quyen_map.get(phan_quyen, "Không rõ")
                trangthai_text = self.trangthai_map.get(trang_thai, "Không rõ")
                formatted_rows.append((
                    ma_tk,
                    ten_nv or 'Chưa gán NV',
                    ten_dn,
                    plain_pw,
                    quyen_text,
                    trangthai_text
                ))
            
            self.master.after(0, lambda: self._update_treeview_from_thread(formatted_rows, f"✅ Đã tải {len(rows)} bản ghi."))

        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Tải dữ liệu thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def _update_treeview_from_thread(self, rows, status_message):
        self.tree.delete(*self.tree.get_children())
        
        if rows:
            for i, row in enumerate(rows):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                self.tree.insert("", tk.END, values=row, tags=(tag,))
        
        self.status_bar.config(text=status_message)

    def load_accounts(self, search_term=""):
        self.status_bar.config(text="🔄 Đang tải dữ liệu, vui lòng chờ...")
        threading.Thread(target=self._load_data_in_thread, args=(search_term,), daemon=True).start()

    # --- Các hàm CRUD (Sử dụng Threading/Luồng chính tùy loại) ---
    
    def save_data(self):
        is_add = self.current_state == 'ADD'
        data = self.get_form_data(is_update=not is_add)
        if data is None: return

        if is_add:
            self.status_bar.config(text="🔄 Đang thêm tài khoản...")
            threading.Thread(target=self._execute_add_item, args=(data,), daemon=True).start()
        elif self.current_state == "EDIT":
            ma_tk = data["MaTK"]
            self.status_bar.config(text=f"🔄 Đang cập nhật Mã {ma_tk}...")
            threading.Thread(target=self._execute_update_item, args=(ma_tk, data), daemon=True).start()

    def _execute_add_item(self, data):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tblTaiKhoan (MaNhanVien, TenDangNhap, MatKhau, PhanQuyen, TrangThai)
                OUTPUT INSERTED.MaTK
                VALUES (?, ?, ?, ?, ?)
            """, (data['MaNhanVien'], data['TenDangNhap'], data['MatKhau'], data['PhanQuyen'], data['TrangThai']))
            new_id = cursor.fetchone()[0] 
            conn.commit()

            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã thêm tài khoản mới Mã {new_id}!"),
                self.load_accounts(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã thêm Mã {new_id}")
            ])
        except pyodbc.IntegrityError:
            self.master.after(0, lambda: messagebox.showerror("Lỗi DB", "Tên đăng nhập đã tồn tại! Vui lòng chọn tên khác."))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Thêm thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def _execute_update_item(self, ma_tk, data):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            
            if data['MatKhau']:
                sql = "UPDATE tblTaiKhoan SET MaNhanVien=?, TenDangNhap=?, MatKhau=?, PhanQuyen=?, TrangThai=? WHERE MaTK=?"
                params = (data['MaNhanVien'], data['TenDangNhap'], data['MatKhau'], data['PhanQuyen'], data['TrangThai'], ma_tk)
            else:
                sql = "UPDATE tblTaiKhoan SET MaNhanVien=?, TenDangNhap=?, PhanQuyen=?, TrangThai=? WHERE MaTK=?"
                params = (data['MaNhanVien'], data['TenDangNhap'], data['PhanQuyen'], data['TrangThai'], ma_tk)
            
            cursor.execute(sql, params)
            conn.commit()

            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã cập nhật Mã {ma_tk}!"),
                self.load_accounts(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã cập nhật Mã {ma_tk}")
            ])
        except pyodbc.IntegrityError:
             self.master.after(0, lambda: messagebox.showerror("Lỗi DB", "Tên đăng nhập đã tồn tại! Vui lòng chọn tên khác."))
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Cập nhật thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    def delete_account(self):
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn tài khoản để xóa!")
            return
        ma_tk = self.entries["ma_tk"].get()
        if not messagebox.askyesno("Xác nhận", f"Xóa tài khoản Mã {ma_tk}?"):
            return
        self.status_bar.config(text=f"🔄 Đang xóa Mã {ma_tk}...")
        threading.Thread(target=self._execute_delete_item, args=(ma_tk,), daemon=True).start()

    def _execute_delete_item(self, ma_tk):
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tblTaiKhoan WHERE MaTK=?", (ma_tk,))
            conn.commit()
            
            self.master.after(0, lambda: [
                messagebox.showinfo("Thành công", f"Đã xóa Mã {ma_tk}!"),
                self.load_accounts(),
                self.clear_entries(),
                self.set_form_state("VIEW"),
                self.status_bar.config(text=f"✅ Đã xóa Mã {ma_tk}")
            ])
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Xóa thất bại:\n{e}"))
        finally:
            if conn: conn.close()

    # =======================================================
    # QUẢN LÝ TRẠNG THÁI & TIỆN ÍCH
    # =======================================================
    def set_form_state(self, state):
        self.current_state = state
        is_view = state == 'VIEW'
        is_add = state == 'ADD'
        is_edit = state == 'EDIT'

        for key, entry in self.entries.items():
            if key == 'ma_tk':
                entry.config(state="readonly")
            elif key in ['ma_nhanvien', 'phan_quyen', 'trang_thai']:
                entry.config(state="readonly" if not is_view else tk.DISABLED)
            elif key == 'mat_khau':
                # Đảm bảo trường mật khẩu luôn cho phép nhập khi ADD/EDIT
                entry.config(state=tk.NORMAL if not is_view else tk.DISABLED)
            else:
                entry.config(state=tk.NORMAL if not is_view else tk.DISABLED)
        
        # Cấu hình màu cho trường Mật khẩu
        if is_add or is_edit:
            self.entries['mat_khau'].config(bg="#424242", fg="white", insertbackground="white")
        else:
            self.entries['mat_khau'].config(bg="SystemButtonFace", fg="black") # Trở về màu mặc định (hoặc màu nền)

        has_selection = self.selected_item is not None
        self.btn_add.config(state=tk.NORMAL if is_view else tk.DISABLED)
        self.btn_edit.config(state=tk.NORMAL if is_view and has_selection else tk.DISABLED)
        self.btn_delete.config(state=tk.NORMAL if is_view and has_selection else tk.DISABLED)
        self.btn_save.config(state=tk.NORMAL if is_add or is_edit else tk.DISABLED)
        self.btn_cancel.config(state=tk.NORMAL if is_add or is_edit else tk.DISABLED)

    # ==========================
    # STATE HELPERS (THÊM/SỬA/HỦY)
    # ==========================
    def clear_entries(self):
        """Xóa dữ liệu trên form, reset về mặc định an toàn cho VIEW."""
        # Mã TK: tạm mở để xóa rồi lại readonly
        self.entries['ma_tk'].config(state='normal')
        self.entries['ma_tk'].delete(0, tk.END)
        self.entries['ma_tk'].config(state='readonly')

        # Các trường text
        for k in ['ten_dang_nhap', 'mat_khau']:
            self.entries[k].config(state=tk.NORMAL)
            self.entries[k].delete(0, tk.END)

        # Combobox Nhân viên
        try:
            default_nv = self.entries['ma_nhanvien']['values'][0]
            self.entries['ma_nhanvien'].set(default_nv)
        except Exception:
            self.entries['ma_nhanvien'].set("-- Chọn Nhân viên --")

            # Combobox Quyền/Trạng thái về mặc định
            self.entries['phan_quyen'].set(self.quyen_map[2])
            self.entries['trang_thai'].set(self.trangthai_map[1])

    def set_add_state(self):
        """Chuyển sang chế độ THÊM: làm trống form, gán Mã TK tiếp theo, mở ô nhập."""
        self.clear_entries()
        self.selected_item = None
        next_id = self.get_next_matk()
        if next_id is not None:
            self.entries['ma_tk'].config(state='normal')
            self.entries['ma_tk'].delete(0, tk.END)
            self.entries['ma_tk'].insert(0, str(next_id))
            self.entries['ma_tk'].config(state='readonly')
        self.set_form_state('ADD')
        self.entries['ten_dang_nhap'].focus_set()

    def set_edit_state(self):
        """Chuyển sang chế độ SỬA. Dữ liệu đã được load khi chọn TreeView."""
        if not self.selected_item:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn tài khoản để sửa!")
            return
        self.set_form_state('EDIT')
        self.entries['ten_dang_nhap'].focus_set()

    def cancel_action(self):
        """Hủy thao tác đang làm, trở về VIEW và tải lại dữ liệu."""
        self.clear_entries()
        self.selected_item = None
        self.set_form_state('VIEW')
        self.load_accounts()

    def get_form_data(self, is_update=False):
        data = {
            "MaTK": self.entries['ma_tk'].get() or None,
            "TenDangNhap": self.entries['ten_dang_nhap'].get().strip(),
            "MatKhau": self.entries['mat_khau'].get(),
        }
        
        ten_nv_chon = self.entries['ma_nhanvien'].get()
        data["MaNhanVien"] = self.nhanvien_map.get(ten_nv_chon) if ten_nv_chon != "-- Chọn Nhân viên --" else None
        
        quyen_text = self.entries['phan_quyen'].get()
        trangthai_text = self.entries['trang_thai'].get()
        
        # Chuyển tên quyền/trạng thái thành mã số (0, 1, 2)
        data["PhanQuyen"] = next((k for k, v in self.quyen_map.items() if v == quyen_text), None)
        data["TrangThai"] = next((k for k, v in self.trangthai_map.items() if v == trangthai_text), None)
        
        if not data["TenDangNhap"]:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Tên đăng nhập.")
            return None
        
        # Kiểm tra mật khẩu chỉ bắt buộc khi THÊM
        if not is_update and not data["MatKhau"]:
            messagebox.showwarning("Thiếu thông tin", "Mật khẩu là bắt buộc khi thêm tài khoản mới.")
            return None
            
        return data

    def on_select_item(self, event=None):
        if self.current_state != 'VIEW':
            return
            
        selected_items = self.tree.selection()
        if not selected_items:
            self.clear_entries()
            self.selected_item = None
            self.set_form_state('VIEW')
            return
            
        self.selected_item = selected_items[0]
        values = self.tree.item(self.selected_item, 'values') 
        
        if values:
            ma_tk = values[0]
            # Lấy dữ liệu đầy đủ (bao gồm MaNV)
            raw_data = self._get_raw_data_by_id(ma_tk)
            
            if not raw_data:
                messagebox.showerror("Lỗi", "Không thể tải dữ liệu chi tiết tài khoản.")
                return

            self.clear_entries() # Clear trước để tránh lỗi state
            
            self.entries['ma_tk'].config(state='normal')
            self.entries['ma_tk'].insert(0, raw_data['MaTK'])
            self.entries['ma_tk'].config(state='readonly')
            
            # ComboBox Nhân viên (Hiển thị Tên NV đã liên kết)
            self.entries['ma_nhanvien'].set(values[1])
            
            self.entries['ten_dang_nhap'].insert(0, raw_data['TenDangNhap'])

            # Điền mật khẩu hiện tại (ADMIN có thể xem), mặc định đang ẩn bằng ký tự ●
            self.entries['mat_khau'].config(state=tk.NORMAL)
            self.entries['mat_khau'].delete(0, tk.END)
            if raw_data.get('MatKhau'):
                self.entries['mat_khau'].insert(0, raw_data['MatKhau'])
            # Nếu checkbox "Hiện MK" đang bật thì cho hiển thị rõ
            self.toggle_pw_visibility()
            
            # Do đã thêm cột Mật khẩu vào Treeview (được che), chỉ số thay đổi
            self.entries['phan_quyen'].set(values[4])
            self.entries['trang_thai'].set(values[5])
            
            self.set_form_state('VIEW')

    def _get_raw_data_by_id(self, ma_tk):
        """Lấy dữ liệu thô bao gồm MaNhanVien gốc (chạy trên luồng chính)."""
        conn = self.get_conn()
        if conn is None: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MaTK, MaNhanVien, TenDangNhap, MatKhau, PhanQuyen, TrangThai FROM tblTaiKhoan WHERE MaTK = ?", (ma_tk,))
            row = cursor.fetchone()
            if row:
                return {
                    'MaTK': row[0], 'MaNhanVien': row[1], 'TenDangNhap': row[2], 
                    'MatKhau': row[3], 'PhanQuyen': row[4], 'TrangThai': row[5]
                }
            return None
        except Exception as e:
            print(f"Lỗi lấy dữ liệu thô Tài khoản: {e}")
            return None
        finally:
            if conn: conn.close()

    def search_accounts(self):
        search_term = self.search_var.get().strip()
        self.load_accounts(search_term)

    def reset_search(self):
        self.search_var.set("")
        self.load_accounts()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("QUẢN LÝ TÀI KHOẢN")
    root.state('zoomed') 
    app = AccountManagementForm(root)
    root.mainloop()