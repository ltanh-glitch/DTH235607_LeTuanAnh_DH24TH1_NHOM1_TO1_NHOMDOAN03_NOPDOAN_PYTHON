-- ================================================
-- DATABASE: quanlybanhang (Database Quản lý Bán hàng)
-- Dự án: Quản lý bán hàng (Python + Tkinter)
-- Tác giả: Lê Tuấn Anh
-- Phiên bản: SQL Server
-- ================================================

-- Xóa database cũ nếu tồn tại
IF EXISTS (SELECT * FROM sys.databases WHERE name = 'QuanLyBanHang')
    DROP DATABASE QuanLyBanHang;
GO

-- ==========================================
-- TẠO DATABASE
-- ==========================================

CREATE DATABASE QuanLyBanHang; -- Lệnh tạo Database
GO
USE QuanLyBanHang; -- Lệnh chọn Database để thực thi các lệnh tiếp theo
GO

-- ==========================================
-- BẢNG: tblChatLieu (Danh mục chất liệu/loại hàng)
-- ==========================================
CREATE TABLE dbo.tblChatLieu (
    MaChatLieu INT IDENTITY(1,1) PRIMARY KEY, -- Khóa chính, tự động tăng (1, 2, 3...)
    TenChatLieu NVARCHAR(100) NOT NULL -- Tên chất liệu (Ví dụ: Vải, Da, Gỗ)
);
GO

-- ==========================================
-- BẢNG: tblHang (Thông tin chi tiết về sản phẩm/hàng hóa)
-- ==========================================
CREATE TABLE dbo.tblHang (
    MaHang INT IDENTITY(1,1) PRIMARY KEY, -- Khóa chính, tự động tăng
    TenHang NVARCHAR(200) NOT NULL, -- Tên mặt hàng
    MaChatLieu INT NULL, -- Khóa ngoại liên kết tới tblChatLieu (NULLable: có thể không rõ chất liệu)
    SoLuong INT NOT NULL DEFAULT 0, -- Số lượng tồn kho (mặc định 0)
    DonGiaNhap DECIMAL(18,2) NULL, -- Giá nhập vào
    DonVi NVARCHAR(50) NULL, -- Đơn vị tính (Cái, Kg...)
    Anh VARBINARY(MAX) NULL, -- Lưu trữ hình ảnh sản phẩm
    GhiChu NVARCHAR(400) NULL, -- Ghi chú thêm
    CONSTRAINT FK_Hang_ChatLieu FOREIGN KEY (MaChatLieu) -- Ràng buộc Khóa ngoại
        REFERENCES dbo.tblChatLieu(MaChatLieu)
        ON UPDATE CASCADE -- Cập nhật MaChatLieu bên tblHang nếu tblChatLieu thay đổi
        ON DELETE SET NULL -- Đặt MaChatLieu về NULL nếu chất liệu bị xóa
);
GO

-- ==========================================
-- BẢNG: tblNhanVien (Thông tin Nhân viên)
-- ==========================================
CREATE TABLE dbo.tblNhanVien (
    MaNhanVien INT IDENTITY(1,1) PRIMARY KEY, -- Khóa chính, tự động tăng
    TenNhanVien NVARCHAR(150) NOT NULL,
    GioiTinh NVARCHAR(10) NULL,
    DiaChi NVARCHAR(300) NULL,
    DienThoai NVARCHAR(50) NULL,
    NgaySinh DATE NULL
);
GO

-- ==========================================
-- BẢNG: tblKhach (Thông tin Khách hàng)
-- ==========================================
CREATE TABLE dbo.tblKhach (
    MaKhach INT IDENTITY(1,1) PRIMARY KEY, -- Khóa chính, tự động tăng
    TenKhach NVARCHAR(200) NOT NULL,
    DiaChi NVARCHAR(300) NULL,
    DienThoai NVARCHAR(50) NULL
);
GO

