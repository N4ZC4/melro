import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import os
import tempfile
import re

# Change to relative import for better module resolution
from .utils import DARK_BG, PANEL_BG, TEXT_COLOR, ACCENT_GOLD, WARNING_COLOR, STATUS_GREEN, BTN_BG, BTN_TEXT, HoverButton

class PassiveRecon:
    def __init__(self, root=None, return_callback=None):
        self.root = root
        self.return_callback = return_callback
        self.scanning = False
        self.attacking = False
        self.selected_network = None
        self.selected_channel = None
        self.attack_process = None
        self.temp_file_path = None
        
    def setup_ui(self, parent_frame):
        """Setup the UI components for Passive Recon page."""
        # The page template from main.py already adds the time, CPU temp, and back button
        
        self.scan_btn = HoverButton(
            parent_frame, 
            text="Scan Networks", 
            font=("Arial", 14, "bold"),
            bg=PANEL_BG, 
            fg=ACCENT_GOLD, 
            bd=0, 
            padx=20, 
            pady=15,
            command=self.start_scan
        )
        self.scan_btn.place(x=20, y=20, width=190, height=60)
        
        # Create choose button with larger font and padding (half size on right)
        self.choose_btn = HoverButton(
            parent_frame, 
            text="Choose", 
            font=("Arial", 14, "bold"),
            bg=PANEL_BG, 
            fg=ACCENT_GOLD, 
            bd=0, 
            padx=20, 
            pady=15,
            state=tk.DISABLED,
            command=self.choose_network
        )
        self.choose_btn.place(x=230, y=20, width=190, height=60)
        
        # Status message
        self.status_label = tk.Label(
            parent_frame, 
            text="Click Scan to find nearby networks", 
            font=("Arial", 12),
            bg=PANEL_BG, 
            fg=TEXT_COLOR,
            wraplength=380 
        )
        self.status_label.place(x=20, y=90, width=400, height=30)
        
        # Network selection section
        selection_frame = tk.Frame(parent_frame, bg=PANEL_BG)
        selection_frame.place(x=10, y=125, width=420, height=300)
        
        # Label for network list
        self.network_label = tk.Label(
            selection_frame, 
            text="Available Networks:", 
            font=("Arial", 14, "bold"),
            bg=PANEL_BG, 
            fg=ACCENT_GOLD, 
            anchor="w"
        )
        self.network_label.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(10, 5))
        
        # Frame for the listbox with scrollbar
        list_frame = tk.Frame(selection_frame, bg=PANEL_BG)
        list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame, width=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Networks listbox
        self.network_listbox = tk.Listbox(
            list_frame,
            bg="#2A2A2A",
            fg=TEXT_COLOR,
            selectbackground=ACCENT_GOLD,
            selectforeground="#000000",
            font=("Arial", 12),
            bd=0,
            highlightthickness=0,
            activestyle="none"
        )
        self.network_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar Configuration
        scrollbar.config(command=self.network_listbox.yview)
        self.network_listbox.config(yscrollcommand=scrollbar.set)
        
        # Attack button
        self.attack_btn = HoverButton(
            parent_frame,
            text="Start Recon",
            font=("Arial", 16, "bold"),
            bg=PANEL_BG,
            fg=ACCENT_GOLD,
            bd=0,
            padx=20,
            pady=15,
            state=tk.DISABLED,
            command=self.start_attack
        )
        self.attack_btn.place(x=20, y=435, width=400, height=60)
        
        # Bind selection event
        self.network_listbox.bind("<<ListboxSelect>>", self.on_selection)
        
    def start_scan(self):
        """Start scanning for networks"""
        if self.scanning:
            return
            
        self.scanning = True
        self.scan_btn.config(state=tk.DISABLED)
        self.network_listbox.delete(0, tk.END)
        self.status_label.config(text="Scanning for networks...")
        self.network_label.config(text="Available Networks:")
        
        # Reset selection
        self.selected_network = None
        self.selected_channel = None
        self.choose_btn.config(state=tk.DISABLED)
        self.attack_btn.config(state=tk.DISABLED)
        
        # Start scan in background thread
        threading.Thread(target=self.run_scan, daemon=True).start()
        
    def run_scan(self):
        """Run the network scan using airodump-ng"""
        try:
            # Run airodump-ng to scan for networks
            process = subprocess.Popen(
                ["sudo", "airodump-ng", "wlan1mon", "--output-format", "csv", "-w", "temp_scan"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for 5 seconds to collect data
            time.sleep(5)
            process.terminate()
            
            # Read the CSV file
            with open("temp_scan-01.csv", "r") as f:
                lines = f.readlines()
            
            # Parse network data
            networks = []
            for line in lines:
                if "," in line and "BSSID" not in line and "Station" not in line:
                    parts = line.strip().split(",")
                    if len(parts) >= 14:
                        bssid = parts[0].strip()
                        channel = parts[3].strip()
                        signal = parts[8].strip()
                        ssid = parts[13].strip()
                        if bssid and ssid:
                            networks.append((ssid, bssid, channel, signal))
            
            # Update UI with found networks
            self.root.after(0, self.update_network_list, networks)
            
        except Exception as e:
            self.root.after(0, self.handle_scan_error, str(e))
        finally:
            # Clean up
            try:
                os.remove("temp_scan-01.csv")
            except:
                pass
            self.scanning = False
            self.root.after(0, self.scan_btn.config, {"state": tk.NORMAL})
            
    def update_network_list(self, networks):
        """Update the network list with found networks"""
        self.network_listbox.delete(0, tk.END)
        for network in networks:
            self.network_listbox.insert(tk.END, f"{network[0]} ({network[1]}) - Ch:{network[2]}")
        self.status_label.config(text=f"Found {len(networks)} networks")
        
    def handle_scan_error(self, error):
        """Handle scan errors"""
        self.status_label.config(text=f"Scan error: {error}")
        
    def on_selection(self, event):
        """Handle selection in the list window"""
        selection = self.network_listbox.curselection()
        if not selection:
            return
            
        # If we're in attack mode, don't do anything with the selection
        if self.attacking:
            return
            
        selected_text = self.network_listbox.get(selection[0])
        # Extract BSSID and channel from the selected text
        bssid = selected_text[selected_text.find("(")+1:selected_text.find(")")]
        channel = selected_text[selected_text.find("Ch:")+3:].strip()
        
        self.selected_network = bssid
        self.selected_channel = channel
        
        self.status_label.config(text=f"Selected network: {selected_text}")
        self.choose_btn.config(state=tk.NORMAL)
        
    def choose_network(self):
        """Export the selected network info to a temp file"""
        if not self.selected_network or not self.selected_channel:
            messagebox.showwarning("Selection Required", "Please select a network first")
            return
        
        try:
            # Create a temp file to store the selected network info
            self.network_info_file = tempfile.mktemp(prefix="network_info_")
            with open(self.network_info_file, "w") as f:
                f.write(f"BSSID: {self.selected_network}\n")
                f.write(f"Channel: {self.selected_channel}\n")
            
            # Update status and enable attack button
            self.status_label.config(text=f"Network selected: {self.selected_network} on channel {self.selected_channel}")
            self.attack_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save network info: {e}")
            print(f"Error creating temp file: {e}")
        
    def start_attack(self):
        """Start the passive reconnaissance"""
        if not hasattr(self, 'network_info_file') or not os.path.exists(self.network_info_file):
            messagebox.showwarning("Selection Required", "Please choose a network first")
            return
            
        if not self.attacking:
            # Start the attack
            self.attacking = True
            self.attack_btn.config(text="Stop Recon", command=self.stop_attack)
            self.scan_btn.config(state=tk.DISABLED)
            self.choose_btn.config(state=tk.DISABLED)
            self.network_listbox.config(state=tk.NORMAL)  # Keep it enabled to scroll through results
            self.status_label.config(text="Running passive reconnaissance...")
            
            # Update the network label
            self.network_label.config(text="Reconnaissance Results:")
            
            # Start attack in background thread
            threading.Thread(target=self.run_attack, daemon=True).start()
        else:
            # Stop the attack
            self.stop_attack()
        
    def run_attack(self):
        """Run the passive reconnaissance using airodump-ng"""
        try:
            # Create a unique output file for results
            self.output_file = tempfile.mktemp(prefix="recon_")
            
            # Clear the listbox to display new results
            self.root.after(0, self.network_listbox.delete, 0, tk.END)
            self.root.after(0, lambda: self.network_listbox.insert(tk.END, f"Starting monitoring on {self.selected_network} (Ch:{self.selected_channel})..."))
            
            # Update UI with status
            self.root.after(0, self.status_label.config, 
                           {"text": f"Monitoring network on channel {self.selected_channel}..."})
            
            # Run airodump-ng with specific BSSID and channel
            self.attack_process = subprocess.Popen(
                ["sudo", "airodump-ng", "--bssid", self.selected_network, 
                 "-c", self.selected_channel, "--output-format", "csv",
                 "-w", self.output_file, "wlan1mon"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait a moment for the CSV file to be created
            time.sleep(2)
            
            # Set the path to the CSV file
            self.csv_file_path = f"{self.output_file}-01.csv"
            
            # Start reading data periodically
            self.read_csv_data()
            
        except Exception as e:
            self.root.after(0, self.handle_attack_error, str(e))
            
    def read_csv_data(self):
        """Read reconnaissance data from the CSV file"""
        if not self.attacking:
            return
            
        try:
            if os.path.exists(self.csv_file_path):
                try:
                    with open(self.csv_file_path, "r", errors="ignore") as f:
                        content = f.read()
                    
                    # Clear the listbox and add the new data
                    self.network_listbox.delete(0, tk.END)
                    
                    # Parse the CSV content to show meaningful data
                    sections = content.split("\n\n")
                    stations = []
                    network_essid = None

                    # Find our target network first
                    if len(sections) >= 1:
                        network_section = sections[0].split("\n")
                        for line in network_section:
                            if self.selected_network in line and "," in line:
                                parts = line.split(',')
                                if len(parts) >= 14:
                                    essid = parts[13].strip()
                                    network_essid = essid if essid else "Hidden Network"
                    
                    # Find connected clients in stations section
                    if len(sections) >= 2:
                        station_section = sections[1].split("\n")
                        inside_station_data = False
                        
                        for line in station_section:
                            # Find the start of station data
                            if "Station MAC" in line:
                                inside_station_data = True
                                continue
                                
                            # Process each station entry
                            if inside_station_data and line.strip() and "," in line:
                                parts = line.split(',')
                                if len(parts) >= 5:
                                    mac = parts[0].strip()
                                    # Check if this client is connected to our target network
                                    connected_to = parts[5].strip() if len(parts) > 5 else ""
                                    
                                    # Include clients with no BSSID (they might be connected)
                                    if mac and (not connected_to or self.selected_network in connected_to):
                                        power = parts[3].strip()
                                        packets = parts[4].strip()
                                        
                                        # Display just the MAC and signal info without "Client:" prefix
                                        client_info = f"{mac} (Signal: {power}, Packets: {packets})"
                                        stations.append(client_info)
                                        
                                        # Add probe requests if available
                                        if len(parts) > 6:
                                            probes = [p.strip() for p in parts[6:] if p.strip()]
                                            if probes:
                                                probe_str = ", ".join(probes)
                                                stations.append(f"  Probes: {probe_str}")
                    
                    # Add just the network ESSID at the top
                    if network_essid:
                        self.network_listbox.insert(tk.END, f"Network: {network_essid}")
                        self.network_listbox.insert(tk.END, "")
                        self.network_listbox.insert(tk.END, "--- Connected Clients ---")
                        self.network_listbox.insert(tk.END, "")
                    
                    # Debug info - print the raw stations section to console
                    if len(sections) >= 2:
                        print(f"Station section found with {len(sections[1].split(self.selected_network))-1} mentions of target network")
                    
                    # Add stations information
                    if stations:
                        for station in stations:
                            self.network_listbox.insert(tk.END, station)
                    else:
                        # Try a more aggressive approach to find clients
                        found_any = False
                        for line in content.split('\n'):
                            if self.selected_network in line and "Station MAC" not in line and "BSSID" not in line:
                                parts = line.split(',')
                                if len(parts) >= 1 and parts[0].strip():
                                    # This might be a client MAC address
                                    mac = parts[0].strip()
                                    if re.match(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', mac, re.I):
                                        found_any = True
                                        power = parts[3].strip() if len(parts) > 3 else "N/A"
                                        # Display just the MAC without "Client:" prefix
                                        self.network_listbox.insert(tk.END, f"{mac} (Signal: {power})")
                        
                        if not found_any:
                            self.network_listbox.insert(tk.END, "No clients currently connected")
                    
                    # Ensure UI is updated immediately
                    self.network_listbox.update_idletasks()
                    self.network_listbox.see(0)  # Scroll to top
                    
                except Exception as e:
                    print(f"Error parsing CSV data: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                # File doesn't exist yet, just wait
                print(f"Waiting for CSV file: {self.csv_file_path}")
            
            # Schedule next read if still attacking
            if self.attacking:
                self.root.after(1000, self.read_csv_data)  # Check more frequently
                
        except Exception as e:
            print(f"Error reading CSV data: {e}")
            if self.attacking:
                self.root.after(2000, self.read_csv_data)
            
    def stop_attack(self):
        """Stop the passive reconnaissance"""
        if self.attack_process:
            self.attack_process.terminate()
            self.attack_process = None
            
        self.attacking = False
        self.attack_btn.config(text="Start Recon", command=self.start_attack)
        self.scan_btn.config(state=tk.NORMAL)
        self.choose_btn.config(state=tk.DISABLED)  # Disable Choose until new selection
        self.network_listbox.config(state=tk.NORMAL)
        self.network_label.config(text="Available Networks:")
        self.status_label.config(text="Reconnaissance stopped")
        
        # Clear the listbox
        self.network_listbox.delete(0, tk.END)
        
        # Clean up temporary files
        try:
            if hasattr(self, 'csv_file_path') and os.path.exists(self.csv_file_path):
                os.remove(self.csv_file_path)
                delattr(self, 'csv_file_path')
                
            if hasattr(self, 'output_file') and os.path.exists(f"{self.output_file}-01.csv"):
                os.remove(f"{self.output_file}-01.csv")
                delattr(self, 'output_file')
                
            if hasattr(self, 'network_info_file') and os.path.exists(self.network_info_file):
                os.remove(self.network_info_file)
                delattr(self, 'network_info_file')
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
        
    def handle_attack_error(self, error):
        """Handle attack errors"""
        self.status_label.config(text=f"Recon error: {error}")
        self.stop_attack()
        
# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("480x640")
    root.configure(bg=DARK_BG)
    
    frame = tk.Frame(root, bg=PANEL_BG, width=440, height=400)
    frame.pack(pady=100)
    
    recon = PassiveRecon(root)
    recon.setup_ui(frame)
    
    root.mainloop() 