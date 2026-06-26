import os
import re
import tkinter as tk
from tkinter import filedialog
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox, Querybox
from core.state import app_state, ALL_TTK_THEMES, php_keywords, save_settings
from ui.explorer import reload_explorer
from tkinter import font


def get_current_tab_data():
    """Retrieves data for the currently active notebook tab."""
    notebook = app_state["notebook"]
    if not notebook: 
        return None
    try:
        current_tab_id = notebook.select()
        return app_state["tabs"].get(current_tab_id) if current_tab_id else None
    except tk.TclError: 
        return None


def update_recent_menu():
    """Updates the recent files menu with the current list of recent files."""
    if not app_state["recent_menu"]: 
        return
    app_state["recent_menu"].delete(0, 'end')
    for filepath in app_state["recent_files"]:
        if os.path.exists(filepath):
            app_state["recent_menu"].add_command(
                label=f"📄 {os.path.basename(filepath)}",
                command=lambda f=filepath: open_specific_file(f)
            )
    if not app_state["recent_files"]:
        app_state["recent_menu"].add_command(label="No recent files", state="disabled")
    else:
        app_state["recent_menu"].add_separator()
        app_state["recent_menu"].add_command(label="🧹 Clear Recent", command=clear_recent_files)


def add_to_recent(filepath):
    """Adds a file to the top of the recent files list and updates settings."""
    if filepath in app_state["recent_files"]:
        app_state["recent_files"].remove(filepath)
    app_state["recent_files"].insert(0, filepath)
    app_state["recent_files"] = app_state["recent_files"][:10]  # Limit to 10 entries
    update_recent_menu()
    save_settings()


def clear_recent_files():
    """Clears all entries from the recent files list."""
    app_state["recent_files"] = []
    update_recent_menu()
    save_settings()


def on_tab_changed(*args):
    """Handles logic executed when switching between tabs."""
    update_line_numbers()
    update_status_bar()
    perform_syntax_highlighting()
    tab_data = get_current_tab_data()
    if tab_data and app_state["window"]:
        filepath = tab_data["filepath"]
        app_state["window"].title(f"Laracode - {filepath}" if filepath else "Laracode")
    elif app_state["window"]:
        app_state["window"].title("Laracode")


def create_new_tab(title=None, filepath=None, content="", event=None):
    """Creates a new editor tab in the notebook."""
    if title is None:
        title = f"Untitled-{app_state['tab_counter']}"
        app_state['tab_counter'] += 1

    notebook = app_state["notebook"]
    tab_frame = ttk.Frame(notebook)
    notebook.add(tab_frame, text=f"📄 {title}")
    notebook.select(tab_frame)
    tab_id = notebook.select()

    current_font = (app_state["font_family"], app_state["font_size"])
    
    # Setup line numbers display
    line_numbers = tk.Text(tab_frame, width=4, padx=5, pady=5, font=current_font, bg="#2b2b2b", fg="gray", state="disabled", highlightthickness=0, borderwidth=0)
    line_numbers.pack(side="left", fill="y", padx=5, pady=5)
    
    # Setup the main text editor area
    editor = tk.Text(tab_frame, undo=True, maxundo=-1, autoseparators=True, font=current_font, wrap="none", padx=5, pady=5, highlightthickness=0, borderwidth=0)
    editor.pack(side="left", fill="both", expand=True, padx=5, pady=5)

    if content: 
        editor.insert("1.0", content)
    
    editor.bind("<KeyRelease>", handle_keypress)
    editor.bind("<ButtonRelease-1>", handle_click)
    
    # Sync scrolling between text editor and line numbers
    original_yscrollcommand = editor.cget("yscrollcommand")
    def on_scroll(*args, ed=editor, ln=line_numbers, orig=original_yscrollcommand):
        if orig: ed.tk.call(orig, *args)
        ln.yview_moveto(ed.yview()[0])
    editor.configure(yscrollcommand=on_scroll)
    
    app_state["tabs"][tab_id] = {
        "title": title, "frame": tab_frame, "editor": editor,
        "line_numbers": line_numbers, "filepath": filepath, "last_line_count": 0
    }
    on_tab_changed()


def close_tab(tab_id=None, event=None):
    """Closes an active editor tab."""
    notebook = app_state["notebook"]
    if not notebook: 
        return
    if tab_id is None:
        try: tab_id = notebook.select()
        except tk.TclError: return
    if tab_id and tab_id in app_state["tabs"]:
        notebook.forget(tab_id)
        del app_state["tabs"][tab_id]
    on_tab_changed()


