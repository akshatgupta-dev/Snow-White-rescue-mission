import tkinter as tk

root = tk.Tk()
try:
    cursor_str = "@/home/akshatgg/applied_programming/second_course/the-adventures-of-cinderella/src/assets/cinderella_cursor.xbm /home/akshatgg/applied_programming/second_course/the-adventures-of-cinderella/src/assets/cinderella_cursor_mask.xbm white black"
    root.configure(cursor=cursor_str)
    print("Success")
except Exception as e:
    print(f"Failed: {e}")
