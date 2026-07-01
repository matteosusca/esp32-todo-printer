import uasyncio

class App:
    """Manages the asynchronous queue and application tasks."""
    def __init__(self):
        # FIFO Queue for buffering PrintJobs
        self.print_queue = uasyncio.Queue()

    async def add_job(self, job):
        """Enqueue a PrintJob."""
        await self.print_queue.put(job)

    async def get_job(self):
        """Dequeue a PrintJob, blocking until one is available."""
        return await self.print_queue.get()
