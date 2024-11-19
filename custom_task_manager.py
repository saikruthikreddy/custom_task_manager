import tkinter as tk
from tkinter import ttk
import psutil
import win32gui
import win32process
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from threading import Thread
import time

# Global variable to track the theme
is_dark_theme = False

# Function to toggle between dark and light themes
def toggle_theme():
    global is_dark_theme
    is_dark_theme = not is_dark_theme
    apply_theme()

def apply_theme():
    if is_dark_theme:
        root.tk_setPalette(background='#2e2e2e', foreground='#ffffff')
        tree.config(bg='#444444', fg='#ffffff')
        app_tree.config(bg='#444444', fg='#ffffff')
        process_frame.config(bg='#444444')
        app_frame.config(bg='#444444')
        graph_frame.config(bg='#444444')
        alert_label.config(bg='#444444', fg='#ffffff')
        canvas_graph.get_tk_widget().config(bg='#2e2e2e')
    else:
        root.tk_setPalette(background='#ffffff', foreground='#000000')
        tree.config(bg='#ffffff', fg='#000000')
        app_tree.config(bg='#ffffff', fg='#000000')
        process_frame.config(bg='#ffffff')
        app_frame.config(bg='#ffffff')
        graph_frame.config(bg='#ffffff')
        alert_label.config(bg='#ffffff', fg='#000000')
        canvas_graph.get_tk_widget().config(bg='#ffffff')

# Function to display non-blocking alert notifications
def show_alert(message):
    alert_label.config(text=message, fg='red')

# Function to clear the alert message
def clear_alert():
    alert_label.config(text='')

# Function to populate the process list
def update_process_list():
    while True:
        for row in tree.get_children():
            tree.delete(row)
        
        # Get and update process info
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                cpu = proc.info['cpu_percent']
                memory = round(proc.info['memory_info'].rss / (1024 * 1024), 2)  # Convert bytes to MB
                tree.insert('', 'end', values=(pid, name, cpu, memory))
                
                # Trigger alerts if CPU or memory usage exceeds thresholds
                if cpu > 80:
                    show_alert(f"High CPU usage: {name} (PID: {pid}) is using {cpu}% CPU.")
                if memory > 200:  # Threshold for memory in MB
                    show_alert(f"High memory usage: {name} (PID: {pid}) is using {memory} MB.")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        time.sleep(1)  # Update every second

# Function to get a list of applications with windows
def get_running_applications():
    applications = []

    def enum_windows_proc(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            app_name = win32gui.GetWindowText(hwnd)
            applications.append((pid, app_name))
        return True

    win32gui.EnumWindows(enum_windows_proc, None)
    return applications

# Function to update the applications list
def update_applications_list():
    while True:
        for row in app_tree.get_children():
            app_tree.delete(row)

        # Get and update running apps
        apps = get_running_applications()
        for pid, app_name in apps:
            app_tree.insert('', 'end', values=(pid, app_name))

        time.sleep(1)  # Update every second

# Function to update CPU and memory usage graphs
def update_graphs():
    while True:
        # Add new data points
        cpu_usage.append(psutil.cpu_percent(interval=0.5))
        memory_usage.append(psutil.virtual_memory().percent)
        
        if len(cpu_usage) > 50:  # Keep graph data to the last 50 points
            cpu_usage.pop(0)
            memory_usage.pop(0)
        
        # Update CPU usage graph
        ax_cpu.clear()
        ax_cpu.plot(cpu_usage, color="blue")
        ax_cpu.set_title("CPU Usage (%)")
        ax_cpu.set_ylim(0, 100)

        # Update memory usage graph
        ax_memory.clear()
        ax_memory.plot(memory_usage, color="green")
        ax_memory.set_title("Memory Usage (%)")
        ax_memory.set_ylim(0, 100)

        # Refresh canvas
        canvas.draw()
        time.sleep(1)  # Update graphs every second

# Create the main application window
root = tk.Tk()
root.title("Custom Task Manager with Applications")
root.geometry("1000x700")

# Frame for scrollable content
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(main_frame)
scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Bind mouse wheel to scroll canvas
def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mouse_wheel)

# Treeview for displaying processes
process_frame = tk.LabelFrame(scrollable_frame, text="Processes")
process_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
columns = ("PID", "Name", "CPU (%)", "Memory (MB)")
tree = ttk.Treeview(process_frame, columns=columns, show="headings")
tree.heading("PID", text="PID")
tree.heading("Name", text="Name")
tree.heading("CPU (%)", text="CPU (%)")
tree.heading("Memory (MB)", text="Memory (MB)")
tree.column("PID", width=100)
tree.column("Name", width=200)
tree.column("CPU (%)", width=100)
tree.column("Memory (MB)", width=150)
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Treeview for displaying running applications
app_frame = tk.LabelFrame(scrollable_frame, text="Running Applications")
app_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
app_columns = ("PID", "Application Name")
app_tree = ttk.Treeview(app_frame, columns=app_columns, show="headings")
app_tree.heading("PID", text="PID")
app_tree.heading("Application Name", text="Application Name")
app_tree.column("PID", width=100)
app_tree.column("Application Name", width=400)
app_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Matplotlib Figure for Graphs
graph_frame = tk.LabelFrame(scrollable_frame, text="CPU and Memory Usage")
graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

fig, (ax_cpu, ax_memory) = plt.subplots(2, 1, figsize=(8, 4), dpi=100)
fig.tight_layout(pad=3.0)

cpu_usage = []
memory_usage = []

# Embed the Matplotlib figure in Tkinter
canvas_graph = FigureCanvasTkAgg(fig, master=graph_frame)
canvas_widget = canvas_graph.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)

# Add Theme Toggle Button
theme_button = tk.Button(root, text="Toggle Theme", command=toggle_theme)
theme_button.pack(padx=10, pady=10)

# Alert label at the top of the window
alert_label = tk.Label(root, text='', fg='red', font=('Arial', 12), anchor='w', padx=10)
alert_label.pack(fill=tk.X, side=tk.TOP)

# Clear Alert Button
clear_button = tk.Button(root, text="Clear Alert", command=clear_alert)
clear_button.pack(padx=10, pady=10)

# Load initial lists and start threads
process_thread = Thread(target=update_process_list, daemon=True)
process_thread.start()

app_thread = Thread(target=update_applications_list, daemon=True)
app_thread.start()

graph_thread = Thread(target=update_graphs, daemon=True)
graph_thread.start()

# Run the application
root.mainloop()
