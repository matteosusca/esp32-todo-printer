import json
import uasyncio
from machine import UART
from core.app import App

def load_config():
    """Load configuration from config.json."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading config.json in main:", e)
        return None

async def main():
    config = load_config()
    if not config:
        print("Error: Configuration could not be loaded.")
        return

    # Initialize UART for the thermal printer
    uart = UART(1, baudrate=9600, tx=18, rx=17)

    # Initialize the App manager
    app = App()

    print("Application initialized. Ready for listeners, drawers, and workers.")

    # Keep-alive loop
    while True:
        await uasyncio.sleep(3600)

if __name__ == '__main__':
    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
