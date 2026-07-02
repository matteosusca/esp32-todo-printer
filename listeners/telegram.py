"""Telegram Long Polling Note Listener.

Fetches text and photo messages from a Telegram bot asynchronously and maps
them to RawNote DTOs.
"""

import json
import sys
import uasyncio
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

    async def listen(self):
        """Start the async long polling loop."""
        self.is_listening = True
        print("TelegramListener: Polling loop started.")

        while self.is_listening:
            try:
                # Perform long polling request (timeout parameter keeps it open on server side)
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

        print("TelegramListener: Polling loop stopped.")

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
        """Perform a non-blocking SSL request to the Telegram API.

        Args:
            method_name (str): Telegram API endpoint method.
            params (dict, optional): Payload parameters to encode in JSON.

        Returns:
            dict: Parsed API JSON response.
        """
        host = "api.telegram.org"
        path = f"/bot{self.token}/{method_name}"
        body = json.dumps(params) if params else ""

        # Open non-blocking SSL socket connection
        reader, writer = await uasyncio.open_connection(host, 443, ssl=True)
        try:
            # Build standard HTTP/1.1 POST request
            headers = [
                f"POST {path} HTTP/1.1",
                f"Host: {host}",
                "Connection: close",
                "Content-Type: application/json",
                f"Content-Length: {len(body)}"
            ]
            request = "\r\n".join(headers) + "\r\n\r\n" + body
            
            writer.write(request.encode('utf-8'))
            await writer.drain()

            # Read whole HTTP response stream
            response_bytes = bytearray()
            while True:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                response_bytes.extend(chunk)

            parts = response_bytes.split(b"\r\n\r\n", 1)
            if len(parts) < 2:
                raise ValueError("Malformed HTTP response")

            header, body_content = parts[0], parts[1]
            status_line = header.split(b"\r\n", 1)[0].decode('utf-8')
            
            if "200 OK" not in status_line:
                raise RuntimeError(f"HTTP response error: {status_line}. Body: {body_content.decode('utf-8')}")

            return json.loads(body_content.decode('utf-8'))

        finally:
            writer.close()
            if hasattr(writer, 'wait_closed'):
                try:
                    await writer.wait_closed()
                except:
                    pass

    async def _download_file(self, file_path):
        """Asynchronously download a file from the Telegram servers.

        Args:
            file_path (str): Relative file path returned by getFile.

        Returns:
            bytes: Downloaded file binary bytes.
        """
        host = "api.telegram.org"
        path = f"/file/bot{self.token}/{file_path}"

        reader, writer = await uasyncio.open_connection(host, 443, ssl=True)
        try:
            headers = [
                f"GET {path} HTTP/1.1",
                f"Host: {host}",
                "Connection: close"
            ]
            request = "\r\n".join(headers) + "\r\n\r\n"
            
            writer.write(request.encode('utf-8'))
            await writer.drain()

            response_bytes = bytearray()
            while True:
                chunk = await reader.read(1024)
                if not chunk:
                    break
                response_bytes.extend(chunk)

            parts = response_bytes.split(b"\r\n\r\n", 1)
            if len(parts) < 2:
                raise ValueError("Malformed HTTP response")

            header, body_content = parts[0], parts[1]
            status_line = header.split(b"\r\n", 1)[0].decode('utf-8')

            if "200 OK" not in status_line:
                raise RuntimeError(f"HTTP response error downloading file: {status_line}")

            return bytes(body_content)

        finally:
            writer.close()
            if hasattr(writer, 'wait_closed'):
                try:
                    await writer.wait_closed()
                except:
                    pass
