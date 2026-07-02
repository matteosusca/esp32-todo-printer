import json
import uasyncio
from machine import UART
from core.app import App
from core.dispatcher import Dispatcher
from hardware.printer import PrintWorker
from listeners.telegram import TelegramListener

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
    if not config or "telegram_token" not in config:
        print("Error: Configuration could not be loaded or missing telegram_token.")
        return

    # 1. Initialize UART for the thermal printer
    uart = UART(1, baudrate=9600, tx=18, rx=17)

    # 2. Initialize App, Dispatcher, and PrintWorker
    app = App()
    dispatcher = Dispatcher()
    worker = PrintWorker(uart, app.print_queue)

    # 3. Start background PrintWorker task
    worker_task = uasyncio.create_task(worker.run())

    # 4. Pipeline Callback: Listener -> Dispatcher -> Queue
    async def on_raw_note(raw_note):
        print("Main: Raw note received from listener. Dispatching...")
        print_job = dispatcher.dispatch(raw_note)
        await app.add_job(print_job)
        print("Main: PrintJob enqueued.")

    # 5. Initialize and run Telegram Listener
    token = config["telegram_token"]
    listener = TelegramListener(token, on_raw_note)

    print("Application initialized. Ready for Telegram messages!")
    
    try:
        await listener.listen()
    except uasyncio.CancelledError:
        print("Main: Shutting down...")
    finally:
        worker.stop()
        await worker_task

if __name__ == '__main__':
    try:
        uasyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