def rename_tab_action():
    """Prompts the user to rename the currently selected tab."""
    tab_id = app_state["right_clicked_tab"]
    if not tab_id or tab_id not in app_state["tabs"]: 
        return
    old_title = app_state["tabs"][tab_id]["title"]
    
    new_name = Querybox.get_string(
        prompt="Enter new tab name:", 
        title="Rename Tab", 
        initialvalue=old_title, 
        parent=app_state["window"]
    )
    
    if new_name and new_name != old_title:
        app_state["notebook"].tab(tab_id, text=f"📄 {new_name}")
        app_state["tabs"][tab_id]["title"] = new_name


def show_tab_context_menu(event):
    """Displays the context menu when right-clicking a tab."""
    notebook = app_state["notebook"]
    try:
        tab_id = notebook.identify(event.x, event.y)
        if tab_id:
            index = notebook.index(f"@{event.x},{event.y}")
            app_state["right_clicked_tab"] = notebook.tabs()[index]
            app_state["tab_context_menu"].post(event.x_root, event.y_root)
    except: 
        pass


def sync_scroll_fast(*args):
    """Synchronizes scrolling between line numbers and the editor."""
    tab_data = get_current_tab_data()
    if tab_data: 
        tab_data["line_numbers"].yview_moveto(tab_data["editor"].yview()[0])


def update_status_bar(*args):
    """Updates information displayed in the status bar."""
    tab_data = get_current_tab_data()
    if not tab_data:
        app_state["status_file"].configure(text="📄 No File")
        app_state["status_pos"].configure(text="")
        app_state["status_words"].configure(text="")
        return
    editor = tab_data["editor"]
    line, col = editor.index(tk.INSERT).split('.')
    words_count = len(editor.get("1.0", "end-1c").split())
    filename = os.path.basename(tab_data["filepath"]) if tab_data["filepath"] else tab_data["title"]
    
    app_state["status_file"].configure(text=f"📄 File: {filename}")
    app_state["status_pos"].configure(text=f"📍 Ln {line}, Col {int(col) + 1}")
    app_state["status_words"].configure(text=f"📝 Words: {words_count}")


def update_line_numbers():
    """Generates and updates the line numbers for the active editor."""
    tab_data = get_current_tab_data()
    if not tab_data: 
        return
    editor = tab_data["editor"]
    line_numbers = tab_data["line_numbers"]
    lines_count = int(editor.index("end-1c").split('.')[0])
    
    if lines_count != tab_data["last_line_count"]:
        line_numbers_string = "\n".join(str(i) for i in range(1, lines_count + 1))
        line_numbers.configure(state="normal")
        line_numbers.delete("1.0", "end")
        line_numbers.insert("1.0", line_numbers_string)
        line_numbers.configure(state="disabled")
        tab_data["last_line_count"] = lines_count
        sync_scroll_fast()


