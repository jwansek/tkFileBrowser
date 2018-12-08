import tkinter as tk
from tkinter import ttk
import os

def on_close():
    if os.path.exists(os.path.join("E:", "temp")):
        os.rmdir(os.path.join("E:", "temp"))
    if os.path.exists(os.path.join(os.path.expanduser("~"), "temp")):
        os.rmdir(os.path.join(os.path.expanduser("~"), "temp"))

    root.destroy()

root = tk.Tk()
root.title("File tester program")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_close)

tk.Label(root, text = "File tester program", font = ("Verdana", 16, "bold")).grid(row = 0, column = 0, columnspan = 2, padx = 3, pady = 3)

ttk.Button(root, text = "Add in user", command = lambda: os.mkdir(os.path.join(os.path.expanduser("~"), "temp"))).grid(row = 1, column = 0, padx = 3, pady = 3, ipady = 3, ipadx = 3)
ttk.Button(root, text = "Delete in user", command = lambda: os.rmdir(os.path.join(os.path.expanduser("~"), "temp"))).grid(row = 1, column = 1, padx = 3, pady = 3, ipady = 3, ipadx = 3)
ttk.Button(root, text = "Add in E:\\", command = lambda: os.mkdir(os.path.join("E:", "temp"))).grid(row = 2, column = 0, padx = 3, pady = 3, ipady = 3, ipadx = 3)
ttk.Button(root, text = "Delete in E:\\", command = lambda: os.rmdir(os.path.join("E:", "temp"))).grid(row = 2, column = 1, padx = 3, pady = 3, ipady = 3, ipadx = 3)

root.mainloop()