-- ==========================================
-- BẢNG: tblHDBan (Hóa đơn Bán hàng - Thông tin chung)
-- ==========================================
CREATE TABLE dbo.tblHDBan (
    MaHDBan INT IDENTITY(1,1) PRIMARY KEY, -- Khóa chính, tự động tăng
    MaNhanVien INT NOT NULL, -- Khóa ngoại (Bắt buộc phải có nhân viên lập)
    MaKhach INT NULL, -- Khóa ngoại (Có thể không cần khách hàng cụ thể)
    NgayBan DATE NOT NULL DEFAULT GETDATE(), -- Ngày tạo Hóa đơn (mặc định là ngày hiện tại)
    TongTien DECIMAL(18,2) NOT NULL DEFAULT 0, -- Tổng tiền của Hóa đơn (sẽ được cập nhật sau)
    CONSTRAINT FK_HDBan_NhanVien FOREIGN KEY (MaNhanVien)
        REFERENCES dbo.tblNhanVien(MaNhanVien)
        ON UPDATE CASCADE
        ON DELETE NO ACTION, -- Cấm xóa Nhân viên nếu họ đã từng lập Hóa đơn
    CONSTRAINT FK_HDBan_Khach FOREIGN KEY (MaKhach)
        REFERENCES dbo.tblKhach(MaKhach)
        ON UPDATE CASCADE
        ON DELETE SET NULL -- Đặt MaKhach về NULL nếu khách hàng bị xóa
);
GO

-- ==========================================
-- BẢNG: tblChiTietHDBan (Chi tiết Hàng hóa trong từng Hóa đơn)
-- ==========================================
CREATE TABLE dbo.tblChiTietHDBan (
    MaHDBan INT NOT NULL, -- Khóa ngoại (liên kết với tblHDBan)
    MaHang INT NOT NULL, -- Khóa ngoại (liên kết với tblHang)
    SoLuong INT NOT NULL DEFAULT 1,
    DonGia DECIMAL(18,2) NOT NULL, -- Đơn giá bán tại thời điểm lập chi tiết
    GiamGia DECIMAL(5,2) NULL DEFAULT 0, -- Giảm giá (dưới dạng %)
    -- Cột tính toán tự động: Số lượng * Đơn giá * (1 - Giảm giá/100)
    ThanhTien AS (SoLuong * DonGia * (1 - ISNULL(GiamGia,0)/100.0)) PERSISTED,
    PRIMARY KEY (MaHDBan, MaHang), -- Khóa chính là tổ hợp của Mã HĐ và Mã Hàng
    CONSTRAINT FK_CTHDBan_HDBan FOREIGN KEY (MaHDBan)
        REFERENCES dbo.tblHDBan(MaHDBan)
        ON UPDATE CASCADE
        ON DELETE CASCADE, -- Xóa Chi tiết HĐ khi Hóa đơn chính bị xóa
    CONSTRAINT FK_CTHDBan_Hang FOREIGN KEY (MaHang)
        REFERENCES dbo.tblHang(MaHang)
        ON UPDATE CASCADE
        ON DELETE NO ACTION -- Cấm xóa Hàng hóa nếu còn tồn tại trong Chi tiết HĐ
);
GO

-- ==========================================
-- BẢNG: tblTaiKhoan (Quản lý tài khoản đăng nhập)
-- ==========================================
CREATE TABLE dbo.tblTaiKhoan (
    MaTK INT IDENTITY(1,1) PRIMARY KEY,
    MaNhanVien INT NULL, -- Khóa ngoại liên kết với Nhân viên (Tài khoản thuộc về NV nào?)
    TenDangNhap NVARCHAR(100) NOT NULL UNIQUE, -- Tên đăng nhập (Bắt buộc và không trùng lặp)
    MatKhau NVARCHAR(100) NOT NULL,
    PhanQuyen INT NOT NULL DEFAULT 0, -- Phân quyền (0: Admin, 1: Nhân viên)
    TrangThai BIT NOT NULL DEFAULT 1, -- Trạng thái tài khoản (1: Hoạt động)
    CONSTRAINT FK_TaiKhoan_NhanVien FOREIGN KEY (MaNhanVien)
        REFERENCES dbo.tblNhanVien(MaNhanVien)
        ON UPDATE CASCADE
        ON DELETE SET NULL -- Đặt MaNhanVien về NULL nếu Nhân viên bị xóa (TK vẫn tồn tại)
);
GO

