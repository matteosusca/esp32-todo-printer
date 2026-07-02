import uasyncio

# Handle MicroPython firmware build variations for Queue
try:
    from uasyncio import Queue
except (ImportError, AttributeError):
    try:
        from asyncio import Queue
    except (ImportError, AttributeError):
        class Queue:
            """Lightweight zero-dependency async FIFO Queue for MicroPython."""
            def __init__(self):
                self._queue = []
                self._ev = uasyncio.Event()

            async def put(self, val):
                self._queue.append(val)
                self._ev.set()

            async def get(self):
                while not self._queue:
                    self._ev.clear()
                    await self._ev.wait()
                return self._queue.pop(0)


class App:
    """Manages the asynchronous queue and application tasks."""
    def __init__(self):
        # FIFO Queue for buffering PrintJobs
        self.print_queue = Queue()

    async def add_job(self, job):
        """Enqueue a PrintJob."""
        await self.print_queue.put(job)

    async def get_job(self):
        """Dequeue a PrintJob, blocking until one is available."""
        return await self.print_queue.get()
