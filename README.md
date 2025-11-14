# 🏪 ỨNG DỤNG QUẢN LÝ BÁN HÀNG

## 📋 Mục lục
- [Giới thiệu](#-giới-thiệu)
- [Tính năng chính](#-tính-năng-chính)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
- [Phân quyền người dùng](#-phân-quyền-người-dùng)
- [Cơ sở dữ liệu](#-cơ-sở-dữ-liệu)
- [Screenshots](#-screenshots)
- [Tác giả](#-tác-giả)

## 📖 Giới thiệu

**Ứng dụng Quản lý Bán hàng** là một phần mềm desktop được phát triển bằng Python với giao diện đồ họa Tkinter, kết nối với cơ sở dữ liệu SQL Server. Ứng dụng được thiết kế để hỗ trợ các cửa hàng bán lẻ trong việc quản lý hoạt động kinh doanh hàng ngày một cách hiệu quả và chuyên nghiệp.

### 🎯 Mục tiêu dự án
- Số hóa quy trình quản lý bán hàng
- Tối ưu hóa việc theo dõi hàng tồn kho
- Quản lý thông tin khách hàng và nhân viên
- Tạo báo cáo doanh thu chi tiết
- Phân quyền người dùng rõ ràng (Admin, Quản lý, Nhân viên)

## ✨ Tính năng chính

### 📊 Bảng điều khiển (Dashboard)
- Hiển thị thống kê tổng quan theo thời gian thực
- Tổng doanh thu, số đơn hàng, sản phẩm, khách hàng
- Top sản phẩm bán chạy nhất
- Thông tin phiên làm việc của người dùng
- Giao diện KPI Cards trực quan

### 🛒 Quản lý Hàng hóa
- Thêm, sửa, xóa sản phẩm
- Tìm kiếm và lọc sản phẩm theo nhiều tiêu chí
- Quản lý chất liệu/danh mục sản phẩm
- Cập nhật số lượng tồn kho
- Upload và hiển thị hình ảnh sản phẩm
- Export dữ liệu ra Excel

### 👤 Quản lý Khách hàng
- Lưu trữ thông tin khách hàng đầy đủ
- Tìm kiếm khách hàng nhanh chóng
- Theo dõi lịch sử giao dịch
- Export danh sách khách hàng

### 👨‍💼 Quản lý Nhân viên
- Quản lý thông tin nhân viên
- Phân quyền truy cập hệ thống
- Theo dõi hiệu suất làm việc
- Chỉ Admin mới có quyền truy cập

### 💰 Lập Hóa đơn Bán hàng
- Tạo hóa đơn bán hàng nhanh chóng
- Tự động tính toán thành tiền
- Giảm giá linh hoạt (theo %, theo số tiền)
- Cập nhật tồn kho tự động
- In hóa đơn hoặc export PDF

### 📜 Báo cáo Doanh thu
- Báo cáo chi tiết theo khoảng thời gian
- Thống kê theo sản phẩm, khách hàng, nhân viên
- Biểu đồ trực quan
- Export báo cáo ra Excel/PDF

### ⚙️ Quản lý Tài khoản
- Tạo, sửa, xóa tài khoản người dùng
- Đặt lại mật khẩu
- Phân quyền truy cập
- Chỉ Admin có quyền quản lý

## 🔧 Công nghệ sử dụng

| Công nghệ | Mục đích |
|-----------|----------|
| **Python 3.8+** | Ngôn ngữ lập trình chính |
| **Tkinter** | Xây dựng giao diện đồ họa (GUI) |
| **pyodbc** | Kết nối và tương tác với SQL Server |
| **SQL Server** | Hệ quản trị cơ sở dữ liệu |
| **Pillow (PIL)** | Xử lý hình ảnh sản phẩm |
| **openpyxl/xlsxwriter** | Export dữ liệu ra Excel |
| **reportlab** | Tạo file PDF |

## 💻 Yêu cầu hệ thống

### Phần mềm cần thiết
- **Python**: Phiên bản 3.8 trở lên
- **SQL Server**: Express 2017 trở lên (hoặc bất kỳ phiên bản nào)
- **SQL Server Management Studio (SSMS)**: Để quản lý database
- **ODBC Driver for SQL Server**: Driver 17 hoặc 18

### Thư viện Python
```
pyodbc>=4.0.0
Pillow>=9.0.0
openpyxl>=3.0.0
reportlab>=3.6.0
```

## 📥 Cài đặt

### Bước 1: Clone hoặc Download dự án
```bash
git clone https://github.com/ltanh-glitch/DTH235607_LeTuanAnh_DH24TH1_NHOM1_TO1_NHOMDOAN03_NOPDOAN_PYTHON.git
cd DoAn_QuanLyBanHang
```

### Bước 2: Cài đặt thư viện Python
```bash
pip install pyodbc Pillow openpyxl reportlab
```

### Bước 3: Cấu hình SQL Server

1. Mở **SQL Server Management Studio (SSMS)**
2. Chạy file script: `Database/sales management.sql`
3. Database `QuanLyBanHang` sẽ được tạo tự động với dữ liệu mẫu

### Bước 4: Cấu hình kết nối Database

Mở file `src/connect_db.py` và cập nhật thông tin kết nối:

```python
def get_connection():
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=LAPTOP-TUANANH;"  # Thay đổi tên server
        "DATABASE=QuanLyBanHang;"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)
```

**Lưu ý**: Thay `YOUR_SERVER_NAME` bằng tên SQL Server của bạn (ví dụ: `localhost` hoặc `.\SQLEXPRESS`)

### Bước 5: Chạy ứng dụng
```bash
cd src
python main_form.py
```

## 📁 Cấu trúc dự án

```
DoAn_QuanLyBanHang/
│
├── Database/
│   └── sales management.sql          # Script tạo database và dữ liệu mẫu
│
├── src/
│   ├── main_form.py                  # Form chính với sidebar và dashboard
│   ├── login_form.py                 # Form đăng nhập
│   ├── splash_form.py                # Màn hình chào mừng
│   ├── auth.py                       # Xử lý xác thực và phân quyền
│   ├── connect_db.py                 # Kết nối cơ sở dữ liệu
│   ├── product_management_form.py    # Quản lý hàng hóa
│   ├── customer_management_form.py   # Quản lý khách hàng
│   ├── employee_management_form.py   # Quản lý nhân viên
│   ├── account_management_form.py    # Quản lý tài khoản
│   ├── sales_invoice_form.py         # Lập hóa đơn bán hàng
│   └── revenue_report_form.py        # Báo cáo doanh thu
│
├── BaoCao_Word/                      # Tài liệu báo cáo đồ án
│
└── README.md                         # File này
```

## 📖 Hướng dẫn sử dụng

### Đăng nhập lần đầu

Sau khi chạy ứng dụng, sử dụng một trong các tài khoản mẫu:

| Tài khoản | Mật khẩu | Quyền hạn |
|-----------|----------|-----------|
| `admin` | `admin123` | ADMIN (Full quyền) |
| `quanly` | `quanly123` | QUẢN LÝ |
| `nhanvien1` | `nhanvien123` | NHÂN VIÊN |

### Quy trình làm việc cơ bản

1. **Đăng nhập** với tài khoản phù hợp
2. **Quản lý Hàng hóa**: Nhập thông tin sản phẩm vào kho
3. **Quản lý Khách hàng**: Thêm thông tin khách hàng mới
4. **Lập Hóa đơn**: Tạo hóa đơn bán hàng cho khách
5. **Báo cáo**: Xem báo cáo doanh thu theo nhu cầu

## 🔐 Phân quyền người dùng

### ADMIN (PhanQuyen = 0)
- ✅ Toàn quyền truy cập tất cả chức năng
- ✅ Quản lý nhân viên
- ✅ Quản lý tài khoản
- ✅ Xem tất cả báo cáo tài chính

### QUẢN LÝ (PhanQuyen = 1)
- ✅ Quản lý hàng hóa
- ✅ Quản lý khách hàng
- ✅ Lập hóa đơn bán hàng
- ✅ Xem báo cáo doanh thu
- ❌ Không quản lý nhân viên và tài khoản

### NHÂN VIÊN (PhanQuyen = 2)
- ✅ Xem thông tin hàng hóa (chỉ đọc)
- ✅ Quản lý khách hàng
- ✅ Lập hóa đơn bán hàng
- ❌ Không xem báo cáo tài chính
- ❌ Không quản lý nhân viên và tài khoản

## 🗄️ Cơ sở dữ liệu

### Sơ đồ quan hệ chính

```
tblChatLieu (Chất liệu)
    ↓
tblHang (Sản phẩm)
    ↓
tblChiTietHDBan (Chi tiết hóa đơn)
    ↑
tblHDBan (Hóa đơn) ← tblKhach (Khách hàng)
    ↑
tblNhanVien (Nhân viên) → tblTaiKhoan (Tài khoản)
```

### Các bảng chính

| Bảng | Mô tả |
|------|-------|
| `tblChatLieu` | Danh mục chất liệu/loại hàng |
| `tblHang` | Thông tin sản phẩm/hàng hóa |
| `tblKhach` | Thông tin khách hàng |
| `tblNhanVien` | Thông tin nhân viên |
| `tblTaiKhoan` | Tài khoản đăng nhập |
| `tblHDBan` | Hóa đơn bán hàng |
| `tblChiTietHDBan` | Chi tiết các sản phẩm trong hóa đơn |


## 🚀 Tính năng nâng cao (Đang phát triển)

- [ ] Quản lý nhập hàng từ nhà cung cấp
- [ ] Tích hợp quét mã vạch
- [ ] Gửi SMS/Email thông báo cho khách hàng
- [ ] Dashboard với biểu đồ động (Chart.js hoặc Matplotlib)
- [ ] Sao lưu và khôi phục dữ liệu tự động
- [ ] Chế độ Dark Mode
- [ ] Multi-language support

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:

1. Fork dự án
2. Tạo branch mới (`git checkout -b feature/TinhNangMoi`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng mới'`)
4. Push lên branch (`git push origin feature/TinhNangMoi`)
5. Tạo Pull Request


## 👨‍💻 Tác giả

**Lê Tuấn Anh**
- MSSV: DTH235607
- Lớp: DH24TH1
- Nhóm: NHOM1_TO1_NHOMDOAN03
- Email: [anh_dth235607@student.agu.edu.vn]
- GitHub: [@ltanh-glitch](https://github.com/ltanh-glitch)

**Trần Vũ Duy**
- MSSV: DTH235633
- Lớp: DH24TH1
- Nhóm: NHOM1_TO1_NHOMDOAN03
- Email: [duy_dth235633@student.agu.edu.vn]

---

## 🙏 Lời cảm ơn

- Cảm ơn Thầy và các bạn đã ghé thăm

---

**⭐ Nếu bạn thấy dự án hữu ích, hãy cho một Star nhé!**

📅 **Cập nhật lần cuối**: Tháng 11, 2025
