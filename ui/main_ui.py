import os
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from typing import Dict, Any

# Import UI components and core application state
from ui.project_creator import open_project_creator
from ui.explorer import load_lc_project, populate_tree
from core.state import app_state, load_settings
from ui.explorer import (
    toggle_explorer, open_project_folder, reload_explorer, on_tree_open, 
    on_tree_double_click, show_tree_context_menu, explorer_new_file, 
    explorer_new_folder, explorer_delete, explorer_close_project
)

from ui.terminal import (
    toggle_terminal, show_output_console, hide_output_console,
    run_php_terminal, run_php_server, run_laravel_server, stop_laravel_server
)

from ui.editor import (
    create_new_tab, open_file, save_file, save_as_file, close_tab, 
    find_text, select_all, undo_action, redo_action, zoom_in, zoom_out, 
    open_settings, show_shortcuts, show_about, exit_app, update_recent_menu, 
    rename_tab_action, show_tab_context_menu, on_tab_changed
)


def create_standard_menubar(window):
    """Constructs and configures the main application menu bar."""
    menubar = tk.Menu(window)
    menu_opts: Dict[str, Any] = {"tearoff": False}

    # File Menu Configuration
    file_menu = tk.Menu(menubar, **menu_opts)
    file_menu.add_command(label="📝 New File", command=create_new_tab, accelerator="Ctrl+N")
    
    new_project_menu = tk.Menu(file_menu, **menu_opts)
    new_project_menu.add_command(label="🐘 PHP", command=lambda: open_project_creator(app_state, "PHP", populate_tree))
    new_project_menu.add_command(label="🚀 Laravel", command=lambda: open_project_creator(app_state, "Laravel", populate_tree))
    file_menu.add_cascade(label="💼 New Project", menu=new_project_menu)
    file_menu.add_command(label="📥 Load Project (.lc)",command=lambda: load_lc_project(app_state, populate_tree))
    
    file_menu.add_separator()
    file_menu.add_command(label="📝 Open File...", command=open_file, accelerator="Ctrl+O")
    file_menu.add_command(label="📂 Open Project...", command=open_project_folder, accelerator="Ctrl+Shift+O")
    file_menu.add_command(label="🚫 Close Project", command=explorer_close_project)
    
    # Recent Files Menu
    app_state["recent_menu"] = tk.Menu(file_menu, **menu_opts)
    file_menu.add_cascade(label="🕒 Open Recent", menu=app_state["recent_menu"])
    update_recent_menu()
    
    file_menu.add_separator()
    file_menu.add_command(label="💾 Save", command=save_file, accelerator="Ctrl+S")
    file_menu.add_command(label="📥 Save As...", command=save_as_file, accelerator="Ctrl+Shift+S")
    file_menu.add_separator()
    file_menu.add_command(label="🚪 Exit", command=exit_app, accelerator="Ctrl+Q")
    menubar.add_cascade(label="File", menu=file_menu)

    # Edit Menu Configuration
    edit_menu = tk.Menu(menubar, **menu_opts)
    edit_menu.add_command(label="↩️ Undo", command=undo_action, accelerator="Ctrl+Z")
    edit_menu.add_command(label="↪️ Redo", command=redo_action, accelerator="Ctrl+Y")
    edit_menu.add_separator()

    def safe_event_generate(event_str):
        """Safely dispatches virtual events to the focused widget."""
        focused = window.focus_get()
        if focused:
            try: focused.event_generate(event_str)
            except tk.TclError: pass

    edit_menu.add_command(label="✂️ Cut", command=lambda: safe_event_generate("<<Cut>>"), accelerator="Ctrl+X")
    edit_menu.add_command(label="📋 Copy", command=lambda: safe_event_generate("<<Copy>>"), accelerator="Ctrl+C")
    edit_menu.add_command(label="📌 Paste", command=lambda: safe_event_generate("<<Paste>>"), accelerator="Ctrl+V")
    edit_menu.add_separator()
    edit_menu.add_command(label="🔠 Select All", command=select_all, accelerator="Ctrl+A")
    edit_menu.add_command(label="🔍 Find & Replace...", command=find_text, accelerator="Ctrl+F")
    menubar.add_cascade(label="Edit", menu=edit_menu)

    # View Menu Configuration
    view_menu = tk.Menu(menubar, **menu_opts)
    view_menu.add_command(label="⌨️ Terminal", command=toggle_terminal, accelerator="Ctrl+J")
    view_menu.add_command(label="📁 File Explorer", command=toggle_explorer, accelerator="Ctrl+E")
    view_menu.add_separator()
    view_menu.add_command(label="➕ Zoom In", command=zoom_in, accelerator="Ctrl++")
    view_menu.add_command(label="➖ Zoom Out", command=zoom_out, accelerator="Ctrl+-")
    menubar.add_cascade(label="View", menu=view_menu)

    # Run Menu Configuration
    run_menu = tk.Menu(menubar, **menu_opts)
    run_menu.add_command(label="✅ Run File in Terminal", command=run_php_terminal, accelerator="Ctrl+R")
    run_menu.add_command(label="⌨️ Open Local Terminal", command=lambda: [show_output_console(), app_state["terminal_input"].focus()], accelerator="Ctrl+Shift+T")
    run_menu.add_separator()
    run_menu.add_command(label="🐘 Run Local PHP Server", command=run_php_server, accelerator="Ctrl+B")
    run_menu.add_separator()
    run_menu.add_command(label="✅ Run Laravel Server", command=run_laravel_server, accelerator="Ctrl+L")
    run_menu.add_command(label="🛑 Stop Laravel Server", command=stop_laravel_server, accelerator="Ctrl+Shift+L")
    menubar.add_cascade(label="Run", menu=run_menu)

    # Settings & Help Menus
    settings_menu = tk.Menu(menubar, **menu_opts)
    settings_menu.add_command(label="⚙️ Preferences", command=open_settings, accelerator="Ctrl+,")
    settings_menu.add_command(label="⌨️ Keyboard Shortcuts", command=show_shortcuts)
    menubar.add_cascade(label="Settings", menu=settings_menu)

    help_menu = tk.Menu(menubar, **menu_opts)
    help_menu.add_command(label="ℹ️ About", command=show_about, accelerator="F1")
    menubar.add_cascade(label="Help", menu=help_menu)

    window.config(menu=menubar)


