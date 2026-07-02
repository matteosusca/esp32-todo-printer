"""Short-Term ToDo List Drawer.

Renders RawNotes categorized as 'short_term' into a formatted ToDo checklist layout.
"""

from drawers.base import BaseDrawer
from hardware import escpos

class ShortTermDrawer(BaseDrawer):
    """Drawer specialized for rendering ToDo lists."""

    def draw(self, note):
        """Yield ESC/POS command byte chunks line-by-line for a ToDo list.

        Args:
            note (core.models.RawNote): RawNote DTO containing ToDo items.

        Yields:
            bytes: ESC/POS formatting command chunks.
        """
        # 1. Initialize printer
        yield escpos.INIT
        
        # 2. Render Header
        yield escpos.align("center")
        yield escpos.bold(True)
        yield escpos.font_size(1, 2)
        title_str = note.title if note.title else "TODO LIST"
        yield escpos.text(f"--- {title_str} ---\n")
        yield escpos.font_size(1, 1)
        yield escpos.bold(False)
        yield escpos.reset_mode()
        yield escpos.align("left")
        
        # Divider line (384 dots width = 32 chars in Font A)
        yield escpos.text("================================\n")
        
        # 3. Process items line-by-line
        if isinstance(note.content, str):
            lines = note.content.split("\n")
            for line in lines:
                item = line.strip()
                if not item:
                    continue
                
                # Format bullet points / checkboxes
                if item.startswith("[ ]") or item.startswith("[x]") or item.startswith("[X]"):
                    formatted_line = item
                elif item.startswith("- ") or item.startswith("* "):
                    formatted_line = f"[ ] {item[2:].strip()}"
                else:
                    formatted_line = f"[ ] {item}"
                
                yield escpos.text(f"{formatted_line}\n")
        
        # 4. Footer & Paper Feed
        yield escpos.text("================================\n")
        yield escpos.feed(4)
