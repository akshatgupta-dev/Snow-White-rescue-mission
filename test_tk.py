import tkinter as tk

root = tk.Tk()

def widget_bind(e):
    print("Widget triggered")

def all_bind(e):
    print("All triggered")

btn = tk.Button(root, text="Test")
btn.pack()
btn.focus_set()

btn.bind("<Return>", widget_bind)
root.bind_all("<Return>", all_bind)

# Wait... in tkinter, unbind_all deletes the all tag?
root.unbind_all("<Return>")

# Send event
btn.event_generate("<Return>")
root.update()

