import tkinter as tk
from tkinter import ttk, filedialog
from ttkbootstrap.dialogs import Messagebox
import os
import json
import subprocess
import threading

def open_project_creator(app_state, project_type, populate_tree_callback):
    # تنظیم والد برای ارث‌بری آیکون
    win = tk.Toplevel(app_state["window"])
    win.title(f"New {project_type} Project")
    win.geometry("500x500") 
    
    # ------------------ اضافه شده: اعمال آیکون ------------------
    win.transient(app_state["window"])
    try:
        # کپی کردن آیکون از پنجره اصلی
        main_icon = app_state["window"].wm_iconbitmap()
        if main_icon:
            win.iconbitmap(main_icon)
    except Exception:
        pass
    # -----------------------------------------------------------

    win.grab_set()
    win.resizable(True, True)

    # Variables
    name_var = tk.StringVar()
    desc_var = tk.StringVar()
    version_var = tk.StringVar()
    location_var = tk.StringVar(value=app_state.get("project_path", os.path.expanduser("~")))

    # Layout
    frame = ttk.Frame(win, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Project Name:").grid(row=0, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=name_var, width=40).grid(row=0, column=1, pady=5, sticky="we")

    ttk.Label(frame, text="Description:").grid(row=1, column=0, sticky="w", pady=5)
    ttk.Entry(frame, textvariable=desc_var, width=40).grid(row=1, column=1, pady=5, sticky="we")

    ttk.Label(frame, text="Version:").grid(row=2, column=0, sticky="w", pady=5)
    if project_type == "Laravel":
        versions = ["13","12","11", "10", "9", "8", "7", "6","5","4","3","2","1"]
        ver_combo = ttk.Combobox(frame, textvariable=version_var, values=versions, state="readonly")
        ver_combo.current(0)
        ver_combo.grid(row=2, column=1, pady=5, sticky="we")
    else:
        version_var.set("1.0.0")
        ttk.Entry(frame, textvariable=version_var).grid(row=2, column=1, pady=5, sticky="we")

    ttk.Label(frame, text="Location:").grid(row=3, column=0, sticky="w", pady=5)
    loc_frame = ttk.Frame(frame)
    loc_frame.grid(row=3, column=1, sticky="we", pady=5)
    ttk.Entry(loc_frame, textvariable=location_var).pack(side="left", fill="x", expand=True, padx=(0, 5))
    
    def browse_loc():
        # اضافه کردن parent=win
        d = filedialog.askdirectory(initialdir=location_var.get(), parent=win)
        if d: location_var.set(d)
    ttk.Button(loc_frame, text="Browse...", command=browse_loc).pack(side="right")

    status_var = tk.StringVar(value="Ready")
    ttk.Label(frame, textvariable=status_var, foreground="blue").grid(row=4, column=0, columnspan=2, sticky="w", pady=(15, 5))

    # Log Console (for displaying Composer output)
    log_frame = ttk.Frame(frame)
    log_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=5)
    frame.rowconfigure(5, weight=1)
    frame.columnconfigure(1, weight=1)

    log_text = tk.Text(log_frame, height=10, bg="#1e1e1e", fg="#d4d4d4", state="disabled", font=("Consolas", 9))
    log_scroll = ttk.Scrollbar(log_frame, command=log_text.yview)
    log_text.configure(yscrollcommand=log_scroll.set)
    log_text.pack(side="left", fill="both", expand=True)
    log_scroll.pack(side="right", fill="y")

    def append_log(message):
        log_text.config(state="normal")
        log_text.insert("end", message + "\n")
        log_text.see("end")
        log_text.config(state="disabled")

    # Actions
    def create_lc_file(path, name, desc, ver, p_type):
        data = {"name": name, "description": desc, "version": ver, "type": p_type}
        with open(os.path.join(path, f"{name}.lc"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def on_success(target_dir):
        app_state["project_path"] = target_dir
        try:
            populate_tree_callback(target_dir)
        except TypeError:
            try:
                populate_tree_callback(app_state)
            except TypeError:
                tree = app_state.get("tree")
                if tree:
                    tree.delete(*tree.get_children())
                    populate_tree_callback(tree, "", target_dir)
                    
        Messagebox.show_info(f"{project_type} project created successfully!", "Success", parent=win)
        win.destroy()


    def process_creation():
        name = name_var.get().strip()
        loc = location_var.get().strip()
        
        if not name or not loc:
            Messagebox.show_error("Name and Location are required.", "Error", parent=win)
            return

        target_dir = os.path.join(loc, name)
        
        if os.path.exists(target_dir) and os.listdir(target_dir):
            Messagebox.show_error(f"Directory '{name}' already exists and is not empty.", "Error", parent=win)
            return
        
        if project_type == "PHP":
            try:
                os.makedirs(target_dir, exist_ok=True)
                with open(os.path.join(target_dir, "index.php"), "w", encoding="utf-8") as f:
                    f.write("<?php\n\n// Basic PHP Project\necho 'Hello World!';\n")
                create_lc_file(target_dir, name, desc_var.get(), version_var.get(), "php")
                append_log("PHP Project created successfully.")
                on_success(target_dir)
            except Exception as e:
                Messagebox.show_error(str(e), "Error", parent=win)
        
        elif project_type == "Laravel":
            btn_create.config(state="disabled")
            status_var.set("Running Composer... Please wait.")
            log_text.config(state="normal")
            log_text.delete(1.0, "end")
            log_text.config(state="disabled")
            
            def run_composer():
                ver = version_var.get()
                composer_cmd = f'composer create-project laravel/laravel "{name}" "{ver}.*"'
                
                win.after(0, lambda: append_log(f"> {composer_cmd}"))
                
                try:
                    process = subprocess.Popen(
                        composer_cmd, cwd=loc, shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    for line in process.stdout:
                        win.after(0, append_log, line.strip())
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        create_lc_file(target_dir, name, desc_var.get(), ver, "laravel")
                        win.after(0, lambda: status_var.set("Finished!"))
                        win.after(0, lambda: on_success(target_dir))
                    else:
                        win.after(0, lambda: status_var.set("Composer Error! Check logs."))
                        win.after(0, lambda: btn_create.config(state="normal"))
                        
                except Exception as e:
                    win.after(0, lambda: append_log(f"System Error: {str(e)}"))
                    win.after(0, lambda: status_var.set("Execution Failed."))
                    win.after(0, lambda: btn_create.config(state="normal"))

            threading.Thread(target=run_composer, daemon=True).start()

    btn_frame = ttk.Frame(frame)
    btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
    btn_create = ttk.Button(btn_frame, text="Create Project", command=process_creation)
    btn_create.pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side="left", padx=5)