-- ==========================================
-- DỮ LIỆU MẪU (Sample Data)
-- ==========================================

-- Chèn 3 loại Chất liệu
INSERT INTO dbo.tblChatLieu (TenChatLieu) VALUES
(N'Vải cotton'),
(N'Da tổng hợp'),
(N'Lụa tơ tằm'),
(N'Polyester'),
(N'Len cashmere'),
(N'Kim loại nhôm'),
(N'Thủy tinh cường lực'),
(N'Gốm sứ'),
(N'Nhựa ABS'),
(N'Da bò thật'),
(N'Vải Denim'),
(N'Cao su tự nhiên'),
(N'Đá hoa cương'),
(N'Vàng 18K'),
(N'Bạc S925'),
(N'Sợi tổng hợp'),
(N'Tre ép'),
(N'Gỗ tự nhiên');

-- Chèn 3 mặt hàng mẫu
INSERT INTO dbo.tblHang (TenHang, MaChatLieu, SoLuong, DonGiaNhap, DonVi, GhiChu)
VALUES
(N'Áo thun nam', 1, 120, 45000.00, N'Cái', N'Màu trắng'),
(N'Váy lụa cao cấp', 4, 30, 450000.00, N'Cái', N'Màu hồng pastel'),
(N'Áo sơ mi Denim', 12, 80, 180000.00, N'Cái', N'Form rộng'),
(N'Thảm trải sàn', 6, 45, 250000.00, N'Cuộn', N'Kích thước lớn'),
(N'Bình nước thể thao', 7, 200, 35000.00, N'Cái', N'Dung tích 1 lít'),
(N'Ghế Da bò văn phòng', 11, 15, 2500000.00, N'Cái', N'Da thật 100%'),
(N'Đồng hồ đeo tay', 13, 25, 800000.00, N'Chiếc', N'Dây da'),
(N'Nhẫn Bạc đính đá', 15, 60, 150000.00, N'Chiếc', N'Bạc S925'),
(N'Bát ăn cơm', 8, 300, 15000.00, N'Cái', N'Sứ trắng'),
(N'Bàn làm việc gỗ sồi', 18, 5, 3200000.00, N'Cái', N'Gỗ sồi nhập khẩu'),
(N'Khăn len choàng cổ', 5, 50, 220000.00, N'Chiếc', N'Len Cashmere'),
(N'Ống hút inox', 10, 500, 5000.00, N'Cây', N'Bảo vệ môi trường'),
(N'Túi xách nữ thời trang', 9, 75, 180000.00, N'Cái', N'Da tổng hợp cao cấp'),
(N'Dép cao su đi biển', 13, 150, 60000.00, N'Đôi', N'Màu xanh dương'),
(N'Áo khoác dù', 6, 90, 250000.00, N'Cái', N'Chất liệu Polyester'),
(N'Đèn bàn LED', 7, 40, 150000.00, N'Cái', N'Thân nhựa ABS'),
(N'Ví da nữ', 2, 50, 120000.00, N'Cái', N'Da nhân tạo'),
(N'Bàn gỗ nhỏ', 3, 10, 850000.00, N'Cái', N'Kích thước 80x40');

