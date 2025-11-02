📡 LAN Surveillance System
A self-contained, LAN-only surveillance platform built for educational and forensic simulation. Designed to run on Raspberry Pi or Ubuntu, this system captures and relays camera feeds with timestamped overlays, local logging, and modular expansion support.

🔧 Features
🎥 Real-time camera feed via Flask + OpenCV

🧠 Local-only IP logging, browser fingerprinting, and timestamp capture

🔊 Sound alerts and overlay triggers (stored in static/sounds)

🗂️ Modular folder structure for assets, logs, and future expansions

🛡️ No internet dependencies — fully LAN-contained

🚀 Setup Instructions
bash
# Clone the repo
git clone git@github.com:catgamer19/lan_surveillance_system.git
cd lan_surveillance_system

# (Optional) Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the Flask server
python app.py
🧪 Simulation Modes
test_mode.py (optional): triggers dummy events for overlay testing

demo_launcher.sh: launches camera feed with timestamp overlays and sound alerts

📁 Folder Structure
Code
lan_surveillance_system/
├── static/
│   └── sounds/         # Audio alerts for overlays
├── templates/          # HTML views (if used)
├── app.py              # Main Flask app
├── README.md           # This file
└── requirements.txt    # Python dependencies
🧠 Notes
All data is stored locally for forensic simulation

No cloud, no external APIs — pure LAN realism

Designed for Raspberry Pi deployment, but runs on Ubuntu as well
