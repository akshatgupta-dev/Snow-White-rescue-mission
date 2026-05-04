import tkinter as tk
from src.tkinter_ui import GameApp

app = GameApp()
app.after(1000, lambda: app.event_generate('<Return>'))
app.after(2000, lambda: app._quit_game())
app.mainloop()
