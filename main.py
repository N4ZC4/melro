import tkinter as tk
from tkinter import ttk, font
import time
import os
import subprocess
import sys
import threading

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import attack modules
from attacks.beacon_flooding import BeaconFloodingAttack
from attacks.passive_recon import PassiveRecon
from attacks.utils import is_in_monitor_mode, set_monitor_mode

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

# Custom button class with hover effect
class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self, master=master, **kw)
        self.defaultBackground = self["background"]
        self.defaultForeground = self["foreground"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def on_enter(self, e):
        if self["state"] != "disabled":
            self["background"] = ACCENT_ORANGE
            self["foreground"] = "#FFFFFF"
            
    def on_leave(self, e):
        self["background"] = self.defaultBackground
        self["foreground"] = self.defaultForeground
        
    def update_default_colors(self):
        """Update the default colors to the current colors"""
        self.defaultForeground = self["foreground"]

class MelroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Melro IoT Project")
        self.root.geometry("480x640")
        self.root.configure(bg=DARK_BG)
        
        # Custom fonts
        self.cyberfont = font.Font(family="Arial", size=18, weight="bold")
        self.titlefont = font.Font(family="Arial", size=24, weight="bold")
        
        # Lists to track time and CPU labels
        self.time_labels = []
        self.cpu_temp_labels = []
        
        # Monitor mode state and interface names
        self.monitor_mode_active = False
        self.normal_interface = "wlan1"
        self.monitor_interface = "wlan1mon"
        
        # Check initial monitor mode state
        self.check_monitor_mode_state()
        
        # Create page frames
        self.main_frame = tk.Frame(root, bg=DARK_BG)
        self.beacon_flooding_page = tk.Frame(root, bg=DARK_BG)
        self.passive_recon_page = tk.Frame(root, bg=DARK_BG)
        
        # Initialize attack modules
        self.beacon_flooding_attack = BeaconFloodingAttack(root, lambda: self.show_frame(self.main_frame))
        self.passive_recon = PassiveRecon(root, lambda: self.show_frame(self.main_frame))
        
        self.setup_ui()
        
        # Start update loops
        self.update_time()
        self.update_cpu_temp()
        
        # Show initial frame
        self.show_frame(self.main_frame)
    
    # Check if monitor mode is active by looking for wlan1mon interface
    def check_monitor_mode_state(self):
        """Check if monitor mode is active by detecting wlan1mon interface"""
        try:
            # Use 'ip link' to list interfaces
            result = subprocess.run(['ip', 'link'], capture_output=True, text=True)
            output = result.stdout
            
            # Check if monitor mode interface exists
            if self.monitor_interface in output:
                self.monitor_mode_active = True
            else:
                self.monitor_mode_active = False
                
            # On non-Linux systems, simulate behavior
            if os.name != 'posix':
                self.monitor_mode_active = False
                
        except Exception as e:
            print(f"Error checking monitor mode: {e}")
            self.monitor_mode_active = False
    
    # Run a command in background thread and update UI when done
    def run_command_async(self, command, on_complete=None):
        """Run a command asynchronously and call on_complete when done"""
        def run_in_thread():
            try:
                # Disable button while command is running
                self.monitor_btn.config(state=tk.DISABLED)
                result = subprocess.run(command, capture_output=True, text=True)
                
                # Wait a moment for interface changes to register
                time.sleep(1)
                
                # Re-enable button
                self.monitor_btn.config(state=tk.NORMAL)
                
                # Call the callback with the result
                if on_complete:
                    self.root.after(0, lambda: on_complete(result))
            except Exception as e:
                print(f"Error running command: {e}")
                # Re-enable button
                self.root.after(0, lambda: self.monitor_btn.config(state=tk.NORMAL))
        
        # Start the command in a separate thread
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True
        thread.start()
    
    # Navigation function
    def show_frame(self, frame):
        for f in [self.main_frame, self.beacon_flooding_page, self.passive_recon_page]:
            f.place_forget()
        frame.place(relwidth=1, relheight=1)
    
    # Button panel creator function
    def create_button_panel(self, parent, text, y_pos, command, height=100):
        frame = tk.Frame(parent, bg=PANEL_BG)
        frame.place(x=20, y=y_pos, width=440, height=height)
        
        accent_left = tk.Frame(frame, width=5, bg=ACCENT_ORANGE)
        accent_left.pack(side=tk.LEFT, fill=tk.Y)
        
        button = HoverButton(frame, text=text, font=("Arial", 32, "bold"), fg=ACCENT_GOLD, bg=PANEL_BG, 
                          bd=0, activebackground=ACCENT_ORANGE, activeforeground="#FFFFFF",
                          command=command, height=height//20)
        button.pack(fill=tk.BOTH, expand=True, padx=10)
        
        accent_right = tk.Frame(frame, width=5, bg=ACCENT_ORANGE)
        accent_right.pack(side=tk.RIGHT, fill=tk.Y)
        
        return frame
    
    # Update monitor button appearance based on state
    def update_monitor_button(self):
        """Update monitor button text and color based on current state"""
        if self.monitor_mode_active:
            self.monitor_btn.config(text="Monitor Mode: On", fg=ACCENT_GOLD)
        else:
            self.monitor_btn.config(text="Monitor Mode: Off", fg=WARNING_COLOR)
        
        # Update default foreground color for proper hover behavior
        self.monitor_btn.update_default_colors()
    
    # Toggle monitor mode function
    def toggle_monitor_mode(self):
        """Toggle monitor mode between managed and monitor mode"""
        if not self.monitor_mode_active:
            # Start monitor mode
            self.run_command_async(
                ['sudo', 'airmon-ng', 'start', self.normal_interface],
                on_complete=lambda result: self.handle_monitor_toggle_result(True)
            )
        else:
            # Stop monitor mode
            self.run_command_async(
                ['sudo', 'airmon-ng', 'stop', self.monitor_interface],
                on_complete=lambda result: self.handle_monitor_toggle_result(False)
            )
    
    def handle_monitor_toggle_result(self, trying_to_enable):
        """Handle the result of toggling monitor mode"""
        # Check the actual state after the command
        self.check_monitor_mode_state()
        
        # Update the button appearance
        self.update_monitor_button()
        
        # Log the result for debugging
        state_text = "enabled" if self.monitor_mode_active else "disabled"
        intended_text = "enable" if trying_to_enable else "disable"
        print(f"Attempted to {intended_text} monitor mode. Current state: {state_text}")
        
        # If we're on Windows or non-Linux, simulate the state change
        if os.name != 'posix':
            self.monitor_mode_active = trying_to_enable
            self.update_monitor_button()
    
    # Page template creator 
    def setup_page_template(self, page, title_text):
        # Add time display
        page_time_label = tk.Label(page, text="00:00:00", font=("Arial", 16, "bold"),
                               bg=DARK_BG, fg=ACCENT_ORANGE)
        page_time_label.place(x=30, y=10)
        self.time_labels.append(page_time_label)
        
        # Add CPU temp display
        page_cpu_label = tk.Label(page, text="CPU Temp: N/A", font=("Arial", 16, "bold"),
                                 bg=DARK_BG, fg=ACCENT_ORANGE)
        page_cpu_label.place(x=250, y=10)
        self.cpu_temp_labels.append(page_cpu_label)
        
        # Create header with title and back button
        header = tk.Frame(page, bg=PANEL_BG, height=50)
        header.place(x=0, y=50, relwidth=1)
        
        # Add back button on the left side of title
        back_btn = HoverButton(header, text="< BACK", font=("Arial", 12, "bold"), 
                            fg=ACCENT_GOLD, bg=PANEL_BG,
                            bd=0, padx=15, pady=5, 
                            command=lambda: self.show_frame(self.main_frame))
        back_btn.pack(side=tk.LEFT, padx=10)
        
        # Title next to back button
        title = tk.Label(header, text=title_text, font=("Arial", 22, "bold"), 
                         fg=ACCENT_GOLD, bg=PANEL_BG)
        title.pack(side=tk.LEFT, padx=10)
        
        # Add content area
        content = tk.Frame(page, bg=PANEL_BG)
        content.place(x=20, y=110, width=440, height=500)
        
        return content
    
    def setup_ui(self):
        self.setup_main_page()
        self.setup_attack_pages()
    
    def setup_main_page(self):
        # Add time and CPU temp to main page
        main_time_label = tk.Label(self.main_frame, text="00:00:00", font=("Arial", 16, "bold"),
                               bg=DARK_BG, fg=ACCENT_ORANGE)
        main_time_label.place(x=30, y=10)
        self.time_labels.append(main_time_label)
        
        # Add CPU temp to main page
        main_cpu_label = tk.Label(self.main_frame, text="CPU Temp: N/A", font=("Arial", 16, "bold"),
                                 bg=DARK_BG, fg=ACCENT_ORANGE)
        main_cpu_label.place(x=250, y=10)
        self.cpu_temp_labels.append(main_cpu_label)
        
        # Create header
        header_frame = tk.Frame(self.main_frame, bg=PANEL_BG, height=70)
        header_frame.place(x=0, y=50, relwidth=1)
        
        head_title = tk.Label(header_frame, text="Melro WiFier v1.0", font=self.titlefont, 
                             fg=ACCENT_GOLD, bg=PANEL_BG)
        head_title.pack(pady=(5, 2))
        
        subtitle = tk.Label(header_frame, text="Network Penetration Testing Tool Project", 
                           font=("Arial", 14), fg=TEXT_COLOR, bg=PANEL_BG)
        subtitle.pack(pady=2)
        
        # --- Dynamic button layout ---
        header_bottom = 120
        bottom_buttons_height = 100
        bottom_buttons_y = 540
        
        spacing = 40 
        
        # Calculate available height for main buttons
        total_available_height = bottom_buttons_y - header_bottom
        total_spacing = spacing * 3 
        available_height = total_available_height - total_spacing
        button_height = int(available_height / 2) 
        
        # First main button
        first_button = self.create_button_panel(self.main_frame, "Passive Recon", 
                                              header_bottom + spacing, 
                                              lambda: self.show_frame(self.passive_recon_page),
                                              height=button_height)
        
        # Second main button
        second_button = self.create_button_panel(self.main_frame, "Beacon Flooding", 
                                               header_bottom + spacing + button_height + spacing, 
                                               lambda: self.show_frame(self.beacon_flooding_page),
                                               height=button_height)
        
        # Monitor Mode button (left)
        monitor_frame = tk.Frame(self.main_frame, bg=PANEL_BG, height=bottom_buttons_height)
        monitor_frame.place(x=20, y=bottom_buttons_y, width=270)
        monitor_left_accent = tk.Frame(monitor_frame, width=5, bg=ACCENT_ORANGE)
        monitor_left_accent.pack(side=tk.LEFT, fill=tk.Y)
        initial_text = "Monitor Mode: On" if self.monitor_mode_active else "Monitor Mode: Off"
        initial_color = ACCENT_GOLD if self.monitor_mode_active else WARNING_COLOR
        self.monitor_btn = HoverButton(monitor_frame, text=initial_text, font=self.cyberfont, 
                                   fg=initial_color, bg=PANEL_BG, bd=0, pady=15,
                                   command=self.toggle_monitor_mode)
        self.monitor_btn.pack(fill=tk.BOTH, expand=True, padx=10)
        monitor_right_accent = tk.Frame(monitor_frame, width=5, bg=ACCENT_ORANGE)
        monitor_right_accent.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Exit button (right)
        exit_frame = tk.Frame(self.main_frame, bg=PANEL_BG, height=bottom_buttons_height)
        exit_frame.place(x=300, y=bottom_buttons_y, width=160)
        exit_left_accent = tk.Frame(exit_frame, width=5, bg=ACCENT_ORANGE)
        exit_left_accent.pack(side=tk.LEFT, fill=tk.Y)
        exit_btn = HoverButton(exit_frame, text="EXIT", font=self.cyberfont, 
                           fg=WARNING_COLOR, bg=PANEL_BG, bd=0, pady=15,
                            command=lambda: self.root.quit())
        exit_btn.pack(fill=tk.BOTH, expand=True, padx=10)
        exit_right_accent = tk.Frame(exit_frame, width=5, bg=ACCENT_ORANGE)
        exit_right_accent.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_attack_pages(self):
        # Setup attack page templates
        beacon_content = self.setup_page_template(self.beacon_flooding_page, "Beacon Flooding")
        passive_recon_content = self.setup_page_template(self.passive_recon_page, "Passive Recon")
        
        # Initialize attack UIs within their content areas
        self.beacon_flooding_attack.setup_ui(beacon_content)
        self.passive_recon.setup_ui(passive_recon_content)
    
    def update_time(self):
        current_time = time.strftime("%H:%M:%S")
        for label in self.time_labels:
            label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def update_cpu_temp(self):
        try:
            temp_file_path = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_file_path):
                with open(temp_file_path, "r") as temp_file:
                    temp = int(temp_file.read()) / 1000
                for label in self.cpu_temp_labels:
                    label.config(text=f"CPU Temp: {temp}°C")
                    # Change color based on temperature
                    if temp > 70:
                        label.config(fg=WARNING_COLOR)
                    elif temp > 60:
                        label.config(fg="#FFAA00")
                    else:
                        label.config(fg=ACCENT_ORANGE)
            else:
                for label in self.cpu_temp_labels:
                    label.config(text="CPU Temp: N/A")
                    label.config(fg=ACCENT_ORANGE)
        except Exception as e:
            for label in self.cpu_temp_labels:
                label.config(text="CPU Temp: N/A")
                label.config(fg=ACCENT_ORANGE)
            print(f"Error reading CPU temperature: {e}")
        self.root.after(1000, self.update_cpu_temp)

# Run the application
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MelroApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 