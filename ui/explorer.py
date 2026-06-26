import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog
from ttkbootstrap.dialogs import Messagebox, Querybox
from core.state import app_state, save_settings


def load_lc_project(app_state, populate_tree_callback):
    """Loads a custom .lc project configuration file."""
    filepath = filedialog.askopenfilename(
        title="Load Project",
        filetypes=[("Logic/Laravel Project", "*.lc")],
        parent=app_state["window"]
    )
    if not filepath:
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        project_dir = os.path.dirname(filepath)
        app_state["project_path"] = project_dir
        
        project_name = data.get("name", "Unknown")
        Messagebox.show_info(f"Project '{project_name}' loaded successfully.", "Project Loaded", parent=app_state["window"])
        
        populate_tree_callback(project_dir)
        
    except Exception as e:
        Messagebox.show_error(f"Failed to load project file:\n{e}", "Error", parent=app_state["window"])
        

def get_open_specific_file():
    """Deferred import to prevent circular dependency issues."""
    from ui.editor import open_specific_file
    return open_specific_file


def populate_tree(tree, parent, path):
    """Recursively populates the Treeview with directory contents."""
    for item in tree.get_children(parent):
        tree.delete(item)
        
    if not path or not os.path.exists(path): 
        return
        
    try:
        entries = os.listdir(path)
        # Sort directories first, then files alphabetically
        entries.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        
        for entry in entries:
            full_path = os.path.join(path, entry)
            is_dir = os.path.isdir(full_path)
            
            # Apply appropriate file/folder icons
            icon = " 📁" if is_dir else " 📄"
            node = tree.insert(parent, "end", text=f"{icon}  {entry}", values=[full_path, is_dir])
            
            # Insert a dummy node for directories to enable expandability
            if is_dir: 
                tree.insert(node, "end") 
    except PermissionError: 
        pass


def on_tree_open(event):
    """Handles expanding a directory node in the Treeview."""
    tree = app_state["tree"]
    node = tree.focus()
    values = tree.item(node, "values")
    if values and values[1] == 'True':
        populate_tree(tree, node, values[0])


def on_tree_double_click(event):
    """Handles opening a file when double-clicked in the Treeview."""
    tree = app_state["tree"]
    node = tree.focus()
    values = tree.item(node, "values")
    if values:
        path, is_dir = values[0], values[1] == 'True'
        if not is_dir: 
            open_func = get_open_specific_file()
            open_func(path)


def open_project_folder(event=None):
    """Prompts the user to open a project directory."""
    folder = filedialog.askdirectory(parent=app_state["window"])
    if folder:
        app_state["project_path"] = folder
        tree = app_state["tree"]
        for item in tree.get_children(): 
            tree.delete(item)
            
        root_node = tree.insert("", "end", text=f" 🌐  {os.path.basename(folder)}", values=[folder, True], open=True)
        populate_tree(tree, root_node, folder)
        save_settings()


def reload_explorer():
    """Refreshes the current project directory in the Treeview."""
    if app_state["project_path"]:
        tree = app_state["tree"]
        for item in tree.get_children(): 
            tree.delete(item)
            
        root_node = tree.insert("", "end", text=f" 🌐  {os.path.basename(app_state['project_path'])}", values=[app_state["project_path"], True], open=True)
        populate_tree(tree, root_node, app_state["project_path"])


# --- Context Menu Operations ---

def get_target_dir_from_node(node):
    """Resolves the appropriate target directory from a selected node."""
    target_dir = app_state["project_path"]
    if node:
        values = app_state["tree"].item(node, "values")
        if values: 
            target_dir = values[0] if values[1] == 'True' else os.path.dirname(values[0])
    return target_dir


def explorer_new_file():
    target_dir = get_target_dir_from_node(app_state.get("right_clicked_node"))
    if not target_dir: 
        return
        
    filename = Querybox.get_string("Enter file name:", "New File", parent=app_state["window"])
    if filename:
        filepath = os.path.join(target_dir, filename)
        try:
            with open(filepath, 'w') as f: 
                f.write("")
            reload_explorer()
            get_open_specific_file()(filepath)
        except Exception as e:
            Messagebox.show_error(str(e), "Error", parent=app_state["window"])


