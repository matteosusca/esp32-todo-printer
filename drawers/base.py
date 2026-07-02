"""Abstract Base Drawer interface.

Drawers format RawNote DTOs into raw ESC/POS command byte streams using Python generators.
"""

class BaseDrawer:
    """Abstract Base Class for note layout drawers/renderers."""

    def draw(self, note):
        """Format a RawNote into a generator yielding ESC/POS command bytes.

        Args:
            note (core.models.RawNote): The note to render.

        Yields:
            bytes: ESC/POS command byte chunks formatted for the printer.
        """
        raise NotImplementedError("Subclasses must implement draw()")
