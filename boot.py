import network
import time
import json

def load_config():
    """Load configuration from a JSON file."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading config.json:", e)
        return None

def connect_wifi(ssid, password):
    """Connect to a Wi-Fi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print('Connecting to network:', ssid)
        wlan.connect(ssid, password)
        
        # Wait for connection with a timeout
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")
    
    if wlan.isconnected():
        print("\nConnected to Wi-Fi")
        print('Network config:', wlan.ifconfig())
    else:
        print("\nFailed to connect to Wi-Fi")

# --- Boot sequence ---
print("Booting...")
config = load_config()

if config:
    connect_wifi(config['wifi_ssid'], config['wifi_password'])
else:
    print("No valid configuration found. Please check config.json.")