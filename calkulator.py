import tkinter as tk
from tkinter import messagebox

expression = ""
def click(button):
    global expression
    if button == '=':
        try:
            result = str(eval(expression))
            display.config(text=result)
            expression = result
        except Exception as e:
            messagebox.showerror("Error", e)
            display.config(text="")
            expression = ""
    else:
        expression += button
        display.config(text=expression)
def clear():
    global expression
    expression = ""
    display.config(text="")

root = tk.Tk()
root.title("Kalkulator_zadanie")

display = tk.Label(root, text="", font=('Arial', 18), bd=10, anchor='e', relief='sunken', width=14)
display.grid(row=0, column=0, columnspan=4, sticky="ew")

tk.Button(root, text='7', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('7')).grid(row=1, column=0)
tk.Button(root, text='8', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('8')).grid(row=1, column=1)
tk.Button(root, text='9', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('9')).grid(row=1, column=2)
tk.Button(root, text='/', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('/')).grid(row=1, column=3)
tk.Button(root, text='4', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('4')).grid(row=2, column=0)
tk.Button(root, text='5', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('5')).grid(row=2, column=1)
tk.Button(root, text='6', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('6')).grid(row=2, column=2)
tk.Button(root, text='*', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('*')).grid(row=2, column=3)
tk.Button(root, text='1', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('1')).grid(row=3, column=0)
tk.Button(root, text='2', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('2')).grid(row=3, column=1)
tk.Button(root, text='3', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('3')).grid(row=3, column=2)
tk.Button(root, text='-', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('-')).grid(row=3, column=3)
tk.Button(root, text='.', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('.')).grid(row=4, column=0)
tk.Button(root, text='0', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('0')).grid(row=4, column=1)
tk.Button(root, text='=', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('=')).grid(row=4, column=2)
tk.Button(root, text='+', padx=20, pady=20, font=('Arial', 18), height=1, width=1, command=lambda: click('+')).grid(row=4, column=3)

tk.Button(root, text='C', padx=20, pady=20, font=('Arial', 18), command=clear, height=1).grid(row=5, column=0, columnspan=4,sticky="ew")
root.mainloop()