def explorer_new_folder():
    target_dir = get_target_dir_from_node(app_state.get("right_clicked_node"))
    if not target_dir: 
        return
        
    foldername = Querybox.get_string("Enter folder name:", "New Folder", parent=app_state["window"])
    if foldername:
        folderpath = os.path.join(target_dir, foldername)
        try:
            os.makedirs(folderpath)
            reload_explorer()
        except Exception as e:
            Messagebox.show_error(str(e), "Error", parent=app_state["window"])


def explorer_delete():
    node = app_state.get("right_clicked_node")
    if not node: 
        return
        
    values = app_state["tree"].item(node, "values")
    if not values: 
        return
        
    path, is_dir = values[0], values[1] == 'True'
    if Messagebox.yesno(f"Are you sure you want to delete '{os.path.basename(path)}'?\nThis action cannot be undone.", "Confirm Delete", parent=app_state["window"]) == "Yes":
        try:
            if is_dir: 
                shutil.rmtree(path)
            else: 
                os.remove(path)
            reload_explorer()
        except Exception as e:
            Messagebox.show_error(str(e), "Error", parent=app_state["window"])


def explorer_rename():
    node = app_state.get("right_clicked_node")
    if not node: 
        return
        
    values = app_state["tree"].item(node, "values")
    if not values: 
        return
        
    path = values[0]
    old_name = os.path.basename(path)
    new_name = Querybox.get_string("Enter new name:", "Rename", initialvalue=old_name, parent=app_state["window"])
    
    if new_name and new_name != old_name:
        new_path = os.path.join(os.path.dirname(path), new_name)
        try:
            os.rename(path, new_path)
            reload_explorer()
        except Exception as e:
            Messagebox.show_error(str(e), "Error", parent=app_state["window"])


def explorer_open_terminal():
    target_dir = get_target_dir_from_node(app_state.get("right_clicked_node"))
    if not target_dir: 
        return
    
    try:
        from ui.terminal import show_output_console, write_to_console, insert_prompt
        
        show_output_console()
        write_to_console(f"\n> Terminal focused on: {target_dir}\n", tag="info")
        insert_prompt()
        
    except ImportError as e:
        Messagebox.show_error(f"Could not load the built-in terminal:\n{e}", "Error", parent=app_state["window"])
    except Exception as e:
        Messagebox.show_error(str(e), "Error", parent=app_state["window"])


def explorer_close_project():
    if not app_state.get("project_path"):
        return
        
    if Messagebox.yesno("Are you sure you want to close the current project?", "Close Project", parent=app_state["window"]) == "Yes":
        app_state["project_path"] = ""
        tree = app_state["tree"]
        
        for item in tree.get_children(): 
            tree.delete(item)
            
        save_settings()


def show_tree_context_menu(event):
    """Dynamically builds and displays the right-click context menu for the explorer."""
    tree = app_state["tree"]
    iid = tree.identify_row(event.y)
    
    if iid:
        tree.selection_set(iid)
        tree.focus(iid)
        app_state["right_clicked_node"] = iid
    else:
        app_state["right_clicked_node"] = None

    context_menu = tk.Menu(tree, tearoff=0)
    context_menu.add_command(label="📝 New File", command=explorer_new_file)
    context_menu.add_command(label="📁 New Folder", command=explorer_new_folder)
    
    # Render file/folder specific options if a valid node is targeted
    if iid:
        context_menu.add_separator()
        context_menu.add_command(label="✏️ Rename", command=explorer_rename)
        context_menu.add_command(label="❌ Delete", command=explorer_delete)
        
    context_menu.add_separator()
    context_menu.add_command(label="⌨️ Open in Terminal", command=explorer_open_terminal)
    
    # Project specific actions
    if app_state.get("project_path"):
        context_menu.add_separator()
        context_menu.add_command(label="🚫 Close Project", command=explorer_close_project)
    
    context_menu.post(event.x_root, event.y_root)


def toggle_explorer(event=None):
    """Toggles the visibility of the file explorer pane."""
    if app_state["explorer_visible"]:
        app_state["explorer_frame"].pack_forget()
        app_state["explorer_visible"] = False
    else:
        app_state["explorer_frame"].pack(side="left", fill="y", padx=(0, 5), before=app_state["editor_container"])
        app_state["explorer_visible"] = True