def perform_syntax_highlighting():
    """Applies basic syntax highlighting to the PHP editor text."""
    tab_data = get_current_tab_data()
    if not tab_data: 
        return
    editor = tab_data["editor"]
    text_content = editor.get("1.0", "end-1c")
    
    for word in php_keywords.keys(): 
        editor.tag_remove(word, "1.0", "end")
        
    for word, color in php_keywords.items():
        editor.tag_config(word, foreground=color)
        pattern = r'\b' + re.escape(word) + r'\b' if word.isalpha() else re.escape(word)
        for match in re.finditer(pattern, text_content):
            editor.tag_add(word, f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")


def handle_keypress(event=None):
    """Event handler for key presses within the editor."""
    update_line_numbers()
    update_status_bar()
    if app_state["update_timer"]: 
        app_state["window"].after_cancel(app_state["update_timer"])
    app_state["update_timer"] = app_state["window"].after(250, perform_syntax_highlighting)


def handle_click(event=None):
    """Event handler for mouse clicks within the editor."""
    sync_scroll_fast()
    update_status_bar()


def select_all(event=None):
    """Selects all text in the current editor."""
    tab_data = get_current_tab_data()
    if tab_data: 
        tab_data["editor"].tag_add("sel", "1.0", "end")
    return "break"


def undo_action(event=None):
    """Performs undo operation on the current editor."""
    tab_data = get_current_tab_data()
    if tab_data:
        try: tab_data["editor"].edit_undo()
        except tk.TclError: pass
        handle_keypress()
    return "break"


def redo_action(event=None):
    """Performs redo operation on the current editor."""
    tab_data = get_current_tab_data()
    if tab_data:
        try: tab_data["editor"].edit_redo()
        except tk.TclError: pass
        handle_keypress()
    return "break"


def open_specific_file(filepath):
    """Opens a specific file path and creates a new editor tab."""
    try:
        with open(filepath, "r", encoding="utf-8") as file: 
            content = file.read()
        create_new_tab(title=os.path.basename(filepath), filepath=filepath, content=content)
        add_to_recent(filepath)
    except Exception as e:
        Messagebox.show_error(f"Could not open file:\n{e}", "Error", parent=app_state["window"])


def open_file(event=None):
    """Prompts the user to select and open a file."""
    filepath = filedialog.askopenfilename(defaultextension=".php", filetypes=[("PHP Files", "*.php"), ("All Files", "*.*")], parent=app_state["window"])
    if filepath: 
        open_specific_file(filepath)


def save_file(event=None):
    """Saves the contents of the currently active tab."""
    tab_data = get_current_tab_data()
    if not tab_data: 
        return
    if tab_data["filepath"]:
        try:
            with open(tab_data["filepath"], "w", encoding="utf-8") as file:
                file.write(tab_data["editor"].get("1.0", "end-1c"))
            add_to_recent(tab_data["filepath"])
            update_status_bar()
        except Exception as e: 
            Messagebox.show_error(f"Could not save file:\n{e}", "Error", parent=app_state["window"])
    else: 
        save_as_file()


def save_as_file(event=None):
    """Prompts the user to specify a file path and saves the active tab's contents."""
    tab_data = get_current_tab_data()
    if not tab_data: 
        return
    filepath = filedialog.asksaveasfilename(defaultextension=".php", filetypes=[("PHP Files", "*.php"), ("All Files", "*.*")], parent=app_state["window"])
    if not filepath: 
        return
    try:
        content = tab_data["editor"].get("1.0", "end-1c")
        with open(filepath, "w", encoding="utf-8") as file: 
            file.write(content)
        current_tab_id = app_state["notebook"].select()
        create_new_tab(title=os.path.basename(filepath), filepath=filepath, content=content)
        close_tab(current_tab_id)
        add_to_recent(filepath)
        reload_explorer() 
    except Exception as e: 
        Messagebox.show_error(f"Could not save file:\n{e}", "Error", parent=app_state["window"])


def find_text(event=None):
    """Opens a dialog to search for text within the current editor."""
    tab_data = get_current_tab_data()
    if not tab_data: 
        return
    editor = tab_data["editor"]
    
    search_query = Querybox.get_string(
        prompt="Enter text to find:", 
        title="Find", 
        parent=app_state["window"]
    )
    
    if search_query:
        editor.tag_remove("search", "1.0", "end")
        start_pos = editor.search(search_query, "1.0", stopindex="end")
        if start_pos:
            end_pos = f"{start_pos}+{len(search_query)}c"
            editor.tag_config("search", background="yellow", foreground="black")
            editor.tag_add("search", start_pos, end_pos)
            editor.see(start_pos)
        else: 
            Messagebox.show_info("Text not found.", "Find", parent=app_state["window"])


def apply_settings(family, size, mode, win=None):
    try:
        valid_size = int(size)
    except ValueError:
        Messagebox.show_warning("Please enter a valid number for font size.", "Warning", parent=app_state["window"])
        return

    app_state["font_family"] = family
    app_state["font_size"] = valid_size
    app_state["theme_mode"] = mode
    app_state["window"].style.theme_use(mode)
    
    new_font = (family, valid_size)
    for data in app_state["tabs"].values():
        data["editor"].configure(font=new_font)
        data["line_numbers"].configure(font=new_font)
        
    save_settings()
    if win: win.destroy()

def zoom_in(event=None):
    """Increases the editor font size."""
    if app_state["font_size"] < 72: 
        apply_settings(app_state["font_family"], app_state["font_size"] + 2, app_state["theme_mode"])


def zoom_out(event=None):
    """Decreases the editor font size."""
    if app_state["font_size"] > 6: 
        apply_settings(app_state["font_family"], app_state["font_size"] - 2, app_state["theme_mode"])


def show_shortcuts(event=None):
    """Displays a list of available keyboard shortcuts."""
    shortcuts = "Ctrl+N: New File\nCtrl+O: Open File\nCtrl+Shift+O: Open Project\nCtrl+S: Save\nCtrl+Shift+S: Save As\nCtrl+Q: Exit\n\nCtrl+Z / Ctrl+Y: Undo / Redo\nCtrl+X / C / V: Cut / Copy / Paste\nCtrl+A: Select All\nCtrl+F: Find & Replace\n\nCtrl+E: Toggle Explorer\nCtrl+J: Toggle Terminal\nCtrl++ / Ctrl+-: Zoom In / Out\n\nCtrl+R: Run File in Terminal\nCtrl+B: Run Local PHP Server\nCtrl+Shift+T: Open Local Terminal\nCtrl+L: Run Laravel Server\nCtrl+Shift+L: Stop Laravel Server"
    Messagebox.show_info(shortcuts, "Keyboard Shortcuts", parent=app_state["window"])


def open_settings(event=None):
    settings_win = ttk.Toplevel(app_state["window"])
    settings_win.title("Preferences")
    settings_win.geometry("450x380")
    
    # Apply app icon explicitly to Toplevels
    if "icon_keepalive" in app_state and app_state["icon_keepalive"]:
        try:
            settings_win.iconphoto(False, app_state["icon_keepalive"])
        except tk.TclError:
            pass

    settings_win.transient(app_state["window"])
    settings_win.grab_set()
    
    settings_notebook = ttk.Notebook(settings_win, bootstyle="info")
    settings_notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    editor_tab = ttk.Frame(settings_notebook, padding=10)
    settings_notebook.add(editor_tab, text="📝 Editor")
    
    system_fonts = list(font.families())
    system_fonts.sort()

    ttk.Label(editor_tab, text="Font Family:").pack(anchor="w", pady=(5, 2))
    family_var = ttk.StringVar(value=app_state["font_family"])

    ttk.Combobox(editor_tab, textvariable=family_var, values=system_fonts, state="readonly").pack(fill="x")
    
    ttk.Label(editor_tab, text="Font Size:").pack(anchor="w", pady=(15, 2))
    size_var = ttk.StringVar(value=str(app_state["font_size"]))
 
    ttk.Combobox(editor_tab, textvariable=size_var, values=["10", "12", "14", "16", "18", "20", "22", "24", "36", "48", "72"]).pack(fill="x")

    appearance_tab = ttk.Frame(settings_notebook, padding=10)
    settings_notebook.add(appearance_tab, text="🎨 Appearance")
    ttk.Label(appearance_tab, text="Color Theme:").pack(anchor="w", pady=(5, 2))
    mode_var = ttk.StringVar(value=app_state["theme_mode"])
    ttk.Combobox(appearance_tab, textvariable=mode_var, values=ALL_TTK_THEMES, state="readonly").pack(fill="x")
    
    btn_frame = ttk.Frame(settings_win)
    btn_frame.pack(fill="x", padx=10, pady=10)
    ttk.Button(btn_frame, text="💾 Apply & Save", bootstyle="primary", command=lambda: apply_settings(family_var.get(), size_var.get(), mode_var.get(), settings_win)).pack(side="right")
    ttk.Button(btn_frame, text="Cancel", bootstyle="secondary", command=settings_win.destroy).pack(side="right", padx=10)


def show_about(event=None):
    """Displays information about the application."""
    Messagebox.show_info(
        "▶ Laracode is Professional PHP/Laravel Editor\n" \
        "💻 Version: 1.0.0\n\n" \
        "▶ Created with Armin Daraei\n" \
        "📞 Tell Me:\n" \
        "  📲 GitHub: armindaraei1381\n" \
        "  📲 Linkdin: ArminDaraei\n"
        "  📲 Telegram: ArminDaraei", 
        "About",
        parent=app_state["window"]
    )


def exit_app(event=None):
    """Safely terminates ongoing background processes and exits the application."""
    if app_state["php_server_process"]:
        try: app_state["php_server_process"].terminate()
        except: pass
    if app_state["laravel_process"]:
        try: app_state["laravel_process"].terminate()
        except: pass
    if app_state["window"]: 
        app_state["window"].destroy()