-- Chèn 2 Nhân viên
INSERT INTO dbo.tblNhanVien (TenNhanVien, GioiTinh, DiaChi, DienThoai, NgaySinh)
VALUES
(N'Lê Tuấn Anh', N'Nam', N'An Giang', '0334056255', '2005-01-27'),
(N'Trần Vũ Duy', N'Nam', N'An Giang', '0987654321', '1992-06-20'),
(N'Nguyễn Thị Hồng', N'Nữ', N'Cần Thơ', '0912345678', '1995-11-15'),
(N'Phạm Văn Cường', N'Nam', N'Đà Nẵng', '0901112233', '1988-03-10'),
(N'Hoàng Thị Lan', N'Nữ', N'Hải Phòng', '0934567890', '2001-08-25'),
(N'Trần Minh Khang', N'Nam', N'TP Hồ Chí Minh', '0778899000', '1997-04-05'),
(N'Bùi Thanh Tâm', N'Nữ', N'Đồng Nai', '0383748291', '1990-12-01'),
(N'Võ Đình Hiếu', N'Nam', N'Bình Dương', '0945678901', '1999-07-12'),
(N'Đặng Thu Hà', N'Nữ', N'Thanh Hóa', '0898765432', '1993-01-20'),
(N'Lý Văn Tùng', N'Nam', N'Quảng Ninh', '0707123456', '2000-09-28'),
(N'Mai Ngọc Mai', N'Nữ', N'Huế', '0369876543', '1985-05-03'),
(N'Hồ Đức Thắng', N'Nam', N'Nghệ An', '0966554433', '1996-10-18'),
(N'Dương Mỹ Lệ', N'Nữ', N'Long An', '0888999111', '1994-02-14'),
(N'Phan Thanh Hải', N'Nam', N'Tiền Giang', '0977888000', '1998-11-29'),
(N'Cao Bảo Ngọc', N'Nữ', N'Hà Tĩnh', '0345678901', '2002-06-07'),
(N'Lâm Quốc Cường', N'Nam', N'Khánh Hòa', '0919283746', '1991-03-22'),
(N'Lưu Thị Phương', N'Nữ', N'Quảng Nam', '0796543210', '1989-08-08');

-- Chèn 2 Khách hàng
INSERT INTO dbo.tblKhach (TenKhach, DiaChi, DienThoai)
VALUES
(N'Công ty TNHH An Giang', N'Hà Nội', '024123456'),
(N'Nguyễn Văn Cảnh', N'HCM', '0900111222'),
(N'Nguyễn Văn Thạnh', N'Hà Nội', '0901230000'),
(N'Lê Thị Bình', N'TP Hồ Chí Minh', '0902341111'),
(N'Phạm Văn Chung', N'Đà Nẵng', '0903452222'),
(N'Trần Thị Diễm', N'Cần Thơ', '0904563333'),
(N'Hoàng Văn Thành', N'Hải Phòng', '0905674444'),
(N'Công ty Cổ phần X', N'Bình Dương', '0274111222'),
(N'Tạ Minh Cẩm', N'Đồng Nai', '0906785555'),
(N'Đoàn Thị Giang', N'Bắc Ninh', '0907896666'),
(N'Lê Minh Huy', N'Vũng Tàu', '0908907777'),
(N'Vũ Thị Kim Xuyến', N'Quảng Ngãi', '0909018888'),
(N'Tập đoàn ZYR', N'Long An', '0723456789'),
(N'Nguyễn Quốc Linh', N'Phú Thọ', '0911223344'),
(N'Đinh Thị Mẫn', N'Bắc Giang', '0922334455'),
(N'Phan Văn Nghĩa', N'Thái Nguyên', '0933445566'),
(N'Tổ chức Thương mại', N'Hà Nội', '0249876543');

-- Chèn 2 Hóa đơn Bán hàng
INSERT INTO dbo.tblHDBan (MaNhanVien, MaKhach, NgayBan)
VALUES
(1, 1, '2025-10-01'), -- Hóa đơn 1: NV 1, Khách 1
(2, 2, '2025-10-02'), -- Hóa đơn 2: NV 2, Khách 2
(3, 3, '2025-10-03'), -- NV 3, Khách 3
(4, 4, '2025-10-04'), -- NV 4, Khách 4
(5, 5, '2025-10-05'), -- NV 5, Khách 5
(6, 6, '2025-10-05'), -- NV 6, Khách 6
(7, 7, '2025-10-06'), -- NV 7, Khách 7
(8, 8, '2025-10-07'), -- NV 8, Khách 8
(9, 9, '2025-10-08'), -- NV 9, Khách 9
(10, 10, '2025-10-09'), -- NV 10, Khách 10
(11, 11, '2025-10-10'), -- NV 11, Khách 11
(12, 12, '2025-10-11'), -- NV 12, Khách 12
(13, 13, '2025-10-12'), -- NV 13, Khách 13
(14, 14, '2025-10-12'), -- NV 14, Khách 14
(15, 15, '2025-10-13'), -- NV 15, Khách 15
(16, 16, '2025-10-14'), -- NV 16, Khách 16
(17, 17, '2025-10-15'); -- NV 17, Khách 17

