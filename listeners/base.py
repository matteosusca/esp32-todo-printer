"""Abstract base class for note listeners.

Provides a common interface for different data sources (Telegram, Notion, etc.)
to fetch incoming raw notes and push them to the pipeline callback.
"""

class BaseListener:
    """Abstract base listener interface.

    All specialized input listeners should subclass this.
    """

    def __init__(self, callback):
        """Initialize the listener with a DTO processing callback.

        Args:
            callback (callable): Async function to process newly received RawNote DTOs.
        """
        self.callback = callback
        self.is_listening = False

    async def listen(self):
        """Start listening for incoming updates. Must be overridden by subclasses.

        This method should run an asynchronous loop and call `await self.callback(raw_note)`
        whenever new data is acquired.
        """
        raise NotImplementedError("Subclasses must implement listen()")

    def stop(self):
        """Stop listening and shut down the update loop."""
        self.is_listening = False
