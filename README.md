# Melro WiFier v1.0
Lightweight Wi-Fi penetration testing project for educational and research purposes using a Raspberry Pi.
![WhatsApp Image 2025-06-04 at 09 58 25](https://github.com/user-attachments/assets/276c7012-e79a-47e0-b34f-91aa3fb73931)

# Run
Start with "python3 main.py" in a root terminal

# Python Dependencies
tkinter    | Usually comes with Python installation  
subprocess | Part of Python standard library  
threading  | Part of Python standard library  
tempfile   | Part of Python standard library  
re         | Part of Python standard library  

# Required Linux Tools (for Raspberry Pi)
airmon-ng    | Part of aircrack-ng suite  
airodump-ng  | Part of aircrack-ng suite  
iwconfig     | Part of wireless-tools  
iw           | Part of iw package  

# Installation Commands for Required Tools:
sudo apt-get update
sudo apt-get install aircrack-ng wireless-tools iw

Note: This project requires root/sudo privileges to run network tools  
Note: The wireless interface must support monitor mode  
Note: Some features may require specific hardware capabilities 