-- Chèn Chi tiết cho Hóa đơn 1 và 2
INSERT INTO dbo.tblChiTietHDBan (MaHDBan, MaHang, SoLuong, DonGia, GiamGia)
VALUES
(1, 1, 2, 90000.00, 0), -- HĐ 1 mua 2 Áo thun
(1, 3, 1, 900000.00, 5), -- HĐ 1 mua 1 Bàn gỗ (giảm 5%)
(2, 2, 1, 150000.00, 0), -- HĐ 2 mua 1 Ví da
(3, 4, 1, 800000.00, 0), -- HĐ 3 mua Váy lụa
(3, 1, 5, 85000.00, 5), -- HĐ 3 mua Áo thun
(4, 9, 2, 3000000.00, 10), -- HĐ 4 mua Bàn làm việc
(5, 7, 3, 180000.00, 0), -- HĐ 5 mua Nhẫn Bạc
(6, 10, 1, 250000.00, 0), -- HĐ 6 mua Khăn len
(7, 13, 50, 65000.00, 15), -- HĐ 7 mua Dép cao su (số lượng lớn)
(8, 2, 2, 150000.00, 0), -- HĐ 8 mua Ví da
(9, 14, 2, 300000.00, 0), -- HĐ 9 mua Áo khoác dù
(10, 5, 1, 200000.00, 0), -- HĐ 10 mua Áo sơ mi Denim
(11, 15, 1, 180000.00, 0), -- HĐ 11 mua Đèn bàn LED
(12, 12, 10, 20000.00, 0), -- HĐ 12 mua Ống hút inox
(13, 6, 1, 280000.00, 5), -- HĐ 13 mua Thảm trải sàn
(14, 8, 20, 18000.00, 0), -- HĐ 14 mua Bát ăn cơm
(15, 11, 1, 3500000.00, 0), -- HĐ 15 mua Ghế Da bò
(17, 3, 1, 950000.00, 0); -- HĐ 17 mua Bàn gỗ nhỏ

-- Chèn DỮ LIỆU TÀI KHOẢN (Liên kết với MaNhanVien)
INSERT INTO dbo.tblTaiKhoan (MaNhanVien, TenDangNhap, MatKhau, PhanQuyen, TrangThai)
VALUES
(1, N'admin', N'admin123', 0, 1), -- TK Admin (PhanQuyen=0) liên kết với NV 1
(2, N'nhanvien', N'nhanvien123', 1, 1); -- TK Nhân viên (PhanQuyen=1) liên kết với NV 2
GO

-- CẬP NHẬT TỔNG TIỀN HÓA ĐƠN
-- Dùng UPDATE JOIN để tính tổng ThanhTien từ ChiTietHDBan và cập nhật vào TongTien của HDBan
UPDATE h
SET TongTien = ct.Total
FROM dbo.tblHDBan h
JOIN (
    SELECT MaHDBan, SUM(ThanhTien) AS Total -- Tính tổng tiền cho từng hóa đơn
    FROM dbo.tblChiTietHDBan
    GROUP BY MaHDBan
) ct ON h.MaHDBan = ct.MaHDBan;
GO

-- KIỂM TRA KẾT QUẢ (Truy vấn để xác nhận dữ liệu đã được chèn thành công)
SELECT * FROM dbo.tblChatLieu;
SELECT * FROM dbo.tblHang;
SELECT * FROM dbo.tblNhanVien;
SELECT * FROM dbo.tblKhach;
SELECT * FROM dbo.tblHDBan; -- Kiểm tra TongTien đã được cập nhật chưa
SELECT * FROM dbo.tblChiTietHDBan; -- Kiểm tra cột ThanhTien đã tính đúng chưa
SELECT * FROM dbo.tblTaiKhoan; -- Kiểm tra liên kết MaNhanVien
GO