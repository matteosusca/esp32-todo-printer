"""Dispatcher for note categorization and routing.

Analyzes RawNote metadata and routes it to the registered Drawer renderer,
packaging the output stream into a PrintJob DTO for the queue.
"""

from core.models import PrintJob
from drawers.short_term import ShortTermDrawer
from drawers.misc import MiscDrawer

class Dispatcher:
    """Routes RawNote objects to the appropriate Drawer and outputs PrintJobs."""

    def __init__(self):
        """Initialize the Dispatcher with default drawer mappings."""
        self.default_drawer = MiscDrawer()
        self.drawers = {
            "short_term": ShortTermDrawer(),
            "misc": self.default_drawer,
        }

    def register_drawer(self, note_type, drawer_instance):
        """Register a new drawer instance for a specific note type.

        Args:
            note_type (str): Category key (e.g. 'long_term', 'calendar').
            drawer_instance (drawers.base.BaseDrawer): Instance of the drawer.
        """
        self.drawers[note_type] = drawer_instance

    def dispatch(self, note):
        """Route a RawNote to a Drawer and return a formatted PrintJob.

        Args:
            note (core.models.RawNote): The note to process.

        Returns:
            core.models.PrintJob: Formatted print job wrapping the ESC/POS byte generator.
        """
        note_type = getattr(note, "note_type", "misc")
        drawer = self.drawers.get(note_type, self.default_drawer)
        
        # Call drawer.draw(note) to get the generator stream of ESC/POS bytes
        generator_stream = drawer.draw(note)
        
        # Package the generator stream into a PrintJob
        return PrintJob(generator_stream)
