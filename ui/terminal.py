import os
import subprocess
import threading
import webbrowser
import tkinter as tk
from ttkbootstrap.dialogs import Messagebox
from typing import Dict, Any
from core.state import app_state


def get_tab_data_and_save():
    """Deferred imports to avoid circular dependency with editor functions."""
    from ui.editor import get_current_tab_data, save_file
    return get_current_tab_data(), save_file


def toggle_terminal(event=None):
    """Toggles visibility of the terminal panel."""
    if app_state.get("terminal_visible"): 
        hide_output_console()
    else: 
        show_output_console()


def setup_terminal_tags():
    """Configures the formatting and color tags for terminal outputs."""
    console = app_state["output_console"]
    console.tag_config("prompt", foreground="#56b6c2", font=("Consolas", 11, "bold"))
    console.tag_config("error", foreground="#e06c75")
    console.tag_config("success", foreground="#98c379")
    console.tag_config("info", foreground="#61afef")


def insert_prompt():
    """Inserts a command-line style prompt with the current path."""
    console = app_state["output_console"]
    cwd = app_state.get("project_path") or os.getcwd()
    prompt_text = f"{cwd}> "
    
    # Insert a new line if the current terminal line is not already empty
    if console.get("end-2c", "end-1c") != "\n":
        console.insert("end", "\n")
        
    console.insert("end", prompt_text, "prompt")
    console.mark_set("input_start", "end-1c")
    console.mark_gravity("input_start", "left")
    console.see("end")


def show_output_console():
    """Renders the output terminal pane and prepares its command bindings."""
    app_state["output_console_frame"].pack(side="top", fill="x", padx=5, pady=(0, 5))
    app_state["terminal_visible"] = True
    console = app_state["output_console"]
    console.configure(state="normal")
    
    # Configure styling tags if they have not been set up
    if not console.tag_names():
        setup_terminal_tags()
        
    # Standard terminal interaction key bindings required for prompt navigation
    console.bind("<Return>", handle_return_key)
    console.bind("<BackSpace>", handle_backspace_key)
    console.bind("<Key>", handle_key_press)
    
    # Write the initial prompt if terminal is currently empty
    if not console.get("1.0", tk.END).strip():
        insert_prompt()
        
    console.focus()


def hide_output_console():
    """Hides the terminal panel."""
    app_state["output_console_frame"].pack_forget()
    app_state["terminal_visible"] = False


def write_to_console(text, clear=False, tag=None):
    """Writes standard text or logs to the output console."""
    console = app_state["output_console"]
    console.configure(state="normal")
    if clear: 
        console.delete("1.0", "end")
    if tag:
        console.insert("end", text, tag)
    else:
        console.insert("end", text)
    console.see("end")


def handle_return_key(event):
    """Executes the user typed terminal commands asynchronously on key return."""
    console = app_state["output_console"]
    cmd = console.get("input_start", "end-1c").strip()
    console.insert("end", "\n")
    
    if not cmd:
        insert_prompt()
        return "break"
        
    if cmd.lower() in ["clear", "cls"]:
        write_to_console("", clear=True)
        insert_prompt()
        return "break"

    cwd = app_state.get("project_path") or os.getcwd()
    
    def task():
        try:
            kwargs: Dict[str, Any] = {
                "shell": True, 
                "cwd": cwd, 
                "stdout": subprocess.PIPE, 
                "stderr": subprocess.STDOUT, 
                "text": True
            }
            if os.name == 'nt': 
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            
            process = subprocess.Popen(cmd, **kwargs)
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    app_state["window"].after(0, write_to_console, line)
                process.stdout.close()
            process.wait()
        except Exception as e:
            app_state["window"].after(0, write_to_console, f"Error: {e}\n", False, "error")
        finally:
            app_state["window"].after(0, insert_prompt)
            
    threading.Thread(target=task, daemon=True).start()
    return "break"


def handle_backspace_key(event):
    """Prevents deleting parts of the command line interface prompt."""
    console = app_state["output_console"]
    if console.compare("insert", "<=", "input_start"):
        return "break"


def handle_key_press(event):
    """Prevents users from typing behind the input prompt index (previous output sections)."""
    console = app_state["output_console"]
    allowed_navigation_keys = [
        "Control_L", "Control_R", "c", "C", "Shift_L", "Shift_R", 
        "Up", "Down", "Left", "Right"
    ]
    if console.compare("insert", "<", "input_start") and event.keysym not in allowed_navigation_keys:
        console.mark_set("insert", "end-1c")


