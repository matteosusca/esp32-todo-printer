"""UART printer interaction, flow control, and PrintWorker task.

This module manages sending raw ESC/POS bytes to the thermal printer
over serial UART, avoiding buffer saturation using rate-limiting,
and handling background job queue processing.
"""

import sys
import uasyncio

def print_exception(e):
    """Print exception traceback. Handles MicroPython vs standard Python compatibility."""
    if hasattr(sys, 'print_exception'):
        sys.print_exception(e)
    else:
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)


class PrintWorker:
    """Worker task that dequeues print jobs and writes their bytes to the printer UART.

    Maintains controlled pacing to prevent buffer saturation on the thermal printer.
    """

    def __init__(self, uart, app, chunk_size=64, delay_ms=20):
        """Initialize the PrintWorker.

        Args:
            uart (machine.UART): The initialized UART peripheral.
            app (core.app.App): The main application instance containing the print queue.
            chunk_size (int): Max chunk size (bytes) to write to UART in a single call.
            delay_ms (int): Delay in milliseconds between consecutive chunk writes.
        """
        self.uart = uart
        self.app = app
        self.chunk_size = chunk_size
        self.delay_ms = delay_ms
        self.is_running = False

    async def run(self):
        """Start the background printing worker loop.

        Blocks and pulls PrintJob objects from the queue, then prints them.
        """
        self.is_running = True
        print("PrintWorker loop started.")

        while self.is_running:
            try:
                # Dequeue next job (blocks until a job is available)
                job = await self.app.get_job()
                
                print("PrintWorker: Dequeued a new print job.")
                await self.process_job(job)
                
            except uasyncio.CancelledError:
                print("PrintWorker: Loop cancelled.")
                break
            except Exception as e:
                print("PrintWorker: Error in run loop:")
                print_exception(e)
                # Graceful failure: Backoff to prevent spamming errors in case of persistent failure
                await uasyncio.sleep(1)

        print("PrintWorker loop stopped.")

    async def process_job(self, job):
        """Process and format a single PrintJob.

        Supports both static bytes/strings and dynamic generators (for line-by-line streaming).

        Args:
            job (core.models.PrintJob): The job to print.
        """
        try:
            data = job.data

            # Check static types first (since bytes/str are also technically iterable)
            if isinstance(data, (bytes, bytearray)):
                await self._write_to_uart(data)
            elif isinstance(data, str):
                await self._write_to_uart(data.encode('utf-8'))
            # Check if it is a generator or an iterable stream
            elif hasattr(data, '__next__') or hasattr(data, '__iter__'):
                for row_chunk in data:
                    if not self.is_running:
                        break
                    
                    if isinstance(row_chunk, (bytes, bytearray)):
                        await self._write_to_uart(row_chunk)
                    elif isinstance(row_chunk, str):
                        await self._write_to_uart(row_chunk.encode('utf-8'))
                    else:
                        print("PrintWorker Warning: Skipped non-byte/non-string chunk in generator stream.")
            else:
                raise TypeError("PrintJob data must be bytes, string, or a generator/iterable yielding them.")

            print("PrintWorker: Job completed successfully.")

        except Exception as e:
            print("PrintWorker: Error processing print job:")
            print_exception(e)

    async def _write_to_uart(self, data_bytes):
        """Write raw bytes to the physical UART in paced chunks.

        Avoids overflowing the printer's input buffer.

        Args:
            data_bytes (bytes): Binary data payload to send.
        """
        offset = 0
        total_len = len(data_bytes)

        while offset < total_len and self.is_running:
            chunk = data_bytes[offset : offset + self.chunk_size]

            try:
                # Write to the hardware UART stream
                written = self.uart.write(chunk)

                # MicroPython uart.write returns bytes written, or None on timeout
                if written is None:
                    print("PrintWorker Warning: UART write returned None. Retrying...")
                    await uasyncio.sleep_ms(50)
                    continue

                if written == 0:
                    print("PrintWorker Warning: UART wrote 0 bytes. Retrying...")
                    await uasyncio.sleep_ms(50)
                    continue

                offset += written

                # Rate-limit the UART throughput to avoid hardware buffer saturation
                if self.delay_ms > 0:
                    await uasyncio.sleep_ms(self.delay_ms)
                else:
                    await uasyncio.sleep(0)  # Yield control to the uasyncio event loop

            except Exception as e:
                print("PrintWorker: Error writing to UART:")
                print_exception(e)
                # Wait before retrying to allow hardware connection to recover
                await uasyncio.sleep(1)
