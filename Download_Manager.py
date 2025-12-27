import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import requests
import os

class DownloadManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Download Manager")
        self.root.geometry("600x320")
        self.root.resizable(False, False)

        self.url = tk.StringVar()
        self.save_dir = ""
        self.file_path = ""
        self.total_size = 0
        self.downloaded = 0

        self.pause_event = threading.Event()
        self.pause_event.set()
        self.downloading = False

        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="File URL:").pack(pady=5)

        # Frame برای Entry + Button
        url_frame = tk.Frame(self.root)
        url_frame.pack(pady=5)

        # Entry
        self.url_entry = tk.Entry(url_frame, textvariable=self.url, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5)

        # دکمه Paste
        tk.Button(url_frame, text="Paste Link", command=self.paste_link).pack(side=tk.LEFT)

        # فعال کردن Ctrl+V
        self.url_entry.bind("<Control-v>", lambda e: self.url_entry.event_generate('<<Paste>>'))
        self.url_entry.bind("<Control-V>", lambda e: self.url_entry.event_generate('<<Paste>>'))

        # راست کلیک برای Paste
        self.url_entry.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Paste", command=self.paste_link)

        tk.Button(self.root, text="Choose Save Folder", command=self.choose_folder).pack(pady=5)
        self.path_label = tk.Label(self.root, text="No folder selected")
        self.path_label.pack()

        self.progress = ttk.Progressbar(self.root, length=550)
        self.progress.pack(pady=10)

        self.percent_label = tk.Label(self.root, text="0%")
        self.percent_label.pack()

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Start", width=10, command=self.start).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Pause", width=10, command=self.pause).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Resume", width=10, command=self.resume).grid(row=0, column=2, padx=5)

    # راست کلیک منو
    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    # Paste Link
    def paste_link(self):
        try:
            clipboard = self.root.clipboard_get()
            self.url.set(clipboard)
        except tk.TclError:
            pass

    def choose_folder(self):
        self.save_dir = filedialog.askdirectory()
        if self.save_dir:
            self.path_label.config(text=self.save_dir)

    def start(self):
        if self.downloading:
            return

        if not self.url.get():
            messagebox.showerror("Error", "Enter download URL")
            return

        if not self.save_dir:
            messagebox.showerror("Error", "Choose save folder")
            return

        self.downloading = True
        threading.Thread(target=self.download, daemon=True).start()

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def download(self):
        try:
            filename = self.url.get().split("/")[-1]
            self.file_path = os.path.join(self.save_dir, filename)

            headers = {}
            if os.path.exists(self.file_path):
                self.downloaded = os.path.getsize(self.file_path)
                headers["Range"] = f"bytes={self.downloaded}-"

            response = requests.get(self.url.get(), stream=True, headers=headers)
            self.total_size = int(response.headers.get("Content-Length", 0)) + self.downloaded

            self.progress["maximum"] = self.total_size

            with open(self.file_path, "ab") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    self.pause_event.wait()
                    if chunk:
                        file.write(chunk)
                        self.downloaded += len(chunk)
                        self.progress["value"] = self.downloaded
                        percent = int((self.downloaded / self.total_size) * 100)
                        self.percent_label.config(text=f"{percent}%")

            messagebox.showinfo("Done", "Download completed")
            self.downloading = False

        except Exception as e:
            self.downloading = False
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    DownloadManager(root)
    root.mainloop()