def run_php_terminal(event=None):
    """Runs the currently selected PHP script file in CLI mode."""
    tab_data, save_func = get_tab_data_and_save()
    if not tab_data or not tab_data["filepath"]:
        Messagebox.show_warning("Please save the file first before running.", "Warning", parent=app_state["window"])
        return
    save_func()
    show_output_console()
    filepath = tab_data["filepath"]
    php_exe = app_state.get("php_path", "php")
    
    write_to_console(f"\n> Running: {php_exe} {filepath}\n{'-'*40}\n", tag="info")
    
    def task():
        try:
            kwargs = {"capture_output": True, "text": True}
            if os.name == 'nt': 
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            
            result = subprocess.run([php_exe, "-f", filepath], **kwargs)
            
            def update_ui():
                if result.stdout: 
                    write_to_console(result.stdout)
                if result.stderr: 
                    write_to_console(result.stderr, tag="error")
                write_to_console(f"\n{'-'*40}\n> Execution finished.\n", tag="success")
                insert_prompt()
                
            app_state["window"].after(0, update_ui)
        except Exception as e:
            app_state["window"].after(
                0, 
                lambda: [write_to_console(f"Error: {str(e)}\n", tag="error"), insert_prompt()]
            )
            
    threading.Thread(target=task, daemon=True).start()


def run_php_server(event=None):
    """Starts a local development server for the current directory using PHP's built-in server."""
    tab_data, save_func = get_tab_data_and_save()
    if not tab_data or not tab_data["filepath"]:
        Messagebox.show_warning("Please save the file first before starting the server.", "Warning", parent=app_state["window"])
        return
    save_func()
    
    if app_state.get("php_server_process"):
        try: 
            app_state["php_server_process"].terminate()
        except: 
            pass
            
    filepath = tab_data["filepath"]
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    url = f"http://localhost:8000/{filename}"
    php_exe = app_state.get("php_path", "php")
    
    try:
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if os.name == 'nt': 
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
        process = subprocess.Popen([php_exe, "-S", "localhost:8000", "-t", directory], **kwargs)
        app_state["php_server_process"] = process
        show_output_console()
        write_to_console(f"\n> Started PHP Local Server at {url}\n> Document Root: {directory}\n", tag="success")
        insert_prompt()
        webbrowser.open(url)
    except Exception as e:
        show_output_console()
        write_to_console(f"\nError starting server: {str(e)}\n", tag="error")
        insert_prompt()


def run_laravel_server(event=None):
    """Initializes the Laravel Development Server (artisan serve) inside the project directory."""
    cwd = app_state.get("project_path")
    if not cwd:
        Messagebox.show_warning("Please Open a Project folder first.", "Warning", parent=app_state["window"])
        return
    if not os.path.exists(os.path.join(cwd, "artisan")):
        Messagebox.show_error("No 'artisan' file found. Is this a Laravel project?", "Error", parent=app_state["window"])
        return
        
    if app_state.get("laravel_process"):
        try: 
            app_state["laravel_process"].terminate()
        except: 
            pass
        
    show_output_console()
    write_to_console(f"\n> Starting Laravel Development Server in {cwd}...\n", tag="info")
    php_exe = app_state.get("php_path", "php")
    
    def task():
        try:
            kwargs = {
                "cwd": cwd, 
                "stdout": subprocess.PIPE, 
                "stderr": subprocess.STDOUT, 
                "text": True
            }
            if os.name == 'nt': 
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            
            process = subprocess.Popen([php_exe, "artisan", "serve"], **kwargs)
            app_state["laravel_process"] = process
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    app_state["window"].after(0, write_to_console, line)
                process.stdout.close()
            process.wait()
            app_state["window"].after(
                0, 
                lambda: [write_to_console("\n> Laravel Server stopped.\n", tag="info"), insert_prompt()]
            )
        except Exception as e:
            app_state["window"].after(
                0, 
                lambda: [write_to_console(f"Error: {e}\n", tag="error"), insert_prompt()]
            )
            
    threading.Thread(target=task, daemon=True).start()


def stop_laravel_server(event=None):
    """Safely terminates the running Laravel Local Server process."""
    if app_state.get("laravel_process"):
        try:
            app_state["laravel_process"].terminate()
            app_state["laravel_process"] = None
            show_output_console()
            write_to_console("\n> Laravel Server stopped manually.\n", tag="error")
            insert_prompt()
        except Exception as e:
            show_output_console()
            write_to_console(f"\n> Error stopping server: {e}\n", tag="error")
            insert_prompt()
