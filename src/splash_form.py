# -*- coding: utf-8 -*-
# splash_form.py - Màn hình chào (Splash Screen)
import tkinter as tk
from tkinter import ttk

def center_window(win, width, height):
    """Căn giữa cửa sổ trên màn hình"""
    win.update_idletasks()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

class SplashScreen:
    def __init__(self, root, on_done=None):
        self.root = root
        self.on_done = on_done

        self.root.title("Đang khởi động...")
        center_window(self.root, 480, 300)
        self.root.configure(bg="#f5f5f5")
        self.root.overrideredirect(True)  # Ẩn thanh tiêu đề

        frame = tk.Frame(self.root, bg="#f5f5f5")
        frame.pack(expand=True, fill="both")

        tk.Label(frame, text="🛒 PHẦN MỀM QUẢN LÝ BÁN HÀNG",
                 font=("Arial", 16, "bold"), bg="#f5f5f5", fg="#1976D2").pack(pady=(80, 10))

        self.progress = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=350)
        self.progress.pack(pady=20)

        self.label_status = tk.Label(frame, text="Đang tải dữ liệu...",
                                     bg="#f5f5f5", fg="#555", font=("Arial", 10))
        self.label_status.pack()

        self.progress_value = 0
        self.update_progress()

    def update_progress(self):
        if self.progress_value < 100:
            self.progress_value += 2
            self.progress["value"] = self.progress_value
            self.label_status.config(text=f"Đang khởi động... {self.progress_value}%")
            self.root.after(60, self.update_progress)
        else:
            self.finish()

    def finish(self):
        self.root.destroy()
        if self.on_done:
            self.on_done()

# ==== Test độc lập ====
if __name__ == "__main__":
    def open_login():
        print("✅ Splash kết thúc — mở LoginForm...")

    root = tk.Tk()
    app = SplashScreen(root, on_done=open_login)
    root.mainloop()