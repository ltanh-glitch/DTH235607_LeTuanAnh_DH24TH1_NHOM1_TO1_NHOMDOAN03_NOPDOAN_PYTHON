import pyodbc

def connect_db():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            'SERVER=LAPTOP-TUANANH;'                
            'DATABASE=QuanLyBanHang;'
            'UID=sa;'
            'PWD=123;'
            'Encrypt=no;'
            'TrustServerCertificate=yes;'
        )
        print("✅ Kết nối SQL Server thành công!")
        return conn
    except Exception as e:
        print("❌ Lỗi kết nối SQL Server:", e)
        return None

if __name__ == "__main__":
    connect_db()
