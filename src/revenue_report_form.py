# -*- coding: utf-8 -*-
# detailed_invoice_report_form.py - Module Báo cáo Chi tiết Hóa đơn (có Mặt hàng & In)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyodbc
import threading
from datetime import datetime, timedelta
import csv # Thư viện để xuất file CSV
from tkcalendar import DateEntry
from auth import get_connection 

class DetailedInvoiceReportForm:
    def __init__(self, master):
        self.master = master
        if isinstance(self.master, tk.Tk):
            self.master.title("Báo cáo Chi tiết Hóa đơn & Mặt hàng")

        self.master.config(bg="#ECEFF1")
        self.raw_report_data = [] # Lưu trữ dữ liệu thô để xuất ra file

        main_frame = tk.Frame(master, bg="#ECEFF1", padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(main_frame, text="🧾 BÁO CÁO CHI TIẾT GIAO DỊCH",
                 font=("Arial", 20, "bold"), fg="#00796B", bg="#ECEFF1").pack(pady=(0, 15))

        # --- 1. Khung Lọc (Filter Frame) ---
        filter_frame = tk.LabelFrame(main_frame, text="🔍 Điều kiện lọc", bg="#E0E0E0", padx=10, pady=5)
        filter_frame.pack(fill="x", pady=(0, 10))

        # Date Filter
        tk.Label(filter_frame, text="Từ ngày:", bg="#E0E0E0").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.date_from = DateEntry(filter_frame, date_pattern='yyyy-mm-dd', locale='vi_VN', width=15)
        self.date_from.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        try:
            self.date_from.set_date(datetime.now().replace(day=1).date()) 
        except: pass 

        tk.Label(filter_frame, text="Đến ngày:", bg="#E0E0E0").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.date_to = DateEntry(filter_frame, date_pattern='yyyy-mm-dd', locale='vi_VN', width=15)
        self.date_to.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.date_to.set_date(datetime.now().date()) 

        # Employee Filter
        tk.Label(filter_frame, text="Nhân viên:", bg="#E0E0E0").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.employee_filter_var = tk.StringVar(value="Tất cả")
        self.employee_combo = ttk.Combobox(filter_frame, textvariable=self.employee_filter_var, state="readonly", width=20)
        self.employee_combo.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        # Nút Báo cáo/In
        tk.Button(filter_frame, text="📈 Lập Báo cáo", command=self.load_data, bg="#009688", fg="white", width=12).grid(row=0, column=6, padx=(20, 5), pady=5, sticky="e")
        self.btn_export = tk.Button(filter_frame, text="🖨️ In/Xuất File", command=self.export_report, bg="#42A5F5", fg="white", width=12, state=tk.DISABLED)
        self.btn_export.grid(row=0, column=7, padx=5, pady=5, sticky="e")
        tk.Button(filter_frame, text="🗑️ Đặt lại", command=self.reset_filters, bg="#90A4AE", width=8).grid(row=0, column=8, padx=5, pady=5, sticky="e")

        filter_frame.grid_columnconfigure(6, weight=1) 

        # --- 2. TreeView (Bảng Chi tiết Hóa đơn + Mặt hàng) ---
        
        # Thêm các cột chi tiết Mặt hàng: MaHang, TenHang, SL, DG, GG
        columns = ("MaHDBan", "NgayBan", "TenNV", "TenKhach", "MaHang", "TenHang", "SoLuong", "DonGia", "GiamGia", "ThanhTien")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        widths = [80, 100, 150, 150, 80, 200, 70, 100, 50, 120]
        col_names = ["Mã HĐ", "Ngày Bán", "Nhân Viên", "Khách Hàng", "Mã Hàng", "Tên Mặt Hàng", "SL", "Đơn Giá", "Giảm (%)", "Thành Tiền"]

        for col, text, width in zip(columns, col_names, widths):
            self.tree.heading(col, text=text, anchor="center")
            anchor_type = "e" if col in ["SoLuong", "DonGia", "GiamGia", "ThanhTien"] else "w"
            self.tree.column(col, width=width, anchor=anchor_type)
            
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        vscrollbar = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vscrollbar.set)
        vscrollbar.pack(side="right", fill="y")
        
        self.tree.tag_configure('oddrow', background="#F5F5F5") 
        self.tree.tag_configure('evenrow', background="#FFFFFF") 

        # --- 3. Khung Tổng hợp (Summary Frame) ---
        summary_frame = tk.Frame(main_frame, bg="#E0F7FA", padx=10, pady=10, relief=tk.RIDGE, bd=2)
        summary_frame.pack(fill="x", pady=(5, 0))
        
        tk.Label(summary_frame, text="Tổng cộng:", font=("Arial", 12, "bold"), bg="#E0F7FA", fg="#333").pack(side="left", padx=5)
        
        self.lbl_total_orders = tk.Label(summary_frame, text="SL HĐ: 0 | SL Mặt hàng: 0", font=("Arial", 12, "bold"), bg="#E0F7FA", fg="#00796B")
        self.lbl_total_orders.pack(side="left", padx=15)
        
        self.lbl_total_revenue = tk.Label(summary_frame, text="DOANH THU GỘP: 0 VND", font=("Arial", 14, "bold"), bg="#E0F7FA", fg="#D32F2F")
        self.lbl_total_revenue.pack(side="right", padx=5)
        
        # --- 4. Thanh trạng thái ---
        self.status_bar = tk.Label(main_frame, text="Sẵn sàng.", bd=1, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        self.load_reference_data()
        self.load_data()

    # =======================================================
    # KẾT NỐI & LOAD (Dùng Threading)
    # =======================================================
    def get_conn(self):
        try:
            from auth import get_connection
            return get_connection()
        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Kết nối SQL thất bại:\n{e}"))
            return None

    def load_reference_data(self):
        """Tải danh sách Nhân viên cho Combobox lọc."""
        conn = self.get_conn()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MaNhanVien, TenNhanVien FROM tblNhanVien ORDER BY TenNhanVien")
            rows = cursor.fetchall()
            
            self.employee_map = {"Tất cả": None}
            employee_names = ["Tất cả"]
            
            for ma, ten in rows:
                self.employee_map[ten] = ma
                employee_names.append(ten)

            self.employee_combo['values'] = employee_names
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi tải danh sách Nhân viên lọc: {e}")
        finally:
            if conn: conn.close()

    def load_data(self):
        """Khởi tạo luồng nền để tải dữ liệu báo cáo."""
        
        try:
            date_from = self.date_from.get_date()
            date_to = self.date_to.get_date()
            
            # FIX LỖI: Thêm 1 ngày vào ngày kết thúc để bao trọn 24h của ngày đó
            date_to_inclusive = date_to + timedelta(days=1)
            
            date_from_str = date_from.strftime('%Y-%m-%d')
            date_to_inclusive_str = date_to_inclusive.strftime('%Y-%m-%d')
            
        except Exception:
            messagebox.showerror("Lỗi", "Ngày tháng không hợp lệ. Vui lòng kiểm tra lại.")
            return

        employee_name = self.employee_filter_var.get()
        employee_id = self.employee_map.get(employee_name)
        
        self.status_bar.config(text="🔄 Đang tải báo cáo doanh thu...")
        self.btn_export.config(state=tk.DISABLED)
        threading.Thread(target=self._load_report_in_thread, 
                         args=(date_from_str, date_to_inclusive_str, employee_id), 
                         daemon=True).start()

    def _load_report_in_thread(self, date_from_str, date_to_inclusive_str, employee_id):
        conn = self.get_conn()
        if not conn:
            self.master.after(0, lambda: self._update_treeview_from_thread([], 0, 0, 0))
            return

        try:
            cursor = conn.cursor()
            # Tải chi tiết từng mặt hàng trong từng hóa đơn (JOIN tblChiTietHDBan và tblHang)
            query = """
                SELECT 
                    hdb.MaHDBan, 
                    hdb.NgayBan, 
                    nv.TenNhanVien, 
                    k.TenKhach,
                    ct.MaHang,
                    hh.TenHang,
                    ct.SoLuong,
                    ct.DonGia,
                    ct.GiamGia,
                    ct.ThanhTien
                FROM tblHDBan hdb
                JOIN tblNhanVien nv ON hdb.MaNhanVien = nv.MaNhanVien
                LEFT JOIN tblKhach k ON hdb.MaKhach = k.MaKhach
                JOIN tblChiTietHDBan ct ON hdb.MaHDBan = ct.MaHDBan
                JOIN tblHang hh ON ct.MaHang = hh.MaHang
                WHERE hdb.NgayBan >= ? AND hdb.NgayBan < ?
            """
            params = [date_from_str, date_to_inclusive_str]
            
            if employee_id is not None:
                query += " AND hdb.MaNhanVien = ?"
                params.append(employee_id)
            
            query += " ORDER BY hdb.NgayBan DESC, hdb.MaHDBan DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            total_revenue = sum(row.ThanhTien for row in rows)
            total_items = len(rows)
            # Đếm số lượng hóa đơn duy nhất
            unique_hds = len(set(row.MaHDBan for row in rows))
            
            self.master.after(0, lambda: self._update_treeview_from_thread(rows, total_revenue, unique_hds, total_items))

        except Exception as e:
            self.master.after(0, lambda: messagebox.showerror("Lỗi", f"Lỗi lập báo cáo chi tiết:\n{e}"))
        finally:
            if conn: conn.close()

    def _update_treeview_from_thread(self, rows, total_revenue, unique_hds, total_items):
        """Cập nhật Treeview và Khung Tổng hợp trên luồng chính."""
        self.tree.delete(*self.tree.get_children())
        self.raw_report_data = [] # Reset dữ liệu thô
        
        for i, row in enumerate(rows):
            # Định dạng ngày và tiền tệ
            if isinstance(row.NgayBan, datetime):
                 ngay_ban_str = row.NgayBan.strftime("%Y-%m-%d")
            else:
                 ngay_ban_str = str(row.NgayBan)
                 
            tong_tien_str = f"{row.ThanhTien:,.0f}" 

            formatted_row = (
                row.MaHDBan, 
                ngay_ban_str, 
                row.TenNhanVien, 
                row.TenKhach or "Khách lẻ", 
                row.MaHang,
                row.TenHang,
                row.SoLuong,
                f"{row.DonGia:,.0f}",
                f"{row.GiamGia:.0f}",
                tong_tien_str
            )
            self.raw_report_data.append(formatted_row) # Lưu dữ liệu để xuất file

            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.tree.insert('', tk.END, values=formatted_row, tags=(tag,))
        
        # Cập nhật khung tổng hợp
        self.lbl_total_orders.config(text=f"SL HĐ: {unique_hds} | SL Mặt hàng: {total_items}")
        self.lbl_total_revenue.config(text=f"DOANH THU GỘP: {total_revenue:,.0f} VND")
        
        self.status_bar.config(text=f"✅ Đã tải {total_items} chi tiết mặt hàng trong {unique_hds} hóa đơn.")
        self.btn_export.config(state=tk.NORMAL if unique_hds > 0 else tk.DISABLED)


    # =======================================================
    # CHỨC NĂNG IN/XUẤT FILE
    # =======================================================
    def export_report(self):
        """Xuất dữ liệu báo cáo hiện tại ra file CSV."""
        if not self.raw_report_data:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Lưu Báo cáo Chi tiết Giao dịch"
        )
        
        if file_path:
            try:
                # Tiêu đề cột
                header = ["Mã HĐ", "Ngày Bán", "Nhân Viên", "Khách Hàng", "Mã Hàng", "Tên Mặt Hàng", "SL", "Đơn Giá", "Giảm (%)", "Thành Tiền"]
                
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(self.raw_report_data)
                
                messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra file:\n{file_path}")
                self.status_bar.config(text=f"✅ Đã xuất báo cáo thành công.")

            except Exception as e:
                messagebox.showerror("Lỗi Xuất File", f"Không thể ghi dữ liệu ra file:\n{e}")

    # =======================================================
    # TIỆN ÍCH
    # =======================================================
    def reset_filters(self):
        """Đặt lại bộ lọc về mặc định và tải lại dữ liệu."""
        try:
             # Đặt lại đầu tháng trước
            self.date_from.set_date(datetime.now().replace(day=1).date())
        except:
             pass
        self.date_to.set_date(datetime.now().date())
        self.employee_filter_var.set("Tất cả")
        self.load_data()


if __name__ == "__main__":
    # Test độc lập (Cần phải cài tkcalendar)
    root = tk.Tk()
    try:
        from tkcalendar import DateEntry 
        root.state('zoomed')
        app = DetailedInvoiceReportForm(root)
    except ImportError:
        tk.Label(root, text="Lỗi: Vui lòng cài đặt tkcalendar (pip install tkcalendar)").pack(pady=20)
    root.mainloop()