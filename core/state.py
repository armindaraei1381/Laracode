import os
import json
from typing import Dict, Any

# Application configuration paths
SETTINGS_DIR = "config"
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "laracode_data.json")

ALL_TTK_THEMES = [
    "cosmo", "flatly", "journal", "litera", "lumen", "minty", "pulse", 
    "sandstone", "united", "yeti", "morph", "simplex", "cerulean", 
    "cyborg", "darkly", "slate", "solar", "superhero", "vapor"
]

php_keywords = {
    # Tags (Red)
    "<?php": "#e06c75", "?>": "#e06c75",
    
    # Constructs & Built-ins (Cyan)
    "echo": "#56b6c2", "print": "#56b6c2", "isset": "#56b6c2", 
    "empty": "#56b6c2", "die": "#56b6c2", "exit": "#56b6c2", "unset": "#56b6c2",
    
    # Control Flow & Modifiers (Purple)
    "function": "#CD5CD6", "if": "#c678dd", "else": "#c678dd", 
    "elseif": "#c678dd", "return": "#c678dd", "class": "#c678dd",
    "public": "#c678dd", "private": "#c678dd", "protected": "#c678dd",
    "static": "#c678dd", "final": "#c678dd", "abstract": "#c678dd",
    "new": "#c678dd", "clone": "#c678dd", "instanceof": "#c678dd",
    "try": "#c678dd", "catch": "#c678dd", "finally": "#c678dd", "throw": "#c678dd",
    "for": "#c678dd", "foreach": "#c678dd", "while": "#c678dd", "do": "#c678dd",
    "switch": "#c678dd", "case": "#c678dd", "break": "#c678dd", "continue": "#c678dd",
    "default": "#c678dd", "interface": "#c678dd", "trait": "#c678dd", 
    "extends": "#c678dd", "implements": "#c678dd", "namespace": "#c678dd", 
    "use": "#c678dd", "as": "#c678dd", "include": "#c678dd", "require": "#c678dd", 
    "include_once": "#c678dd", "require_once": "#c678dd", "global": "#c678dd",
    
    # Booleans & Null (Orange)
    "true": "#d19a66", "false": "#d19a66", "null": "#d19a66",

    "(": "#d19a66",")": "#d19a66","/": "#e06c75", 
}


app_state: Dict[str, Any] = {
    "window": None,
    "notebook": None,
    "tabs": {},
    "tab_counter": 1,
    "update_timer": None,
    "status_bar": None,
    "status_file": None,
    "status_pos": None,
    "status_words": None,
    "font_family": "Consolas",
    "font_size": 12,
    "theme_mode": "darkly", 
    "word_wrap": False,
    "php_path": "php",
    "recent_files": [],          
    "recent_menu": None,         
    "tab_context_menu": None,
    "right_clicked_tab": None,
    "output_console_frame": None,
    "output_console": None,
    "terminal_input": None,
    "php_server_process": None,
    "laravel_process": None,
    "terminal_visible": False,
    "project_path": None,
    "tree": None,
    "tree_context_menu": None,
    "right_clicked_node": None,
    "explorer_frame": None,
    "editor_container": None,
    "explorer_visible": False 
}

def load_settings():
    """Loads application settings from the configuration file."""
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                app_state["font_family"] = data.get("font_family", "Consolas")
                app_state["font_size"] = data.get("font_size", 12)
                
                # Validate and apply theme
                saved_theme = data.get("theme_mode", "darkly")
                app_state["theme_mode"] = saved_theme if saved_theme in ALL_TTK_THEMES else "darkly"
                
                app_state["word_wrap"] = data.get("word_wrap", False)
                app_state["php_path"] = data.get("php_path", "php")
                app_state["recent_files"] = data.get("recent_files", [])
                app_state["project_path"] = data.get("project_path", None)
        except Exception:
            # Fallback to default state if parsing fails
            pass

def save_settings():
    """Saves the current application state to the configuration file."""
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        
    data = {
        "font_family": app_state["font_family"],
        "font_size": app_state["font_size"],
        "theme_mode": app_state["theme_mode"],
        "word_wrap": app_state["word_wrap"],
        "php_path": app_state["php_path"],
        "recent_files": app_state["recent_files"],
        "project_path": app_state["project_path"]
    }
    
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")
