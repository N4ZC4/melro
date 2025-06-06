import tkinter as tk
import os
import subprocess

# Colors and styles
DARK_BG = "#0f0e0e"
DARKER_BG = "#080808"
PANEL_BG = "#202020"
ACCENT_ORANGE = "#FFA500"
ACCENT_GOLD = "#FFD700"
STATUS_GREEN = "#00FF00"
TITLE_COLOR = "#FFFFFF"
TEXT_COLOR = "#E0E0E0"
WARNING_COLOR = "#FF5252"
BTN_BG = "#2F2F2F"
BTN_TEXT = "#E0E0E0"

class HoverButton(tk.Button):
    """Custom button class with hover effect"""
    def __init__(self, master, **kw):
        tk.Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.defaultForeground = self["foreground"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        """Change color on hover"""
        if self["state"] != "disabled":
            self["background"] = ACCENT_ORANGE
            self["foreground"] = "#FFFFFF"

    def on_leave(self, e):
        """Change color back to default"""
        self["background"] = self.defaultBackground
        self["foreground"] = self.defaultForeground

def setup_page_template(page, title_text, subtitle_text=None):
    """Create a common page template with a header and subtitle"""
    # Header
    header = tk.Label(page, text=title_text, font=("Arial", 16, "bold"), 
                     bg=DARK_BG, fg=TITLE_COLOR)
    header.place(relx=0.5, y=60, anchor="center")
    
    # Subtitle (optional)
    if subtitle_text:
        subtitle = tk.Label(page, text=subtitle_text, font=("Arial", 12), 
                          bg=DARK_BG, fg="#CCCCCC")
        subtitle.place(relx=0.5, y=90, anchor="center")
    
    return header

def create_button(parent, text, command, bg=PANEL_BG, fg=ACCENT_GOLD):
    """Helper method to create styled buttons"""
    button = HoverButton(parent, text=text, font=("Arial", 14, "bold"),
                        bg=bg, fg=fg, bd=0,
                        activebackground=ACCENT_ORANGE, activeforeground="#FFFFFF",
                        command=command)
    return button

def get_wifi_interfaces():
    """Get list of wireless interfaces"""
    try:
        # For Linux systems
        if os.name == 'posix':
            result = subprocess.check_output(['iwconfig'], stderr=subprocess.STDOUT, text=True)
            interfaces = []
            for line in result.split('\n'):
                if ' IEEE ' in line:  # This is a wireless interface
                    interfaces.append(line.split()[0])
            return interfaces
        # For Windows systems (simplified version)
        elif os.name == 'nt':
            result = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], text=True)
            if "Name" in result:
                return ["wlan0"]  # Placeholder for Windows demo
            return []
    except Exception as e:
        print(f"Error getting interfaces: {e}")
        return []

def is_in_monitor_mode(interface):
    """Check if interface is in monitor mode"""
    try:
        if os.name == 'posix':
            result = subprocess.check_output(['iwconfig', interface], stderr=subprocess.STDOUT, text=True)
            return 'Mode:Monitor' in result
        return False
    except Exception:
        return False

def set_monitor_mode(interface, enable=True):
    """Set interface to monitor mode or managed mode"""
    try:
        if os.name == 'posix':
            if enable:
                subprocess.call(['sudo', 'ip', 'link', 'set', interface, 'down'])
                subprocess.call(['sudo', 'iw', interface, 'set', 'monitor', 'none'])
                subprocess.call(['sudo', 'ip', 'link', 'set', interface, 'up'])
                return True
            else:
                subprocess.call(['sudo', 'ip', 'link', 'set', interface, 'down'])
                subprocess.call(['sudo', 'iw', interface, 'set', 'type', 'managed'])
                subprocess.call(['sudo', 'ip', 'link', 'set', interface, 'up'])
                return True
        return False
    except Exception as e:
        print(f"Error setting mode: {e}")
        return False 