def setup_app():
    """Initializes the application window, layout, and global event bindings."""
    load_settings()
    window = ttk.Window(themename=app_state["theme_mode"])
    window.withdraw()
    window.title("Laracode")
    window.geometry("1360x720")
    app_state["window"] = window
    
    # Icon Configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.abspath(os.path.join(base_dir, "..", "config", "laracode.png"))
    
    if os.path.exists(icon_path):
        try:
            icon_img = tk.PhotoImage(file=icon_path)
            # Applied to main window only (False) to bypass Windows PNG icon bug
            window.iconphoto(False, icon_img) 
            # Keep reference to prevent garbage collection and use in Toplevels
            app_state["icon_keepalive"] = icon_img
        except tk.TclError:
            pass 
 
    # Global Key Bindings
    window.bind("<Control-n>", lambda e: create_new_tab())
    window.bind("<Control-o>", lambda e: open_file())
    window.bind("<Control-O>", lambda e: open_project_folder()) 
    window.bind("<Control-s>", lambda e: save_file())
    window.bind("<Control-S>", lambda e: save_as_file())        
    window.bind("<Control-w>", lambda e: close_tab())
    window.bind("<Control-q>", lambda e: exit_app())
    window.bind("<Control-f>", lambda e: find_text())
    window.bind("<Control-a>", select_all)
    window.bind("<Control-z>", undo_action)
    window.bind("<Control-y>", redo_action)
    window.bind("<Control-e>", toggle_explorer)
    window.bind("<Control-j>", toggle_terminal)
    window.bind("<Control-T>", lambda e: [show_output_console(), app_state["terminal_input"].focus()]) 
    window.bind("<Control-r>", run_php_terminal)
    window.bind("<Control-b>", run_php_server)
    window.bind("<Control-l>", run_laravel_server)
    window.bind("<Control-L>", stop_laravel_server)
    window.bind("<Control-plus>", zoom_in)
    window.bind("<Control-minus>", zoom_out)
    window.bind("<Control-comma>", open_settings)
    window.bind("<F1>", show_about)
    window.protocol("WM_DELETE_WINDOW", exit_app)

    create_standard_menubar(window)
    
    # Context Menus
    context_menu = ttk.Menu(window, tearoff=False)
    context_menu.add_command(label="✏️ Rename Tab", command=rename_tab_action)
    context_menu.add_command(label="❌ Close Tab", command=lambda: close_tab(app_state["right_clicked_tab"]))
    app_state["tab_context_menu"] = context_menu
    
    tree_context_menu = ttk.Menu(window, tearoff=False)
    tree_context_menu.add_command(label="📄 New File", command=explorer_new_file)
    tree_context_menu.add_command(label="📁 New Folder", command=explorer_new_folder)
    tree_context_menu.add_separator()
    tree_context_menu.add_command(label="🗑️ Delete", command=explorer_delete)
    app_state["tree_context_menu"] = tree_context_menu

    # Main UI Layout Layout
    main_body = ttk.Frame(window)
    main_body.pack(side="top", fill="both", expand=True)

    # File Explorer Pane
    explorer_frame = ttk.Frame(main_body, width=250)
    app_state["explorer_frame"] = explorer_frame
    if app_state["explorer_visible"]:
        explorer_frame.pack(side="left", fill="y", padx=(5,0), pady=5)
    
    explorer_frame.pack_propagate(False)
    ttk.Label(explorer_frame, text='EXPLORER', font=("Arial", 10, "bold"), bootstyle="secondary").pack(side="top", fill="x", padx=5, pady=5)
    
    tree = ttk.Treeview(explorer_frame, show="tree", selectmode="browse", bootstyle="primary")
    tree.pack(fill="both", expand=True, padx=5, pady=5)

    tree.bind("<<TreeviewOpen>>", on_tree_open)
    tree.bind("<Double-1>", on_tree_double_click)
    tree.bind("<Button-3>", show_tree_context_menu)
    app_state["tree"] = tree
    
    if app_state["project_path"] and os.path.exists(app_state["project_path"]):
        reload_explorer()
        
    # Editor Notebook Pane
    notebook_frame = ttk.Frame(main_body)
    notebook_frame.pack(side="left", fill="both", expand=True)
    app_state["editor_container"] = notebook_frame

    notebook = ttk.Notebook(notebook_frame, bootstyle="primary")
    notebook.pack(fill="both", expand=True, padx=5, pady=5)
    app_state["notebook"] = notebook
    notebook.bind("<Button-3>", show_tab_context_menu)
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # Bottom Layout (Terminal & Status Bar)
    bottom_container = ttk.Frame(window)
    bottom_container.pack(side="bottom", fill="x")

    output_frame = ttk.Frame(bottom_container)
    app_state["output_console_frame"] = output_frame
    
    output_header = ttk.Frame(output_frame)
    output_header.pack(fill="x", padx=5, pady=5)

    ttk.Label(output_header, text="T E R M I N A L", bootstyle="secondary", font=("Arial", 12, "bold")).pack(side="left")
    ttk.Button(output_header, text="❌", width=3, bootstyle="danger-outline", command=hide_output_console).pack(side="right")
    
    output_console = tk.Text(output_frame, height=15, font=("Consolas", 10), state="disabled", bg="#1e1e1e", fg="#d4d4d4", borderwidth=0)
    output_console.pack(fill="both", expand=True, padx=5, pady=0)
    app_state["output_console"] = output_console

    # Status Bar
    status_bar = ttk.Frame(bottom_container, bootstyle="secondary", border=4)
    status_bar.pack(side="bottom", fill="x")
    app_state["status_bar"] = status_bar
    
    ttk.Button(status_bar, text="Terminal", bootstyle="secondary", command=toggle_terminal).pack(side="left", padx=5, pady=2)

    app_state["status_file"] = ttk.Label(status_bar, text="📄 No File", font=("Arial", 9), bootstyle="inverse-secondary")
    app_state["status_file"].pack(side="right", padx=5, pady=2)

    ttk.Label(status_bar, text="🔤 UTF-8", font=("Arial", 9), bootstyle="inverse-secondary").pack(side="right", padx=3, pady=2)

    app_state["status_words"] = ttk.Label(status_bar, text="", font=("Arial", 9), bootstyle="inverse-secondary")
    app_state["status_words"].pack(side="right", padx=5, pady=2)

    app_state["status_pos"] = ttk.Label(status_bar, text="", font=("Arial", 9), bootstyle="inverse-secondary")
    app_state["status_pos"].pack(side="right", padx=5, pady=2)

    # Finalize and Display Window
    window.update() 
    window.deiconify()
    window.mainloop()
