"""Telegram Long Polling Note Listener.

Fetches text and photo messages from a Telegram bot asynchronously using aiohttp
ClientSession and maps them to RawNote DTOs.
"""

import json
import sys
import uasyncio
import aiohttp
from listeners.base import BaseListener
from core.models import RawNote

def print_exception(e):
    """Print exception traceback. Handles MicroPython vs standard Python compatibility."""
    if hasattr(sys, 'print_exception'):
        sys.print_exception(e)
    else:
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)


class TelegramListener(BaseListener):
    """Listener that polls the Telegram Bot API for incoming print jobs."""

    def __init__(self, token, callback):
        """Initialize the Telegram listener.

        Args:
            token (str): The Telegram Bot API token.
            callback (callable): The async callback to hand off parsed RawNotes.
        """
        super().__init__(callback)
        self.token = token
        self.offset = 0
        self.session = None  # Persistent aiohttp session reused across polls

    async def listen(self):
        """Start the async long polling loop with a persistent ClientSession."""
        self.is_listening = True
        print("TelegramListener: Polling loop started.")

        try:
            # Establish a persistent session to enable connection pooling (reuses SSL handshake)
            async with aiohttp.ClientSession() as session:
                self.session = session
                
                while self.is_listening:
                    try:
                        # Perform long polling request
                        updates = await self._api_request("getUpdates", {
                            "offset": self.offset,
                            "timeout": 30,
                            "allowed_updates": ["message"]
                        })

                        if updates and updates.get("ok"):
                            for update in updates.get("result", []):
                                # Track offset to avoid fetching duplicates
                                self.offset = update["update_id"] + 1
                                
                                message = update.get("message")
                                if message:
                                    await self._handle_message(message)
                        
                    except uasyncio.CancelledError:
                        print("TelegramListener: Loop cancelled.")
                        break
                    except Exception as e:
                        print("TelegramListener: Error in updates polling:")
                        print_exception(e)
                        # Network backoff: pause to allow connection issues to resolve
                        await uasyncio.sleep(5)
        finally:
            self.session = None

        print("TelegramListener: Polling loop stopped and session closed.")

    async def _handle_message(self, message):
        """Parse incoming Telegram message and trigger pipeline callback."""
        try:
            text = message.get("text")
            photo = message.get("photo")

            if text:
                text = text.strip()
                # Simple parser routing based on prefix / content rules
                if text.startswith("/todo"):
                    clean_text = text[5:].strip()
                    note = RawNote(
                        content=clean_text,
                        title="Todo List",
                        note_type="short_term"
                    )
                else:
                    lines = text.split("\n")
                    if len(lines) > 1:
                        title = lines[0]
                        content = "\n".join(lines[1:])
                    else:
                        title = None
                        content = text
                        
                    note = RawNote(
                        content=content,
                        title=title,
                        note_type="misc"
                    )
                
                print(f"TelegramListener: Received text note (Type: {note.note_type})")
                await self.callback(note)

            elif photo:
                # Telegram photo list contains multiple resolution variants; get the largest
                largest_photo = photo[-1]
                file_id = largest_photo["file_id"]
                
                print("TelegramListener: Fetching photo path...")
                file_info = await self._api_request("getFile", {"file_id": file_id})
                
                if file_info and file_info.get("ok"):
                    file_path = file_info["result"].get("file_path")
                    if file_path:
                        print("TelegramListener: Downloading photo binary data...")
                        photo_data = await self._download_file(file_path)
                        
                        note = RawNote(
                            content=photo_data,
                            title="Image Note",
                            note_type="misc"
                        )
                        print("TelegramListener: Received photo note")
                        await self.callback(note)
                        
        except Exception as e:
            print("TelegramListener: Failed to parse/process message:")
            print_exception(e)

    async def _api_request(self, method_name, params=None):
        """Perform a non-blocking request to the Telegram API using the persistent session.

        Args:
            method_name (str): Telegram API endpoint method.
            params (dict, optional): Payload parameters to encode in JSON.

        Returns:
            dict: Parsed API JSON response.
        """
        if not self.session:
            raise RuntimeError("TelegramListener: ClientSession is not initialized.")

        url = f"https://api.telegram.org/bot{self.token}/{method_name}"
        headers = {"Content-Type": "application/json"}
        body = json.dumps(params) if params else None

        # Modern context manager automatically handles socket lifecycle and closing
        async with self.session.post(url, data=body, headers=headers) as resp:
            raw_body = await resp.read()
            if resp.status != 200:
                body_str = raw_body.decode('utf-8', 'replace')
                raise RuntimeError(f"HTTP response error: {resp.status}. Body: {body_str}")
            
            # json.loads directly accepts bytes in Python 3/MicroPython, saving a string copy
            return json.loads(raw_body)

    async def _download_file(self, file_path):
        """Asynchronously download a file from the Telegram servers using the persistent session.

        Args:
            file_path (str): Relative file path returned by getFile.

        Returns:
            bytes: Downloaded file binary bytes.
        """
        if not self.session:
            raise RuntimeError("TelegramListener: ClientSession is not initialized.")

        url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"

        # Clean context manager approach, chunked transfer decoding is handled natively by aiohttp
        async with self.session.get(url) as resp:
            raw_body = await resp.read()
            if resp.status != 200:
                raise RuntimeError(f"HTTP response error downloading file: {resp.status}")
            
            return raw_body