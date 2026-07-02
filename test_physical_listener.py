import json
import time
import network
import uasyncio
from listeners.telegram import TelegramListener

def connect_wifi(ssid, password):
    """Establish a physical Wi-Fi connection on the ESP32."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Connecting to Wi-Fi SSID: {ssid}...")
        wlan.connect(ssid, password)
        
        # Connect timeout of 15 seconds
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            
    if wlan.isconnected():
        print("Wi-Fi Connected! IP Config:", wlan.ifconfig())
        return True
    else:
        print("Error: Wi-Fi connection timed out.")
        return False

async def on_note_received(note):
    """Callback triggered whenever the listener parses an incoming message."""
    print("\n==========================================")
    print("          📩 NEW RAW NOTE RECEIVED        ")
    print("==========================================")
    print(f"Title:     {note.title}")
    print(f"Type:      {note.note_type}")
    print("Content:")
    
    # Check if content is photo binary data
    if isinstance(note.content, bytes):
        print(f"[Photo Binary Data: {len(note.content)} bytes]")
    else:
        print(note.content)
    print("==========================================\n")

async def main():
    # 1. Load config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        print("Error: Could not read config.json. Make sure it exists on the ESP32.")
        return

    # 2. Connect to the network
    ssid = config.get("wifi_ssid")
    password = config.get("wifi_password")
    token = config.get("telegram_token")

    if not ssid or not password or not token:
        print("Error: Please fill in wifi_ssid, wifi_password, and telegram_token in config.json.")
        return

    if not connect_wifi(ssid, password):
        return

    # 3. Start the non-blocking Telegram Listener
    listener = TelegramListener(token, on_note_received)
    
    print("\nTelegram Bot Polling started!")
    print("Send a message or a photo to your bot now...")
    
    try:
        await listener.listen()
    except KeyboardInterrupt:
        listener.stop()
        print("Listener stopped.")

if __name__ == "__main__":
    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest terminated.")
